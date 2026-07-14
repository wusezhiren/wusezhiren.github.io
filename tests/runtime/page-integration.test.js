const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');

function pageContext() {
  const html = fs.readFileSync('index.html', 'utf8');
  const scripts = [...html.matchAll(/<script(?: src="([^"]+)")?>([\s\S]*?)<\/script>/g)];
  const canvas = { width: 960, height: 540, getContext: () => new Proxy({}, { get: (_target, name) => name.startsWith('create') ? () => ({ addColorStop() {} }) : () => {} }), addEventListener() {} };
  const context = { console, Math, Date, URLSearchParams, performance: { now: () => 0 }, setTimeout, clearTimeout, localStorage: { getItem: () => null, setItem() {} }, location: { search: '' }, document: { getElementById: () => canvas, querySelector: () => null }, Image: function () {}, AudioContext: function () {}, requestAnimationFrame() {}, addEventListener() {} };
  context.window = context;
  vm.createContext(context);
  for (const [, src, inline] of scripts) vm.runInContext(src ? fs.readFileSync(src, 'utf8') : inline, context);
  return context;
}

test('dedicated skills keep phase events but spawn one FX layer per cast', () => {
  const page = pageContext();
  const stats = vm.runInContext(`(() => {
    const p = new Player('blade');
    const phases = [];
    p.bladeAction = p.bladeAction || null;
    const original = p.handleBladeEvent;
    p.handleBladeEvent = event => { if (event.type === 'phase') phases.push(event.name); original.call(p, event); };
    p.cast(p.skills.find(s => s.fx === 'tripleslash'));
    for (let i = 0; i < 60; i++) p.update();
    return { fx: window.__dof70SkillFXSpawnCount, phases };
  })()`, page);
  assert.equal(stats.fx, 1);
  assert.equal(stats.phases.length, 3);
});

test('real page cast/update chain resolves weapon-specific hits for all five weapons', () => {
  const weapons = ['lightsword', 'katana', 'greatsword', 'club', 'shortsword'];
  for (const weapon of weapons) {
    const page = pageContext();
    const result = vm.runInContext(`(() => {
      enemies.length = 0;
      const p = new Player('blade');
      p.equipItem(DOF70.equipment.normalizeWeapon({ type: 'weapon', weaponType: '${weapon}', stats: {} }, 'blade'));
      p.x = 160; p.y = 430;
      const enemy = new Enemy(220, 430, 'gob');
      enemies.push(enemy);
      const skill = p.skills.find(s => s.fx === 'tripleslash');
      let resolved = 0;
      const resolveHit = p.resolveHit;
      p.resolveHit = hit => { resolved++; return resolveHit.call(p, hit); };
      p.cast(skill);
      const originalDamage = skill.dmg;
      skill.dmg = [-999, -999];
      for (let i = 0; i < 30; i++) p.update();
      const triple = { resolved, damage: enemy.maxhp - enemy.hp };
      enemies.length = 0;
      const enemy2 = new Enemy(220, 430, 'gob');
      enemies.push(enemy2);
      skill.dmg = originalDamage;
      p.x = 160; p.y = 430; p.attackTimer = 0; p.cast(p.skills.find(s => s.fx === 'hiddenblade'));
      const hidden = p.attackType;
      hidden.dmg = [-999, -999];
      for (let i = 0; i < 60; i++) p.update();
      return { triple, hidden: { damage: enemy2.maxhp - enemy2.hp }, fx: window.__dof70SkillFXSpawnCount };
    })()`, page);
    assert.ok(result.triple.resolved > 0, `${weapon}: triple slash did not resolve a hit`);
    assert.ok(result.triple.damage > 0, `${weapon}: triple slash did not damage enemy`);
    assert.ok(result.hidden.damage > 0, `${weapon}: hidden blade did not damage enemy`);
    assert.equal(result.fx, 2, `${weapon}: dedicated FX spawn count`);
  }
});
