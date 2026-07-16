import { cleanChannel, parseClientMessage } from "./protocol.mjs";
import { hashPassword, newToken, tokenHash, validateCredentials, validateSave, verifyPassword } from "./auth.mjs";

const json = data => JSON.stringify(data);
const SESSION_MS = 30 * 24 * 60 * 60 * 1000;
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS'
};
const response = (data, status = 200) => Response.json(data, { status, headers: corsHeaders });

async function body(request) {
  try { return await request.json(); } catch { return null; }
}

async function createSession(env, userId) {
  await env.DB.prepare('DELETE FROM sessions WHERE expires_at<=?').bind(Date.now()).run();
  const token = newToken();
  await env.DB.prepare('INSERT INTO sessions (token_hash,user_id,expires_at) VALUES (?,?,?)')
    .bind(await tokenHash(token), userId, Date.now() + SESSION_MS).run();
  return token;
}

async function authenticatedUser(request, env) {
  const header = request.headers.get('Authorization') || '';
  if (!header.startsWith('Bearer ')) return null;
  const hash = await tokenHash(header.slice(7));
  return env.DB.prepare(`SELECT users.id,users.username,users.save_json FROM sessions
    JOIN users ON users.id=sessions.user_id WHERE sessions.token_hash=? AND sessions.expires_at>?`)
    .bind(hash, Date.now()).first();
}

async function authRoute(request, env, pathname) {
  if (pathname === '/auth/register' && request.method === 'POST') {
    const input = await body(request); const valid = validateCredentials(input?.username, input?.password);
    if (valid.error) return response({ error: valid.error }, 400);
    const exists = await env.DB.prepare('SELECT id FROM users WHERE username=?').bind(valid.username).first();
    if (exists) return response({ error: '用户名已存在' }, 409);
    const password = await hashPassword(input.password), now = Date.now();
    let result;
    try {
      result = await env.DB.prepare('INSERT INTO users (username,password_hash,password_salt,created_at,updated_at) VALUES (?,?,?,?,?)')
        .bind(valid.username, password.hash, password.salt, now, now).run();
    } catch (error) {
      if (String(error).includes('UNIQUE')) return response({ error: '用户名已存在' }, 409);
      throw error;
    }
    return response({ token: await createSession(env, result.meta.last_row_id), username: valid.username }, 201);
  }
  if (pathname === '/auth/login' && request.method === 'POST') {
    const input = await body(request); const valid = validateCredentials(input?.username, input?.password);
    if (valid.error) return response({ error: '用户名或密码错误' }, 401);
    const user = await env.DB.prepare('SELECT * FROM users WHERE username=?').bind(valid.username).first();
    if (!user || !await verifyPassword(input.password, user.password_salt, user.password_hash)) return response({ error: '用户名或密码错误' }, 401);
    return response({ token: await createSession(env, user.id), username: user.username, save: user.save_json ? JSON.parse(user.save_json) : null });
  }
  if (pathname === '/auth/logout' && request.method === 'POST') {
    const header = request.headers.get('Authorization') || '';
    if (header.startsWith('Bearer ')) await env.DB.prepare('DELETE FROM sessions WHERE token_hash=?').bind(await tokenHash(header.slice(7))).run();
    return response({ ok: true });
  }
  const user = await authenticatedUser(request, env);
  if (!user) return response({ error: '登录已失效' }, 401);
  if (pathname === '/auth/me' && request.method === 'GET') return response({ username: user.username, save: user.save_json ? JSON.parse(user.save_json) : null });
  if (pathname === '/save' && request.method === 'PUT') {
    const input = await body(request), valid = validateSave(input?.save);
    if (valid.error) return response({ error: valid.error }, 400);
    await env.DB.prepare('UPDATE users SET save_json=?,updated_at=? WHERE id=?').bind(valid.serialized, Date.now(), user.id).run();
    return response({ ok: true, updatedAt: Date.now() });
  }
  return response({ error: 'Not found' }, 404);
}

export class TownChannel {
  constructor(ctx) {
    this.ctx = ctx;
    this.players = new Map();
    for (const socket of ctx.getWebSockets()) {
      const attachment = socket.deserializeAttachment();
      if (attachment?.id && attachment.player) this.players.set(attachment.id, attachment.player);
    }
  }

  fetch(request) {
    if (request.headers.get("Upgrade") !== "websocket") return new Response("WebSocket required", { status: 426 });
    const pair = new WebSocketPair();
    const client = pair[0];
    const server = pair[1];
    const id = crypto.randomUUID();
    server.serializeAttachment({ id });
    this.ctx.acceptWebSocket(server);
    server.send(json({ type: "welcome", id, players: [...this.players].map(([playerId, player]) => ({ id: playerId, ...player })) }));
    return new Response(null, { status: 101, webSocket: client });
  }

  webSocketMessage(socket, raw) {
    const attachment = socket.deserializeAttachment();
    const id = attachment?.id;
    if (!id) return socket.close(1008, "Missing player id");
    const message = parseClientMessage(raw, this.players.get(id));
    if (!message) return;
    const joined = this.players.has(id);
    this.players.set(id, message.player);
    socket.serializeAttachment({ id, player: message.player });
    this.broadcast({ type: joined ? "move" : "join", id, ...message.player }, socket);
  }

  webSocketClose(socket) {
    this.remove(socket);
  }

  webSocketError(socket) {
    this.remove(socket);
  }

  remove(socket) {
    const id = socket.deserializeAttachment()?.id;
    if (id && this.players.delete(id)) this.broadcast({ type: "leave", id });
  }

  broadcast(message, except) {
    const payload = json(message);
    for (const socket of this.ctx.getWebSockets()) {
      if (socket === except) continue;
      try { socket.send(payload); } catch { this.remove(socket); }
    }
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: corsHeaders });
    if (url.pathname === "/health") return response({ ok: true, service: "dnf-town-online" });
    if (url.pathname.startsWith('/auth/') || url.pathname === '/save') return authRoute(request, env, url.pathname);
    if (url.pathname !== "/town") return new Response("Not found", { status: 404 });
    const id = env.TOWN_CHANNEL.idFromName(cleanChannel(url.searchParams.get("channel")));
    return env.TOWN_CHANNEL.get(id).fetch(request);
  }
};
