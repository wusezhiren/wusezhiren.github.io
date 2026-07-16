const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');

const html = fs.readFileSync('index.html', 'utf8');
const config = fs.readFileSync('assets/multiplayer.config.js', 'utf8');

test('renders registration and login controls with persistent token support', () => {
  assert.match(html, /id="accountModal"/);
  assert.match(html, /id="accountRegister"/);
  assert.match(html, /id="accountPassword"[^>]+minlength="8"/);
  assert.match(html, /localStorage\.getItem\('dnf_auth_token'\)/);
  assert.match(html, /AUTH\.init\(\)/);
});

test('cloud save is wired to local save and page shutdown', () => {
  assert.match(html, /AUTH\.scheduleSave\(\)/);
  assert.match(html, /beforeunload[\s\S]*serializeRun\(\)[\s\S]*AUTH\.saveNow\(true\)/);
  assert.match(config, /wss:\/\/dnf-town-online\.1781718217\.workers\.dev\/town/);
});
