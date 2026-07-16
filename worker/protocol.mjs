export const CLASSES = new Set(["blade", "berserk"]);
export const MAX_NAME_LENGTH = 16;
export const WORLD_WIDTH = 1800;
export const MIN_Y = 340;
export const MAX_Y = 510;

export function cleanChannel(value) {
  const channel = String(value || "hendonmyre-1").replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 32);
  return channel || "hendonmyre-1";
}

export function cleanName(value) {
  const name = String(value || "冒险家").replace(/[\u0000-\u001f\u007f<>]/g, "").trim().slice(0, MAX_NAME_LENGTH);
  return name || "冒险家";
}

export function cleanPlayer(input = {}, fallback = {}) {
  const cls = CLASSES.has(input.cls) ? input.cls : (CLASSES.has(fallback.cls) ? fallback.cls : "blade");
  const number = (value, defaultValue) => Number.isFinite(Number(value)) ? Number(value) : defaultValue;
  return {
    name: cleanName(input.name ?? fallback.name),
    cls,
    x: Math.max(30, Math.min(WORLD_WIDTH - 30, number(input.x, fallback.x ?? 180))),
    y: Math.max(MIN_Y, Math.min(MAX_Y, number(input.y, fallback.y ?? 430))),
    dir: number(input.dir, fallback.dir ?? 1) < 0 ? -1 : 1,
    state: input.state === "walk" || input.state === "run" ? input.state : "idle"
  };
}

export function parseClientMessage(raw, fallback) {
  let message;
  try {
    message = JSON.parse(typeof raw === "string" ? raw : new TextDecoder().decode(raw));
  } catch {
    return null;
  }
  if (!message || (message.type !== "join" && message.type !== "move")) return null;
  return { type: message.type, player: cleanPlayer(message.player, fallback) };
}
