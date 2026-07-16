const encoder = new TextEncoder();
export const USERNAME_RE = /^[a-zA-Z0-9_\u4e00-\u9fff]{3,16}$/u;
export const MIN_PASSWORD_LENGTH = 8;
export const MAX_SAVE_BYTES = 128 * 1024;

export function validateCredentials(username, password) {
  const name = String(username || '').trim();
  if (!USERNAME_RE.test(name)) return { error: '用户名需为3-16位中文、字母、数字或下划线' };
  if (typeof password !== 'string' || password.length < MIN_PASSWORD_LENGTH || password.length > 72) return { error: '密码需为8-72位' };
  return { username: name };
}

export function bytesToBase64(bytes) {
  let value = '';
  for (const byte of bytes) value += String.fromCharCode(byte);
  return btoa(value);
}

export function base64ToBytes(value) {
  const raw = atob(value);
  return Uint8Array.from(raw, char => char.charCodeAt(0));
}

export async function hashPassword(password, salt = crypto.getRandomValues(new Uint8Array(16))) {
  const key = await crypto.subtle.importKey('raw', encoder.encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations: 100000 }, key, 256);
  return { salt: bytesToBase64(salt), hash: bytesToBase64(new Uint8Array(bits)) };
}

export async function verifyPassword(password, salt, expected) {
  const actual = await hashPassword(password, base64ToBytes(salt));
  if (actual.hash.length !== expected.length) return false;
  let difference = 0;
  for (let i = 0; i < expected.length; i++) difference |= actual.hash.charCodeAt(i) ^ expected.charCodeAt(i);
  return difference === 0;
}

export function newToken() {
  return bytesToBase64(crypto.getRandomValues(new Uint8Array(32))).replaceAll('+', '-').replaceAll('/', '_').replaceAll('=', '');
}

export async function tokenHash(token) {
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(token));
  return bytesToBase64(new Uint8Array(digest));
}

export function validateSave(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return { error: '存档格式无效' };
  const serialized = JSON.stringify(value);
  if (encoder.encode(serialized).length > MAX_SAVE_BYTES) return { error: '存档数据过大' };
  return { serialized };
}
