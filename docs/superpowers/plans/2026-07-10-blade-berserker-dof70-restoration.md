# 剑魂与狂战士 DOF 70 严格还原实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以本地 DOF（重生 70 版本）为权威来源，严格还原剑魂、狂战士、共通上挑及基础战斗动作，并接入五类武器、原版物理伤害结算和统一 70 级副本。

**Architecture:** 先用 Python 工具生成可追溯的技能、动作、武器、被动和怪物审计数据，再以无 DOM 依赖的 CommonJS/浏览器双用 JavaScript 模块实现伤害、状态、动作、装备和存档原语。13 个玩法技能保持专用处理器，通过薄适配层接入现有单文件 Canvas 运行时，不建设通用技能 DSL，也不重写现有商店、背包或地图框架。

**Tech Stack:** 静态 HTML5 Canvas、原生 JavaScript、Node.js 内置 `node:test`、Python 3 `unittest`、Pillow、现有 PVF/ANI/IMG 解析工具。

---

## 实施前提与工作方式

- 权威规格：`docs/superpowers/specs/2026-07-10-blade-berserker-dof70-restoration-design.md`
- 在独立 worktree 中执行本计划；不要覆盖用户未提交的规格文档或 `.superpowers/` 会话文件。
- 每项生产代码修改遵循 `@test-driven-development`：先写失败测试、确认失败、写最小实现、确认通过。
- 每个任务结束前遵循 `@verification-before-completion`，运行任务内列出的定向测试。
- 遇到未知 PVF/ANI/ATK 字段、五精通等级歧义、伤害取整或客户端硬编码行为时，停止该依赖链并登记为待实测项；不得填入近似值让测试通过。
- 计划中的提交步骤仅提交该任务列出的文件，不提交 `.superpowers/`、临时截图或无关改动。

## 文件职责

### 新增工具与生成数据

- `tools/atk.py`：解析 `.atk` 攻击信息，暴露攻击类型、控制参数和原始字段。
- `tools/dof70_skill_audit_config.py`：固定 13 个玩法技能、9 个被动/增益及其权威资源清单。
- `tools/dof70_skill_audit.py`：推导 70 级最高可达技能等级，生成严格审计数据和待实测列表。
- `tools/dof70_action_audit.py`：无损导出基础动作、技能阶段、身体/武器 ANI、box 和来源。
- `assets/dof70/swordman-restoration.json`：运行时使用的权威静态数据。
- `assets/dof70/swordman-restoration.meta.js`：把同一份审计 JSON 包装为同步浏览器全局 `DOF70_RESTORATION`。
- `assets/dof70/swordman-timelines.json`：动作与技能逐阶段时间轴。
- `assets/dof70/swordman-timelines.meta.js`：把同一份时间轴包装为同步浏览器全局 `DOF70_TIMELINES`。
- `docs/superpowers/verification/2026-07-10-blade-berserker-dof70-matrix.md`：人类可读差异矩阵。
- `docs/superpowers/verification/2026-07-10-dof70-client-measurements.md`：待实测问题、候选解释、证据和关闭状态。

### 新增运行时模块

- `src/classes/availability.js`：职业开放状态及所有入口的统一验证。
- `src/save/migrations.js`：存档 schema、旧武器迁移及禁用职业恢复结果。
- `src/equipment/weapons.js`：五类武器定义、默认武器、职业限制和物品规范化。
- `src/combat/damage.js`：百分比、固定和混合物理伤害纯函数。
- `src/combat/status.js`：无敌、霸体、硬直、浮空、倒地、起身、抓取、吸附和每目标命中原语。
- `src/combat/action-player.js`：阶段时间轴、动作推进、阶段事件、取消窗口和输入缓冲。
- `src/combat/passives.js`：武器奥义、五精通、血气唤醒、血之狂暴和暴走。
- `src/combat/skills/common/uppercut.js`：上挑专用处理器。
- `src/combat/skills/blade/*.js`：六个剑魂技能专用处理器。
- `src/combat/skills/berserk/*.js`：六个狂战技能专用处理器。
- `src/combat/skills/index.js`：仅负责按稳定技能键选择专用处理器。
- `src/monsters/dof70.js`：70 级普通、精英和 Boss 模板。

所有 `src/**/*.js` 使用同一种 IIFE 双用协议：工厂函数接收显式依赖，浏览器端挂到唯一 `globalThis.DOF70` 命名空间，Node 端通过 `module.exports` 导出。`index.html` 在现有内联运行时前按以下顺序同步加载，禁止依赖异步 `fetch` 竞态：

1. `assets/dof70/swordman-restoration.meta.js`
2. `assets/dof70/swordman-timelines.meta.js`
3. `src/classes/availability.js`、`src/save/migrations.js`、`src/equipment/weapons.js`
4. `src/combat/damage.js`、`src/combat/status.js`、`src/combat/action-player.js`、`src/combat/passives.js`
5. 13 个专用技能处理器和 `src/combat/skills/index.js`
6. `src/monsters/dof70.js`

每个模块初始化时校验所需依赖和数据 schema；缺失时抛出包含模块名的错误，不能以空配置继续。Node 测试直接注入 JSON fixture，不执行浏览器全局分支。

### 修改现有文件

- `tools/skl.py`：补充学习间隔、职业上限、前置技能和 level property 结构化解析。
- `tools/ani70.py`：严格模式下保留原始延迟、空帧和 box，并报告未知字段。
- `tools/build_player_atlas.py`：从 DOF 70 生成五类武器图集。
- `tools/build_skill_actions.py`：移除有损延迟裁剪，补充武器动作与来源。
- `tools/build_skillfx.py`、`tools/skillfx_config.py`：目标技能严格来源模式，禁止旧客户端静默回退。
- `index.html`：加载新模块和数据，以薄适配层替换通用技能近似，接入职业禁用、存档迁移、武器、伤害、状态和 70 级怪物。

---

### Task 1: 建立 Node 运行时测试基线与职业统一门禁

**Files:**
- Create: `src/classes/availability.js`
- Create: `tests/runtime/class-availability.test.js`
- Create: `tools/extract_inline_js.py`
- Create: `tests/test_extract_inline_js.py`
- Modify: `index.html:29-33,202-249,2495-2511,2547-2553,2571-2588,2699-2706,2935-2956`

- [ ] **Step 1: 写职业开放状态的失败测试**

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const { classAvailability, canStartClass } = require('../../src/classes/availability.js');

test('only blade and berserk are playable', () => {
  assert.equal(canStartClass('blade'), true);
  assert.equal(canStartClass('berserk'), true);
  assert.equal(canStartClass('spectre'), false);
  assert.equal(canStartClass('asura'), false);
  assert.equal(canStartClass('unknown'), false);
  assert.equal(classAvailability('spectre').label, '暂未开放');
});
```

- [ ] **Step 2: 运行测试并确认因模块缺失而失败**

Run: `node --test tests/runtime/class-availability.test.js`

Expected: FAIL，提示无法找到 `src/classes/availability.js`。

- [ ] **Step 3: 实现无 DOM 依赖的职业门禁模块**

模块遵循本计划统一 IIFE 协议，同时导出到 `globalThis.DOF70.classes` 和 `module.exports`，固定 `blade/berserk` 为 `available`，`spectre/asura` 为 `coming-soon`，未知键为 `invalid`。在 `index.html` 现有元数据脚本之后、内联运行时之前加载该文件。

- [ ] **Step 4: 在所有入口接入同一个 `canStartClass()`**

在 `index.html` 中：

- 保留四张职业卡和 `CLASS_KEYS` 排列。
- `drawSelect()` 为禁用卡降低透明度并绘制“暂未开放”。
- 数字键、Enter、`startGame()`、`continueGame()`、`?shot=` 和 `?state=mapsel` 均调用同一个门禁。
- 禁用职业存档返回职业选择并显示提示，不构造 `Player`。

- [ ] **Step 5: 扩充源码入口回归测试并运行**

测试读取 `index.html`，断言所有入口调用 `canStartClass`，并断言卡片文案存在。

Run: `node --test tests/runtime/class-availability.test.js && python3 -m unittest discover -s tests -v`

Expected: 新测试 PASS；旧测试中若仅因“全部四职业可玩”假设失败，更新该旧合同后重新运行，不能删除无关断言。

- [ ] **Step 6: 增加可复现的内联脚本提取工具**

`tools/extract_inline_js.py <html> <output>` 使用现有验证流程的正则语义提取所有无 `src` 的内联脚本，以 UTF-8 写入目标文件。测试覆盖多个内联脚本、外部脚本排除和空脚本。

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_extract_inline_js -v && python3 tools/extract_inline_js.py index.html /tmp/index-inline.js && node --check /tmp/index-inline.js`

Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add src/classes/availability.js tests/runtime/class-availability.test.js tools/extract_inline_js.py tests/test_extract_inline_js.py index.html
git commit -m "feat: disable unfinished swordman classes"
```

---

### Task 2: 扩展 SKL 与 ATK 严格解析能力

**Files:**
- Create: `tools/atk.py`
- Create: `tests/test_atk_reader.py`
- Create: `tests/test_skl_reader.py`
- Modify: `tools/skl.py:34-165`
- Modify: `tools/ani70.py:19-146`
- Create: `tests/test_ani70_parser.py`

- [ ] **Step 1: 为真实目标 fixture 写失败测试**

测试从本地 `Script.pvf` 读取：

- `skill/swordman/tripleslash.skl` 的初学等级、学习间隔、最大等级和前置技能。
- `skill/swordman/reckless.skl` 的 level property 原始列。
- `character/swordman/attackinfo/chargecrashdash.atk` 与 `chargecrashupper.atk` 的差异。
- 一个身体 ANI 的空帧、原始 delay 和 box。

断言缺失路径通过 `read_required()` 抛出包含技能键、字段和 PVF 路径的异常。

- [ ] **Step 2: 运行测试并确认字段缺失**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skl_reader tests.test_atk_reader tests.test_ani70_parser -v`

Expected: FAIL，明确缺少新字段或 `tools.atk`。

- [ ] **Step 3: 最小扩展解析器**

在 `SkillReader.read_skill()` 中增加结构化字段但保留旧字段：

```python
{
    "required_level_range": int | None,
    "growtype_maximum_level": list[int],
    "pre_required_skills": list[dict],
    "skill_type": list,
    "skill_class": list,
    "level_property": list,
}
```

`tools/atk.py` 复用 `parse_tokens()`，返回原始 section 和已确认语义字段；未知字段保留在 `raw_sections`，不猜测含义。

- [ ] **Step 4: 给 ANI 增加 strict 选项**

`parse_ani70(data, strict=True)` 必须：

- 保留原始 delay 和空帧。
- 保留 box keyword 与六个原始整数。
- 未知属性宽度无法唯一确定时抛错。
- 非 strict 模式保持旧生成器兼容。

- [ ] **Step 5: 运行解析器测试和现有工具测试**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_skl_reader tests.test_atk_reader tests.test_ani70_parser tests.test_skill_actions tests.test_skillfx_config -v`

Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add tools/skl.py tools/atk.py tools/ani70.py tests/test_skl_reader.py tests/test_atk_reader.py tests/test_ani70_parser.py
git commit -m "feat: parse DOF skill and attack metadata"
```

---

### Task 3: 生成 13 技能、9 被动和待实测审计矩阵

**Files:**
- Create: `tools/dof70_skill_audit_config.py`
- Create: `tools/dof70_skill_audit.py`
- Create: `tests/test_dof70_skill_audit.py`
- Create: `tests/test_dof70_skill_levels.py`
- Create: `tests/test_dof70_passives.py`
- Create: `tests/test_dof70_source_failures.py`
- Create: `assets/dof70/swordman-restoration.json`
- Create: `assets/dof70/swordman-restoration.meta.js`
- Create: `docs/superpowers/verification/2026-07-10-blade-berserker-dof70-matrix.md`
- Create: `docs/superpowers/verification/2026-07-10-dof70-client-measurements.md`

- [ ] **Step 1: 写目标集合和最高等级失败测试**

锁定玩法技能集合恰好为：

```python
{
  "uppercut", "tripleSlash", "momentarySlash", "chargeCrash",
  "rapidMoveSlash", "illusionSlash", "weaponCombo", "goreCross",
  "hopSmash", "grabBlastBlood", "bloodBlast", "bloodyRave",
  "outrageBreak"
}
```

被动/增益集合恰好为武器奥义、五精通、血气唤醒、血之狂暴、暴走。测试最高等级推导包含技能初学等级、学习间隔、全局上限、growtype 上限、前置和武器奥义影响，不只比较最终数字。

- [ ] **Step 2: 写严格来源和待实测失败测试**

断言：

- 每项来源只来自 DOF 70 客户端。
- 每个必需字段要么为已验证值，要么有 `unverified` 条目。
- `unverified` 包含至少两个候选解释、影响范围、验证步骤和状态。
- 不允许 `estimate`、旧网页锚或虚构里鬼 MP/CD。
- 生成到临时目录时缺任一必需 SKL/ANI/ATK 会失败。

- [ ] **Step 3: 运行测试并确认审计器不存在**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dof70_skill_audit tests.test_dof70_skill_levels tests.test_dof70_passives tests.test_dof70_source_failures -v`

Expected: FAIL。

- [ ] **Step 4: 实现审计配置和生成器**

配置使用稳定英文键，避免当前 `frenzy` 同时指“怒气爆发特效”和“血之狂暴 SKL”的冲突。生成器接受 `--output-dir`，默认输出仓库资产；测试使用临时目录。每次从同一 Python 对象同时生成格式化 JSON 和 `globalThis.DOF70_RESTORATION=<compact-json>;`，测试断言二者深度相等，避免浏览器包装数据漂移。

- [ ] **Step 5: 生成 JSON 和 Markdown 矩阵**

Run: `python3 tools/dof70_skill_audit.py`

Expected: 输出 13 个玩法技能、9 个被动/增益、五种武器分支和待实测条目；任何未证明字段不会进入 `verified`。

- [ ] **Step 6: 执行待实测前置检查**

逐项检查 `docs/superpowers/verification/2026-07-10-dof70-client-measurements.md`：

- 若存在阻塞运行时结构的开放项，例如五精通最终等级、五类武器映射、伤害取整/防御公式，先按规格完成客户端实测并添加区分候选公式的测试。
- 若本地客户端无法验证，停止后续依赖任务并向用户报告阻塞，不使用近似值继续。

- [ ] **Step 7: 运行全量审计测试**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dof70_skill_audit tests.test_dof70_skill_levels tests.test_dof70_passives tests.test_dof70_source_failures -v`

Expected: PASS，且阻塞字段不存在开放状态。

- [ ] **Step 8: 提交**

```bash
git add tools/dof70_skill_audit_config.py tools/dof70_skill_audit.py tests/test_dof70_skill_audit.py tests/test_dof70_skill_levels.py tests/test_dof70_passives.py tests/test_dof70_source_failures.py assets/dof70/swordman-restoration.json assets/dof70/swordman-restoration.meta.js docs/superpowers/verification/2026-07-10-blade-berserker-dof70-matrix.md docs/superpowers/verification/2026-07-10-dof70-client-measurements.md
git commit -m "feat: audit DOF 70 swordman combat data"
```

---

### Task 4: 无损生成基础动作与技能阶段时间轴

**Files:**
- Create: `tools/dof70_action_audit.py`
- Create: `tests/test_dof70_action_audit.py`
- Create: `tests/test_dof70_base_actions.py`
- Create: `tests/test_dof70_weapon_branches.py`
- Create: `assets/dof70/swordman-timelines.json`
- Create: `assets/dof70/swordman-timelines.meta.js`
- Modify: `tools/build_skill_actions.py:19-101`
- Modify: `tests/test_skill_actions.py:9-51`

- [ ] **Step 1: 写无损时间轴失败测试**

断言：

- 不过滤空帧。
- 不把 delay 裁剪到 10..500ms。
- 每帧保留身体 ANI、武器 ANI、原始坐标、box 和来源路径。
- 基础动作覆盖站、走、跑、起跳、空中、落地、正背面受击、浮空、倒地、起身。
- 基础普攻按光剑、太刀、巨剑、钝器、短剑分别记录身体 ANI、武器 ANI、段数、原始帧和来源；不能用里·鬼剑术时间轴代替普通攻击。
- 五类里鬼动作分别覆盖原始资源中的完整段数。
- 每个基础动作和技能阶段保留影子层锚点；左右翻转测试断言身体、武器、影子和特效相对脚底的镜像偏移一致。
- 三段斩不会人为删除源 ANI 最后一帧。

- [ ] **Step 2: 运行测试并确认旧生成器有损**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dof70_action_audit tests.test_dof70_base_actions tests.test_dof70_weapon_branches tests.test_skill_actions -v`

Expected: FAIL，至少指出 delay 裁剪、空帧过滤和五武器分支缺失。

- [ ] **Step 3: 实现无损审计器并保持旧消费格式兼容**

`dof70_action_audit.py` 输出新时间轴；`build_skill_actions.py` 仅从该数据生成旧 renderer 所需 clip，不再修改原始时间。旧 `assets/skill_actions.*` 可继续存在，但不作为行为权威来源。审计器同时从同一对象生成 `swordman-timelines.json` 和 `globalThis.DOF70_TIMELINES=<compact-json>;`，测试断言二者深度相等。

- [ ] **Step 4: 生成时间轴并运行测试**

Run: `python3 tools/dof70_action_audit.py && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dof70_action_audit tests.test_dof70_base_actions tests.test_dof70_weapon_branches tests.test_skill_actions -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add tools/dof70_action_audit.py tools/build_skill_actions.py tests/test_dof70_action_audit.py tests/test_dof70_base_actions.py tests/test_dof70_weapon_branches.py tests/test_skill_actions.py assets/dof70/swordman-timelines.json assets/dof70/swordman-timelines.meta.js
git commit -m "feat: preserve DOF swordman action timelines"
```

---

### Task 5: 构建五类 DOF 70 武器图集

**Files:**
- Modify: `tools/build_player_atlas.py:7-64`
- Create: `tests/test_weapon_atlas.py`
- Modify: `assets/weapons.meta.js`
- Create: `assets/weapon_katana.png`
- Create: `assets/weapon_katana.json`
- Create: `assets/weapon_greatsword.png`
- Create: `assets/weapon_greatsword.json`
- Create: `assets/weapon_club.png`
- Create: `assets/weapon_club.json`
- Create: `assets/weapon_shortsword.png`
- Create: `assets/weapon_shortsword.json`
- Modify or regenerate: `assets/weapon_beamswd.png`
- Modify or regenerate: `assets/weapon_beamswd.json`

- [ ] **Step 1: 写五类来源和非透明关键帧测试**

测试从 Task 3 已验证的映射读取五类 NPK，不通过当前 `lswd` 注释猜测太刀。每类断言：DOF 70 来源、有效帧、关键动作帧非全透明、链接不越界、与身体时间轴所需帧可对应。

- [ ] **Step 2: 运行测试并确认当前只有两类武器**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_weapon_atlas -v`

Expected: FAIL。

- [ ] **Step 3: 重构生成器为显式 `main()` 和可测试函数**

生成器必须：

- 使用 DOF 70 `ImagePacks2`。
- 接受 `--output-dir`。
- 对未知 IMG 格式、解压失败、空图集和链接越界抛错。
- 生成稳定键：`lightsword/katana/greatsword/club/shortsword`；如保留 `beamswd` 旧键，仅作为明确迁移别名。

- [ ] **Step 4: 生成资产并运行测试**

Run: `python3 tools/build_player_atlas.py && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_weapon_atlas -v`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add tools/build_player_atlas.py tests/test_weapon_atlas.py assets/weapons.meta.js assets/weapon_*.png assets/weapon_*.json
git commit -m "feat: add five DOF swordman weapon atlases"
```

---

### Task 6: 实现五类武器规则与存档迁移

**Files:**
- Create: `src/equipment/weapons.js`
- Create: `src/save/migrations.js`
- Create: `tests/runtime/weapons.test.js`
- Create: `tests/runtime/save-migrations.test.js`
- Modify: `index.html:108-115,300-358,583-627,1039-1068,1198-1220,2164-2224,2313-2441,2560-2588,2655-2682`

- [ ] **Step 1: 写武器规则失败测试**

覆盖：

- 五种稳定类型和 70 级基础属性。
- 光剑仅剑魂可装备。
- 剑魂默认光剑，狂战默认权威审计确认的合法武器。
- `normalizeWeapon()` 保留旧物品 ID、稀有度、未知扩展字段。
- 当前装备类型驱动武器图集键，而不是职业硬编码。

- [ ] **Step 2: 写存档迁移失败测试**

fixture 覆盖已装备旧通用剑、背包多把旧剑、未知类型、禁用职业、非法职业、缺槽位及非数组字段。断言 schema 递增、迁移幂等、其他字段不丢失、禁用职业返回选择界面结果。

- [ ] **Step 3: 运行测试并确认模块缺失**

Run: `node --test tests/runtime/weapons.test.js tests/runtime/save-migrations.test.js`

Expected: FAIL。

- [ ] **Step 4: 实现纯规则模块**

`weapons.js` 浏览器端从同步加载的 `globalThis.DOF70_RESTORATION` 读取定义；Node 测试通过工厂参数注入 JSON fixture。`migrations.js` 返回 `{save, changed, notices, blockedClass}`，不直接操作 localStorage 或 UI。该任务同时在 `index.html` 现有内联脚本前加入 Task 3/4 数据包装脚本和当前已有模块的 `<script>` 标签，测试加载顺序与“缺数据立即抛错”。后续任务每新增一个运行时模块，都在同一加载区按“文件职责”规定的顺序追加标签。

- [ ] **Step 5: 接入现有装备流通链路**

最小修改：

- 保留单一 `weapon` 槽和普通防具逻辑。
- 只替换 `genEquip()` 武器分支，所有武器固定等级 70。
- 商店和掉落继续调用原有链路，但武器生成不再依赖 `difficulty()`。
- 价格公式显式处理绝对物攻，不把其当无量纲百分比求和。
- `equipItem()` 集中校验职业限制并返回可显示原因。
- 背包、商店和角色面板显示类型、等级、物攻、攻速和限制。
- 武器绘制读取 `player.equipped.weapon.weaponType`。
- `Save.load()` 后立即迁移并保存变化；`continueGame()` 在构造玩家前处理禁用职业。

- [ ] **Step 6: 运行 Node、Python 和语法检查**

Run: `node --test tests/runtime/weapons.test.js tests/runtime/save-migrations.test.js && python3 -m unittest discover -s tests -v`

重新提取最新内联脚本后运行：`python3 tools/extract_inline_js.py index.html /tmp/index-inline.js && node --check /tmp/index-inline.js`

Expected: 全部 PASS。

- [ ] **Step 7: 提交**

```bash
git add src/equipment/weapons.js src/save/migrations.js tests/runtime/weapons.test.js tests/runtime/save-migrations.test.js index.html
git commit -m "feat: add typed weapons and save migration"
```

---

### Task 7: 实现原版物理伤害纯函数与 70 级怪物模板

**Files:**
- Create: `src/combat/damage.js`
- Create: `src/monsters/dof70.js`
- Create: `tests/runtime/damage.test.js`
- Create: `tests/runtime/monsters-dof70.test.js`
- Modify: `index.html:39,361-388,397-415,464-478,583-618,648-657,733-749,783-813,818-852,853-872,2589-2622,2655-2682`
- Modify: `tests/test_default_test_mode.py`
- Modify or retire superseded assertions: `tests/test_skill_stats.py`

- [ ] **Step 1: 写百分比、固定、混合与防御失败测试**

使用 Task 3 已关闭待实测项的公式和区分候选取整方式的数据点，测试返回 breakdown：

```javascript
{
  percentBase,
  fixedBase,
  strengthFactor,
  masteryFactor,
  defenseFactor,
  critical,
  final
}
```

覆盖普通、暴击、五精通、暴走/血气修正层及逐段取整。测试不得仅断言近似范围。

- [ ] **Step 2: 写统一 70 级怪物失败测试**

断言四张地图生成的普通、精英、Boss 都为 70 级，并具有 HP、物防、硬直、浮空抗性和抓取抗性；房间号和旧 `recommendedLv` 不改变等级。

- [ ] **Step 3: 运行测试并确认旧倍率模型失败**

Run: `node --test tests/runtime/damage.test.js tests/runtime/monsters-dof70.test.js`

Expected: FAIL。

- [ ] **Step 4: 实现纯函数和怪物模板**

模块不得访问 Canvas、DOM、全局 `player` 或 `enemies`。随机暴击由调用方传入已确定布尔值，便于复现。

- [ ] **Step 5: 接入所有现有伤害入口**

普攻、`Projectile`、`SkillField` 和技能命中统一调用 `DOFDamage.resolvePhysicalHit()`；`Enemy.takeDamage()` 只执行资格判断、实际扣血和状态反馈。删除 `dmgMul()` 对目标技能结算的控制权，移除空中固定 1.12 倍等未获权威确认的网页规则。

- [ ] **Step 6: 固定角色与副本为 70 级**

- `DEFAULT_PLAYER_LEVEL=70`。
- `gainExp()` 不再改变战斗等级或技能等级；如保留经验展示，不参与结算。
- `difficulty()` 不再决定怪物等级和装备等级。
- 地图保留主题、房数和怪物池；差异只使用审计数据中的明确同级模板倍率。

- [ ] **Step 7: 替换冲突的旧测试合同并运行全套测试**

`test_skill_stats.py` 不再断言旧 `skill_stats.json` 的网页换算伤害；保留“旧文件不再被运行时引用”的迁移断言，权威数值由新审计和 Node 测试承担。

Run: `node --test tests/runtime/damage.test.js tests/runtime/monsters-dof70.test.js && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`

Expected: PASS。

- [ ] **Step 8: 提交**

```bash
git add src/combat/damage.js src/monsters/dof70.js tests/runtime/damage.test.js tests/runtime/monsters-dof70.test.js tests/test_default_test_mode.py tests/test_skill_stats.py index.html
git commit -m "feat: add DOF physical damage and level 70 monsters"
```

---

### Task 8: 实现共享状态与动作播放器

**Files:**
- Create: `src/combat/status.js`
- Create: `src/combat/action-player.js`
- Create: `tests/runtime/status.test.js`
- Create: `tests/runtime/action-player.test.js`
- Create: `tests/runtime/basic-actions.test.js`
- Modify: `index.html:361-388,659-758,853-908,1019-1037,1128-1197,1198-1221`

- [ ] **Step 1: 写状态原语失败测试**

依次覆盖：无敌、受击免疫、霸体、硬直、浮空、落地转倒地、倒地停留、起身、起身保护、抓取成功、不可抓取失败、目标绑定、持续吸附、每目标单次命中、重复命中间隔和命中停顿。

- [ ] **Step 2: 写动作播放器失败测试**

使用可控虚拟时钟，断言：

- 阶段使用原始毫秒时间，不统一压缩整段动作。
- 只有标记 `speedScalable` 的阶段受攻速影响。
- 身体与武器帧来自同一阶段进度。
- 阶段事件只触发一次。
- 转向、取消和输入缓冲只在声明窗口生效。
- 命中停顿期间动作、位移、状态持续时间、命中间隔和绑定特效使用同一冻结时钟；渲染循环可继续重绘当前帧，但不能推进阶段或重复发出事件。

- [ ] **Step 3: 写基础动作失败测试**

覆盖站、走、跑、跳起、空中、落地、正背面受击、浮空、倒地和起身；按五种武器参数化普攻动作；左右朝向下断言身体、武器、影子和特效相对脚底偏移保持镜像一致。

- [ ] **Step 4: 运行测试并确认模块缺失**

Run: `node --test tests/runtime/status.test.js tests/runtime/action-player.test.js tests/runtime/basic-actions.test.js`

Expected: FAIL。

- [ ] **Step 5: 实现纯状态与动作模块**

动作播放器只发出事件，如 `move`、`hitbox`、`effect`、`consume`、`cooldown`、`state`，不直接遍历敌人或绘图。状态模块返回明确结果，如 `{accepted, damageAllowed, controlAllowed, reason}`。命中解析返回 `hitstopMs`，主循环把同一个冻结量传给动作、状态和技能特效时钟；禁止各模块维护互不一致的 hitstop 计数器。

- [ ] **Step 6: 接入 Fighter、Player 和 Enemy**

- 受击、倒地、起身和抓取资格统一走状态模块。
- `Player.update()` 不再只用 `attackTimer` 判断能否行动。
- `pickSwordFrame()` 优先读取动作播放器的身体/武器帧。
- 保留旧动画函数作为非目标资源的临时 fallback，但目标基础动作资源失败时明确报错。

- [ ] **Step 7: 运行定向及全量测试**

Run: `node --test tests/runtime/status.test.js tests/runtime/action-player.test.js tests/runtime/basic-actions.test.js && python3 -m unittest discover -s tests -v`

Expected: PASS。

- [ ] **Step 8: 提交**

```bash
git add src/combat/status.js src/combat/action-player.js tests/runtime/status.test.js tests/runtime/action-player.test.js tests/runtime/basic-actions.test.js index.html
git commit -m "feat: add DOF combat states and action playback"
```

---

### Task 9: 用上挑打通专用技能完整链路

**Files:**
- Create: `src/combat/skills/common/uppercut.js`
- Create: `src/combat/skills/index.js`
- Create: `tests/runtime/skills/uppercut.test.js`
- Modify: `index.html:250-298,719-731,759-813,1939-1973`

- [ ] **Step 1: 写上挑阶段失败测试**

用 Task 3/4 生成数据测试准备、上斩判定和收招；断言角色不离地、原版浮空力/硬直/霸体/取消窗口生效，MP 与冷却在权威时点发生，身体/武器/特效和 hitbox 事件同步。

从本任务开始，每个技能测试还必须在至少一个有效命中点断言权威命中停顿：冻结期间阶段、位移、状态持续时间和绑定特效不推进，恢复后事件不重复。Tasks 10-13 的每个新技能测试沿用该合同，并覆盖各技能不同命中阶段的停顿值。

- [ ] **Step 2: 运行测试并确认通用 cast 无法满足**

Run: `node --test tests/runtime/skills/uppercut.test.js`

Expected: FAIL。

- [ ] **Step 3: 实现上挑专用处理器和薄调度器**

处理器导出 `createUppercut(context, auditData, timeline)`；`skills/index.js` 只做稳定键映射，不解释 `type/hits/reach/radius`。

- [ ] **Step 4: 接入页面事件适配层**

页面负责把处理器事件映射到移动、命中解析和 `spawnSkillFX()`。上挑不再进入 `Player.cast()` 的通用 `hits` 分支。

- [ ] **Step 5: 运行定向、状态和语法测试**

Run: `node --test tests/runtime/skills/uppercut.test.js tests/runtime/status.test.js tests/runtime/action-player.test.js`

Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add src/combat/skills/common/uppercut.js src/combat/skills/index.js tests/runtime/skills/uppercut.test.js index.html
git commit -m "feat: restore DOF uppercut behavior"
```

---

### Task 10: 实现三段斩、破军升龙击与拔刀斩

**Files:**
- Create: `src/combat/skills/blade/triple-slash.js`
- Create: `src/combat/skills/blade/charge-crash.js`
- Create: `src/combat/skills/blade/momentary-slash.js`
- Create: `tests/runtime/skills/blade/triple-slash.test.js`
- Create: `tests/runtime/skills/blade/charge-crash.test.js`
- Create: `tests/runtime/skills/blade/momentary-slash.test.js`
- Modify: `src/combat/skills/index.js`
- Modify: `index.html:203-214,256-298,719-813,1939-1973`

- [ ] **Step 1: 写三段斩失败测试**

测试三次独立动作、位移、方向修正窗口、每段命中历史、衔接失败条件及五武器精通分支。

- [ ] **Step 2: 实现三段斩并运行测试**

Run: `node --test tests/runtime/skills/blade/triple-slash.test.js`

Expected: PASS。

- [ ] **Step 3: 写破军升龙击失败测试**

分别断言霸体突进撞击和上斩浮空事件，命中框、位移速度、霸体和取消窗口不能合并为同质两段。

- [ ] **Step 4: 实现破军升龙击并运行测试**

Run: `node --test tests/runtime/skills/blade/charge-crash.test.js`

Expected: PASS。

- [ ] **Step 5: 写拔刀斩五武器失败测试**

参数化五种武器，测试蓄势、瞬时范围斩、判定帧、闪光事件、收招及权威追加判定。

- [ ] **Step 6: 实现拔刀斩并移除对应通用 profile 依赖**

Run: `node --test tests/runtime/skills/blade/momentary-slash.test.js`

Expected: PASS。

- [ ] **Step 7: 运行剑魂首批和基础链路测试**

Run: `node --test tests/runtime/skills/uppercut.test.js tests/runtime/skills/blade/*.test.js tests/runtime/status.test.js tests/runtime/action-player.test.js`

Expected: PASS。

- [ ] **Step 8: 提交**

```bash
git add src/combat/skills/blade/triple-slash.js src/combat/skills/blade/charge-crash.js src/combat/skills/blade/momentary-slash.js tests/runtime/skills/blade/triple-slash.test.js tests/runtime/skills/blade/charge-crash.test.js tests/runtime/skills/blade/momentary-slash.test.js src/combat/skills/index.js index.html
git commit -m "feat: restore core blade skill stages"
```

---

### Task 11: 实现猛龙断空斩、里·鬼剑术与幻影剑舞

**Files:**
- Create: `src/combat/skills/blade/rapid-move-slash.js`
- Create: `src/combat/skills/blade/weapon-combo.js`
- Create: `src/combat/skills/blade/illusion-slash.js`
- Create: `tests/runtime/skills/blade/rapid-move-slash.test.js`
- Create: `tests/runtime/skills/blade/weapon-combo.test.js`
- Create: `tests/runtime/skills/blade/illusion-slash.test.js`
- Modify: `src/combat/skills/index.js`
- Modify: `index.html:203-214,590-592,712-749,759-813`

- [ ] **Step 1: 写猛龙多次冲刺失败测试**

测试每次冲刺独立动作/位移/命中、原版转向窗口、无敌/霸体阶段和终结判定；禁止复用当前固定五次、全程无敌的 dash 通用分支。

- [ ] **Step 2: 实现猛龙并运行测试**

Run: `node --test tests/runtime/skills/blade/rapid-move-slash.test.js`

Expected: PASS。

- [ ] **Step 3: 写五武器里鬼失败测试**

参数化五类武器，断言动作段数、判定、衔接和附加效果来自对应时间轴；断言无 MP、无虚构冷却、无通用冲刺。

- [ ] **Step 4: 实现里鬼并删除旧虚构配置**

从 `CLASSES.blade.skills` 删除 `mp:30/cd:1200/type:'dash'/dash:20` 语义；快捷位仍触发专用连段。

Run: `node --test tests/runtime/skills/blade/weapon-combo.test.js`

Expected: PASS。

- [ ] **Step 5: 写幻影剑舞失败测试**

测试准备、锁向连续斩击、剑气终结、收招、武器分支和仅允许阶段受攻速缩放。

- [ ] **Step 6: 实现幻影剑舞并运行剑魂全套**

Run: `node --test tests/runtime/skills/blade/*.test.js`

Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add src/combat/skills/blade/rapid-move-slash.js src/combat/skills/blade/weapon-combo.js src/combat/skills/blade/illusion-slash.js tests/runtime/skills/blade/rapid-move-slash.test.js tests/runtime/skills/blade/weapon-combo.test.js tests/runtime/skills/blade/illusion-slash.test.js src/combat/skills/index.js index.html
git commit -m "feat: restore advanced blade weapon skills"
```

---

### Task 12: 实现十字斩、崩山击与怒气爆发

**Files:**
- Create: `src/combat/skills/berserk/gore-cross.js`
- Create: `src/combat/skills/berserk/hop-smash.js`
- Create: `src/combat/skills/berserk/blood-blast.js`
- Create: `tests/runtime/skills/berserk/gore-cross.test.js`
- Create: `tests/runtime/skills/berserk/hop-smash.test.js`
- Create: `tests/runtime/skills/berserk/blood-blast.test.js`
- Modify: `src/combat/skills/index.js`
- Modify: `index.html:215-225,256-298,759-813,1939-1973`

- [ ] **Step 1: 写十字斩失败测试**

分别测试横斩、竖斩和延迟血十字，断言三者事件和判定时点独立，血十字不会在按键时提前命中。

- [ ] **Step 2: 实现十字斩并运行测试**

Run: `node --test tests/runtime/skills/berserk/gore-cross.test.js`

Expected: PASS。

- [ ] **Step 3: 写崩山击失败测试**

测试起跳前冲、下劈、落地、冲击波、落地点、霸体和落地恢复，禁止近似成两次同质圆形攻击。

- [ ] **Step 4: 实现崩山击并运行测试**

Run: `node --test tests/runtime/skills/berserk/hop-smash.test.js`

Expected: PASS。

- [ ] **Step 5: 写怒气爆发失败测试**

测试起手控制、每次血气喷发的范围/间隔/命中限制、终段浮空及收招。

- [ ] **Step 6: 实现怒气爆发并运行首批狂战测试**

Run: `node --test tests/runtime/skills/berserk/gore-cross.test.js tests/runtime/skills/berserk/hop-smash.test.js tests/runtime/skills/berserk/blood-blast.test.js`

Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add src/combat/skills/berserk/gore-cross.js src/combat/skills/berserk/hop-smash.js src/combat/skills/berserk/blood-blast.js tests/runtime/skills/berserk/gore-cross.test.js tests/runtime/skills/berserk/hop-smash.test.js tests/runtime/skills/berserk/blood-blast.test.js src/combat/skills/index.js index.html
git commit -m "feat: restore berserker strike skills"
```

---

### Task 13: 实现嗜魂之手、嗜魂封魔斩与崩山裂地斩

**Files:**
- Create: `src/combat/skills/berserk/grab-blast-blood.js`
- Create: `src/combat/skills/berserk/bloody-rave.js`
- Create: `src/combat/skills/berserk/outrage-break.js`
- Create: `tests/runtime/skills/berserk/grab-blast-blood.test.js`
- Create: `tests/runtime/skills/berserk/bloody-rave.test.js`
- Create: `tests/runtime/skills/berserk/outrage-break.test.js`
- Modify: `src/combat/skills/index.js`
- Modify: `index.html:215-225,759-813,1939-1973`

- [ ] **Step 1: 写嗜魂之手抓取分支失败测试**

测试普通目标绑定、不可抓取目标、Boss 抗性分支、喷血爆炸、伤害/回血时点和控制解除。

- [ ] **Step 2: 实现嗜魂之手并运行测试**

Run: `node --test tests/runtime/skills/berserk/grab-blast-blood.test.js`

Expected: PASS。

- [ ] **Step 3: 写嗜魂封魔斩失败测试**

测试持续吸附、目标位置更新、可释放窗口、终斩独立结算、普通/霸体/不可抓取分支和中断清理。

- [ ] **Step 4: 实现嗜魂封魔斩并运行测试**

Run: `node --test tests/runtime/skills/berserk/bloody-rave.test.js`

Expected: PASS。

- [ ] **Step 5: 写崩山裂地斩失败测试**

测试跃进、HP 消耗时点、生命不足限制、砸击、冲击波、每次岩浆喷发、霸体/无敌和落地恢复；断言各段使用各自权威伤害项。

- [ ] **Step 6: 实现崩山裂地斩并运行狂战全套**

Run: `node --test tests/runtime/skills/berserk/*.test.js`

Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add src/combat/skills/berserk/grab-blast-blood.js src/combat/skills/berserk/bloody-rave.js src/combat/skills/berserk/outrage-break.js tests/runtime/skills/berserk/grab-blast-blood.test.js tests/runtime/skills/berserk/bloody-rave.test.js tests/runtime/skills/berserk/outrage-break.test.js src/combat/skills/index.js index.html
git commit -m "feat: restore berserker grab and eruption skills"
```

---

### Task 14: 接入 9 个被动与自动增益

**Files:**
- Create: `src/combat/passives.js`
- Create: `tests/runtime/passives.test.js`
- Create: `tests/runtime/auto-buffs.test.js`
- Modify: `index.html:583-618,659-669,759-782,2590-2622`

- [ ] **Step 1: 写九项等级和结算层失败测试**

测试武器奥义、五精通、血气唤醒、血之狂暴和暴走的固定最高可达等级、触发条件、属性层和技能联动。每个期望来自 `swordman-restoration.json`，不在测试中重新手写第二套数值。

- [ ] **Step 2: 写自动施放/续放失败测试**

测试进房自动施放、动作和消耗不会跳过、持续结束后仅在冷却/资源/状态允许时续放；受击、倒地、技能中和资源不足时延迟，不能强制覆盖当前动作。

- [ ] **Step 3: 运行测试并确认模块缺失**

Run: `node --test tests/runtime/passives.test.js tests/runtime/auto-buffs.test.js`

Expected: FAIL。

- [ ] **Step 4: 实现被动快照和自动增益控制器**

`passives.js` 返回纯属性修正和自动施放意图，不直接修改 Canvas 实体。明确使用 `bloodBlast` 表示怒气爆发，使用 `frenzyBuff` 表示血之狂暴，避免键冲突。

- [ ] **Step 5: 接入角色属性和进房流程**

武器精通和血气状态参与 `damage.js` 的已验证层；自动增益通过动作播放器施放，不直接设置永久倍率。

- [ ] **Step 6: 运行被动、伤害和技能全套测试**

Run: `node --test tests/runtime/passives.test.js tests/runtime/auto-buffs.test.js tests/runtime/damage.test.js tests/runtime/skills/**/*.test.js`

如果当前 shell 不展开 `**`，使用：`node --test tests/runtime`

Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add src/combat/passives.js tests/runtime/passives.test.js tests/runtime/auto-buffs.test.js index.html
git commit -m "feat: restore swordman passives and auto buffs"
```

---

### Task 15: 收紧目标动作与特效资源失败策略

**Files:**
- Modify: `tools/skillfx_config.py:8-115`
- Modify: `tools/build_skillfx.py:102-230`
- Modify: `tools/verify_skillfx.py`
- Modify: `tests/test_skillfx_config.py`
- Modify: `tests/test_skillfx_verify.py`
- Create: `tests/test_dof70_skillfx_sources.py`
- Modify: `assets/skillfx.json`
- Modify: `assets/skillfx.meta.js`
- Modify: `assets/skillfx.png`
- Modify: `index.html:1019-1125,1939-2057`

- [ ] **Step 1: 写严格来源失败测试**

对 13 个玩法技能断言：

- 来源是 DOF 70 精确 ANI/IMG/NPK 路径。
- 最终 JSON 保留来源字段。
- 缺层、解析失败、未知 IMG 格式、同 basename 多候选未裁决时构建失败。
- 禁止回退到 `地下城与勇士/ImagePacks2`。
- 空帧、循环、原始 delay、offset、scale 和 alpha 保留。

- [ ] **Step 2: 运行测试并确认当前存在静默跳层**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dof70_skillfx_sources tests.test_skillfx_config tests.test_skillfx_verify -v`

Expected: FAIL。

- [ ] **Step 3: 将构建副作用移入显式 `main()` 并增加 strict targets**

非目标旧 clip 可继续兼容生成；13 个目标 clip 使用 strict 路径，任何缺失都失败。生成器接受临时输出目录，测试导入时不写资产。

- [ ] **Step 4: 让技能处理器按阶段创建特效**

删除 `Player.cast()` 按键时统一创建所有目标技能特效的行为。十字血十字、崩山落地冲击、嗜魂喷血和岩浆等由专用阶段事件创建并按世界坐标锚定。

- [ ] **Step 5: 重建特效并运行验证**

Run: `python3 tools/build_skillfx.py && python3 tools/verify_skillfx.py assets/skillfx.json && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_dof70_skillfx_sources tests.test_skillfx_config tests.test_skillfx_verify tests.test_skill_layer_timing -v`

Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add tools/skillfx_config.py tools/build_skillfx.py tools/verify_skillfx.py tests/test_skillfx_config.py tests/test_skillfx_verify.py tests/test_dof70_skillfx_sources.py assets/skillfx.json assets/skillfx.meta.js assets/skillfx.png index.html
git commit -m "fix: enforce DOF skill effect sources"
```

---

### Task 16: 完成全量自动验证与浏览器验收

**Files:**
- Create: `tools/verify_dof70_restoration.py`
- Create: `tools/capture_dof70_evidence.py`
- Create: `tools/dof70_browser_scenarios.json`
- Create: `tests/test_dof70_restoration_manifest.py`
- Create: `tests/test_capture_dof70_evidence.py`
- Modify: `docs/superpowers/verification/2026-07-10-blade-berserker-dof70-matrix.md`
- Modify: `docs/superpowers/verification/2026-07-10-dof70-client-measurements.md`
- Create: `docs/superpowers/verification/2026-07-10-blade-berserker-dof70-results.md`
- Modify: `PLAN.md`

- [ ] **Step 1: 写完成清单失败测试**

清单必须覆盖以下维度的笛卡尔积或显式豁免理由：

- 13 个玩法技能。
- 9 个被动/增益。
- 剑魂五武器分支。
- 基础动作。
- 普通、霸体、不可抓取、浮空、倒地和 Boss 测试桩。
- 普通、精英、Boss 目标级别。
- 每个技能至少一个命中和一个未命中场景。
- 鬼泣/阿修罗所有入口禁用。
- 旧存档迁移。
- 无开放待实测项。
- 每项自动测试和画面证据路径。

- [ ] **Step 2: 实现只读总验证器**

`verify_dof70_restoration.py` 读取审计 JSON、矩阵和证据 manifest，不重建资产；缺任一项时以非零退出并打印稳定键。命令模式明确分离：

- `--structural`：只验证审计、矩阵、场景定义和自动测试 manifest，供证据生成前使用。
- `--evidence <manifest>`：执行全部结构检查并额外要求画面与录像证据完整，是唯一允许用于最终完成声明的模式。
- 不带模式参数时退出非零并打印用法，避免误把结构验证当最终验证。

同时实现：

- `dof70_browser_scenarios.json`：每个场景有稳定 ID、职业、武器、技能/基础动作、朝向、测试桩状态、预期检查点和输出文件名。
- `capture_dof70_evidence.py`：Python 编排层仅依赖标准库，自动探测 `chromium`、`chromium-browser` 或 `google-chrome`，并探测 `ffmpeg`；任一缺失时以非零退出并打印安装要求，不能跳过。脚本启动 `python3 -m http.server` 子进程，等待端口可用，对每个关键帧场景先用 `--headless --dump-dom` 读取检查结果，再用 `--headless --screenshot=<path> --window-size=1280,720` 捕获画面；对每个完整动作场景按场景定义的 `durationMs/fps` 逐帧请求 `?dof70case=<id>&frame=<n>` 并截图，再调用 `ffmpeg -framerate <fps> -i frame-%04d.png -c:v libx264 -pix_fmt yuv420p <id>.mp4` 合成确定性完整录制；最后在 `finally` 中终止服务器。
- 页面测试入口 `?dof70case=<scenario-id>&frame=<n>`：只从场景清单允许的值构造固定玩家、武器、测试桩和虚拟时钟；从动作开始精确推进到第 `n` 帧对应时间后暂停，写入 `window.__DOF70_EVIDENCE__={ready,scenario,frame,checks,errors}`，并把同一 JSON 写到 `<pre id="dof70-evidence-result">`，供 `--dump-dom` 稳定解析。测试入口可以锁血、重置冷却和固定 RNG，但必须调用正式技能处理器，不能修改处理器逻辑。

证据默认写入 `/tmp/dof70-evidence-<timestamp>/`，包含 `manifest.json`、关键帧 PNG、逐帧 PNG 和 MP4。`manifest.json` 每项保存场景 ID、目标等级、命中/未命中、URL、浏览器/ffmpeg 版本、关键帧路径、录像路径、帧数、页面 `checks/errors`、生成时间和审计数据 schema/hash。`--output-dir` 可指定持久目录；结果文档记录实际命令与路径。

- [ ] **Step 3: 运行 Python 全量测试**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`

Expected: 全部 PASS。

- [ ] **Step 4: 运行 Node 全量测试**

Run: `node --test tests/runtime`

Expected: 全部 PASS。

- [ ] **Step 5: 运行生成资产和语法验证**

```bash
python3 tools/dof70_skill_audit.py
python3 tools/dof70_action_audit.py
python3 tools/build_player_atlas.py
python3 tools/build_skill_actions.py
python3 tools/build_skillfx.py
python3 tools/verify_skillfx.py assets/skillfx.json
python3 tools/verify_dof70_restoration.py --structural
python3 tools/extract_inline_js.py index.html /tmp/index-inline.js
```

然后运行：`node --check /tmp/index-inline.js`

Expected: 所有命令退出码 0，重新生成后 `git diff` 只包含预期稳定资产差异。

- [ ] **Step 6: 执行浏览器矩阵验收**

先运行捕获工具：

```bash
python3 tools/capture_dof70_evidence.py \
  --scenarios tools/dof70_browser_scenarios.json \
  --output-dir /tmp/dof70-evidence-final
```

Expected: 命令退出码 0，`/tmp/dof70-evidence-final/manifest.json` 中所有场景 `errors=[]` 且全部预期检查点为 true，每个完整动作场景有非空 MP4。随后人工查看生成的 PNG 和 MP4，逐项覆盖：

- 上挑和两职业各六技能，左右朝向。
- 剑魂五种武器的普攻、里鬼及所有有武器差异的技能。
- 狂战抓取成功、不可抓取、Boss、吸附释放和技能中断。
- 每个技能至少一个命中和未命中场景；普通、精英、Boss 均在矩阵中覆盖。
- 基础站/走/跑/跳/落地/普攻/受击/浮空/倒地/起身，左右朝向下身体、武器、影子和特效锚点。
- 鬼泣、阿修罗置灰；数字键、URL 和旧存档无法绕过。
- 商店、掉落、背包、装备和旧存档迁移。

每份证据写入结果文档；二进制大文件不默认提交，记录可复现命令、manifest hash 和 `/tmp` 路径，不伪造已检查状态。`verify_dof70_restoration.py --evidence /tmp/dof70-evidence-final/manifest.json` 必须检查完整场景集合、目标等级和命中维度、关键帧、录像、页面检查点、零错误和 schema/hash 一致。

- [ ] **Step 7: 逐行关闭审计矩阵**

所有差异必须为“已修复”或有明确阻塞报告。任何 `open/blocked` 待实测项存在时，不得声称严格还原完成。

- [ ] **Step 8: 请求代码审查**

调用 `@requesting-code-review`，重点检查技能阶段、伤害公式、抓取状态清理、存档迁移幂等性、职业旁路和测试缺口。修复阻塞问题并重新运行 Steps 3-7。

- [ ] **Step 9: 更新验证记录并提交**

```bash
git add tools/verify_dof70_restoration.py tools/capture_dof70_evidence.py tools/dof70_browser_scenarios.json tests/test_dof70_restoration_manifest.py tests/test_capture_dof70_evidence.py docs/superpowers/verification/2026-07-10-blade-berserker-dof70-matrix.md docs/superpowers/verification/2026-07-10-dof70-client-measurements.md docs/superpowers/verification/2026-07-10-blade-berserker-dof70-results.md PLAN.md index.html
git commit -m "test: verify DOF blade and berserker restoration"
```

---

## 最终验收命令

在项目根目录执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
node --test tests/runtime
python3 tools/verify_skillfx.py assets/skillfx.json
python3 tools/verify_dof70_restoration.py --evidence /tmp/dof70-evidence-final/manifest.json
node --check /tmp/index-inline.js
```

预期：所有命令退出码 0；审计矩阵没有未解释差异或未关闭待实测项；浏览器证据覆盖规格要求的技能、武器、状态、基础动作、职业禁用和存档迁移。
