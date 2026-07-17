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

test('all casts immediately start their configured cooldown', () => {
  const page = pageContext();
  const result = vm.runInContext(`(() => {
    const blade = new Player('blade');
    const dedicated = blade.skills.find(s => s.fx === 'tripleslash');
    blade.cast(dedicated);
    const dedicatedCooldown = dedicated._cd;
    const asura = new Player('asura');
    const regular = asura.skills.find(s => s.fx === 'normalwave');
    asura.cast(regular);
    return {
      dedicatedCooldown,
      dedicatedExpected: dedicated.cd,
      regularCooldown: regular._cd,
      regularExpected: regular.cd,
    };
  })()`, page);
  assert.equal(result.dedicatedCooldown, result.dedicatedExpected);
  assert.equal(result.regularCooldown, result.regularExpected);
});

test('screenshot skill loop does not reset gameplay resources or cooldowns', () => {
  const html = fs.readFileSync('index.html', 'utf8');
  assert.doesNotMatch(html, /player\.mp=player\.maxmp;\s*for\(const s of player\.skills\)s\._cd=0/);
});

test('strong ground hits and launched landings put normal monsters down', () => {
  const page = pageContext();
  const result = vm.runInContext(`(() => {
    const ground = new Enemy(220, 430, 'orc');
    ground.takeDamage(1, 1, 12, false);
    const groundFrame = pickMonFrame(ground, MON_DEF.orc);

    const airborne = new Enemy(220, 430, 'gob');
    player = new Player('blade');
    airborne.launched = true;
    airborne.z = 1;
    airborne.vz = -2;
    airborne.update();
    airborne.update();
    return {
      groundKnockdown: ground.knockdown,
      groundFrame,
      expectedGroundFrame: MON_DEF.orc.die.at(-1),
      landingKnockdown: airborne.knockdown,
      landingLaunched: airborne.launched,
    };
  })()`, page);
  assert.ok(result.groundKnockdown > 0);
  assert.equal(result.groundFrame, result.expectedGroundFrame);
  assert.ok(result.landingKnockdown > 0);
  assert.equal(result.landingLaunched, false);
});

test('downed and newly risen monsters remain vulnerable', () => {
  const page = pageContext();
  const result = vm.runInContext(`(() => {
    player = new Player('blade');
    const enemy = new Enemy(220, 430, 'orc');
    enemy.takeDamage(1, 1, 12, false);
    const downHp = enemy.hp;
    const downDamage = enemy.takeDamage(10, 1, 2, false);
    while (enemy.knockdown > 0) enemy.update();
    const risenHp = enemy.hp;
    const risenDamage = enemy.takeDamage(10, 1, 2, false);
    return { downHp, downDamage, risenHp, risenDamage, finalHp: enemy.hp };
  })()`, page);
  assert.equal(result.downDamage, 10);
  assert.equal(result.risenHp, result.downHp - 10);
  assert.equal(result.risenDamage, 10);
  assert.equal(result.finalHp, result.risenHp - 10);
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
      const hitboxes = [];
      const resolveHit = p.resolveHit;
      p.resolveHit = hit => { resolved++; return resolveHit.call(p, hit); };
      const emit = p.handleBladeEvent;
      p.handleBladeEvent = event => { if (event.type === 'hitbox' && event.skill === 'triple-slash') hitboxes.push({ reach: event.reach, damage: event.damage }); return emit.call(p, event); };
      p.cast(skill);
      const originalDamage = skill.dmg;
      skill.dmg = [-999, -999];
      for (let i = 0; i < 30; i++) p.update();
      const triple = { resolved, damage: enemy.maxhp - enemy.hp, hitboxes, playerX: p.x, enemyX: enemy.x };
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
    assert.equal(result.triple.hitboxes.length, 3, `${weapon}: triple slash hitbox phases ${JSON.stringify(result.triple)}`);
    assert.ok(result.triple.hitboxes.every(hit => hit.damage[0] > 0), `${weapon}: triple slash consumed mutated damage ${JSON.stringify(result.triple)}`);
    assert.ok(result.triple.damage > 0, `${weapon}: triple slash did not damage enemy ${JSON.stringify(result.triple)}`);
    assert.ok(result.hidden.damage > 0, `${weapon}: hidden blade did not damage enemy`);
    assert.equal(result.fx, 2, `${weapon}: dedicated FX spawn count`);
  }
});
