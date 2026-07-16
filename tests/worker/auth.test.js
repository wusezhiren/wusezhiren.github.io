const assert = require('node:assert/strict');
const test = require('node:test');

async function auth() {
  return import('../../worker/auth.mjs');
}

test('validates account names and password bounds', async () => {
  const { validateCredentials } = await auth();
  assert.deepEqual(validateCredentials('勇士_01', 'password123'), { username: '勇士_01' });
  assert.ok(validateCredentials('ab', 'password123').error);
  assert.ok(validateCredentials('valid_name', 'short').error);
  assert.ok(validateCredentials('<script>', 'password123').error);
});

test('hashes passwords with salt and verifies without storing plaintext', async () => {
  const { hashPassword, verifyPassword } = await auth();
  const first = await hashPassword('correct horse battery staple');
  const second = await hashPassword('correct horse battery staple');
  assert.notEqual(first.salt, second.salt);
  assert.notEqual(first.hash, second.hash);
  assert.equal(await verifyPassword('correct horse battery staple', first.salt, first.hash), true);
  assert.equal(await verifyPassword('wrong password', first.salt, first.hash), false);
});

test('accepts bounded object saves and rejects invalid or oversized data', async () => {
  const { validateSave, MAX_SAVE_BYTES } = await auth();
  assert.equal(validateSave({ run: { clsKey: 'blade' } }).error, undefined);
  assert.ok(validateSave(null).error);
  assert.ok(validateSave([]).error);
  assert.ok(validateSave({ payload: 'x'.repeat(MAX_SAVE_BYTES) }).error);
});
