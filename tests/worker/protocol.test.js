const assert = require('node:assert/strict');
const test = require('node:test');

async function protocol() {
  return import('../../worker/protocol.mjs');
}

test('normalizes channel and player identity fields', async () => {
  const { cleanChannel, cleanName, cleanPlayer } = await protocol();
  assert.equal(cleanChannel('../hendon myre!?'), 'hendonmyre');
  assert.equal(cleanChannel(''), 'hendonmyre-1');
  assert.equal(cleanName('  <勇士>\u0000  '), '勇士');
  assert.deepEqual(cleanPlayer({ name: '剑魂玩家', cls: 'blade', x: -50, y: 999, dir: -4, state: 'walk' }), {
    name: '剑魂玩家', cls: 'blade', x: 30, y: 510, dir: -1, state: 'walk'
  });
});

test('rejects unsupported messages and preserves safe fallback state', async () => {
  const { parseClientMessage } = await protocol();
  assert.equal(parseClientMessage('not json'), null);
  assert.equal(parseClientMessage(JSON.stringify({ type: 'attack' })), null);
  const result = parseClientMessage(JSON.stringify({ type: 'move', player: { x: 320, state: 'hacked', cls: 'asura' } }), {
    name: '现有玩家', cls: 'berserk', x: 100, y: 420, dir: 1, state: 'idle'
  });
  assert.equal(result.type, 'move');
  assert.deepEqual(result.player, { name: '现有玩家', cls: 'berserk', x: 320, y: 420, dir: 1, state: 'idle' });
});
