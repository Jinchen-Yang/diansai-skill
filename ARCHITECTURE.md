# ARCHITECTURE — 五层架构 + 双编排形态（已落地）

> 本文是治理文档。设计稿提出的五层重构 **P1–P5 已全部实装并自测通过**（`sh tools/selftest.sh`，11 步全绿）。
> 各层落地点见 §8；§9 的开放项决议见文末。owner：lead（与 `CLAUDE.md` 同级）。

---

## 0. 为什么要这份文档（现状诊断）

当前仓库 11 个 skill 技术上是合法 Claude Code skill（有 `name`+`description` frontmatter，已被 harness 加载）。但按"agent 系统"的标准看，五层结构强弱不均：

| 层 | 现状 | 病灶 |
|---|---|---|
| 执行层 | `tools/` 无 LLM 确定性脚本，脏活/推理分离 | ✅ 扎实，**保留不动** |
| 校验层 | 确定性门齐（pinmux/protocol/power/compile） | 🟡 门结果**不进状态**：`board.py done` 不检查门是否 PASS，跳门和过门无法区分 |
| 多 agent 层 | git + `board/*.yaml` + `board.py` 的 DAG | 🟡 纯人驱动、pull-only、跨机无通知；`elec-design` 只叫人敲命令，**没用 harness 内子代理** |
| 文件控制层 | CLAUDE.md 归属表 + 一任务一文件 | 🟡 **零强制**：无 CODEOWNERS / pre-commit / allowed-tools |
| 用户交互层 | 散文式"提请用户确认" | 🔴 无结构化签字，**跳过的门 = 通过的门** |

另有一处错配：CLAUDE.md 承诺"SKILL.md 头部标 `lane` 与 `needs`"，但实际写在**正文散文**里，编排器无法机读路由。

**本设计目标**：执行层保留；其余四层从"约定"升级为"结构 + 强制"；能力标注挪进 frontmatter；并按用户决定支持**两种编排形态共用同一套执行层与门**。

---

## 1. 设计原则（不变量）

1. **推理在 Claude Code，脏活在 `tools/`**：任何层的实现都不在 skill/工具里直接调大模型 API。（沿用 CLAUDE.md）
2. **确定性门优先**：正确性靠确定性脚本 + 人工逐网核对，不靠模型"觉得对"。
3. **门的结果是状态的一部分**：状态机不接受"未过门"的完成。
4. **能力可机读**：lane / needs / gate / allowed-tools 进 frontmatter，编排器据此路由，不靠读正文。
5. **一份执行层，两种编排**：3 机 git 协同与单人子代理编排，复用同一批 `tools/` 与门定义，绝不出现两套逻辑漂移。
6. **强制 > 自觉**：目录归属、门、签字都要有机械兜底，而非仅文档约定。

---

## 2. 五层总览

```
┌─────────────────────────────────────────────────────────────┐
│ L5 用户交互层    结构化签字 / 人工门 / 歧义上报               │
│    （AskUserQuestion + design/signoffs.yaml 状态文件）        │
├─────────────────────────────────────────────────────────────┤
│ L4 编排/多-agent 层   两形态共用同一 DAG + 同一门             │
│    A: 3机 git 协同（board.py，pull 驱动，跨机异步）           │
│    B: 单人子代理编排（Agent/Workflow，会话内 fan-out）        │
├─────────────────────────────────────────────────────────────┤
│ L3 文件控制层    目录归属强制（CODEOWNERS + pre-commit +      │
│    skill frontmatter 的 writes: 白名单）                      │
├─────────────────────────────────────────────────────────────┤
│ L2 校验层    确定性门，结果写回任务状态（gate→state 耦合）    │
│    pinmux_check / gen_protocol 自检 / power_budget / compile  │
├─────────────────────────────────────────────────────────────┤
│ L1 执行层    无 LLM 的纯 Python（tools/）+ 契约生成           │
│    （保留现状，仅补 gate 退出码与机读 report）                │
└─────────────────────────────────────────────────────────────┘
```

数据/控制流：`L5 批准` 解锁 → `L4 派活`（给某 lane 或某子代理）→ skill 调 `L1 执行` → `L2 门`产出机读 report → report 写回 L4 任务状态 → 触发下游派活，遇人工门回到 `L5`。

---

## 3. 逐层规范

### L1 执行层（保留 + 微调）
- **保留**：`tools/` 全部脚本无 LLM 依赖；脏活在此，推理在 Claude Code。
- **唯一新增约束**：每个"门"脚本必须满足
  - 退出码：PASS=0，FAIL≠0（供 pre-commit / 子代理 / board 判定）。
  - 机读产物：在 stdout 之外写一份 `--report <path>` 的 YAML（见 L2），不依赖人去读 stdout。
- 受影响脚本：`pinmux_check.py`、`gen_protocol.py`（自检）、`power_budget.py`、固件 compile 包装。

### L2 校验层（门 → 状态 耦合）
核心修复：**门的结果必须落盘成状态，`done` 必须校验门。**

- 统一 gate report 格式 `design/gates/<gate>.yaml`：
  ```yaml
  gate: pinmux         # pinmux | protocol | power | compile
  target: contracts/pinmap.yaml
  result: PASS         # PASS | FAIL
  checked_at: <由调用方注入时间戳，脚本不取系统时钟>
  by: 控制             # 哪个 lane/子代理跑的
  details: []          # FAIL 时的逐条原因
  ```
- `board.py done <id>` 改为：若该任务在 DAG 里声明了 `requires_gate: pinmux`，则**校验 `design/gates/pinmux.yaml` 存在且 result==PASS**，否则拒绝标完成。
- 效果：跳门无法标完成；"完成"在审计上等价于"门已过 + 签字已留"。

### L3 文件控制层（归属强制）
把 CLAUDE.md 的归属表从散文变三道闸：
1. **`.github/CODEOWNERS`**：`design/*` → 硬件，`firmware/*` → 控制，`vision/*` → 算法，`contracts/ env/ tools/ lib/ .claude/` → lead。PR 审查级兜底。
2. **`tools/check_ownership.py` + pre-commit**：按当前 `.elec-lane` 校验本次 staged 改动是否越界写了别人目录，越界则拒绝提交。本地兜底（无需 PR 流程也生效）。
3. **skill frontmatter `writes:` 白名单**（见 §4）：声明该 skill 允许写的目录；配合 `allowed-tools` 收敛能力面。机读、供编排器与审查用。

### L4 编排 / 多-agent 层（双形态，详见 §6）
- 单一事实源：流水线 DAG 仍只定义一次（现在在 `board.py` 的 `TASKS`），两形态都读它。
- 形态 A（3 机）= 现有 board.py，补 gate 校验与跨机留言。
- 形态 B（单人）= 新增一个**编排 skill**用 Agent/Workflow 在会话内 fan-out，读同一 DAG、调同一门。

### L5 用户交互层（结构化签字）
- 人工门不再是散文，落成 `design/signoffs.yaml`：
  ```yaml
  - gate: bom-approval       # 对应 select-parts 的人工批
    status: approved         # pending | approved | rejected
    note: ""                 # 用户备注（如"换 TB6612 为 DRV8833"）
  - gate: wiring-net-review   # interconnect 的逐网核对
    status: pending
  ```
- skill 在到达人工门时：用 **AskUserQuestion** 取得明确选择 → 写 `signoffs.yaml` → `board.py done` 校验对应 signoff==approved 才放行。
- 歧义（read-problem 的 `ambiguities`）同样走 AskUserQuestion，不替用户拍硬约束。

---

## 4. Skill frontmatter schema（能力机读化）

现状只有 `name`/`description`。目标 schema（YAML frontmatter，全部机读）：

```yaml
name: interconnect
description: ...（沿用，触发用）
lane: any                 # lead | 硬件 | 控制 | 算法 | any   —— 谁能跑
needs: []                 # [multimodal] 等能力要求；multimodal 步骤只在 lead/Claude lane 跑
reads:                    # 输入产物（供编排器判依赖/做形态B的上下文注入）
  - design/bom.csv
  - design/power.yaml
writes:                   # ★ 文件控制白名单：本 skill 只允许写这些
  - contracts/pinmap.yaml
  - design/wiring.svg
  - design/harness.md
gate: pinmux              # 本步必须过的确定性门（对应 L2 report），无则 none
signoff: wiring-net-review # 本步人工门 id（对应 L5），无则 none
allowed-tools: Read, Edit, Bash(python tools/*)   # 收敛能力面
```

- `lane`/`needs` 从正文挪到这里 → 兑现 CLAUDE.md 的承诺，编排器可路由（DeepSeek/GLM lane 自动跳过 `needs: multimodal`）。
- `writes` 是 L3 白名单的机读来源；`gate`/`signoff` 是 L2/L5 的钩子。
- 不破坏现有：`name`/`description` 不变，新增字段对老 harness 是惰性的（多余 frontmatter 被忽略）。

---

## 5. 门-状态耦合（把校验接进状态机）

```
skill 跑完执行 ──► tools/<gate>.py --report design/gates/<gate>.yaml
                          │ exit 0 / ≠0
                          ▼
              design/gates/<gate>.yaml (PASS/FAIL)
                          │
   board.py done <id> ────┤ 读 DAG 的 requires_gate / requires_signoff
                          ├─ gate.result != PASS      → 拒绝
                          ├─ signoff.status != approved→ 拒绝
                          └─ 全过 → 标 done + 自动派生下游
```

要点：`done` 从"无条件标记"变成"带前置条件的状态跃迁"。这一改让 L2、L5 真正长出牙齿，且对形态 A/B 都生效（两者都走 `board.py done` 或其等价校验函数）。

---

## 6. 双编排形态（用户：两者都要，分场景）

两形态**共用**：同一份 DAG、同一批 `tools/` 门、同一 `signoffs.yaml`/`gates/` 状态。区别只在"谁来跑下一个任务、怎么交接"。

### 形态 A — 3 机 git 协同（现场 3 人）
- 引擎：`board.py`（保留），增强：`done` 加门/签字校验（§5）；`status` 显示每个任务的门状态。
- 交接：pull 驱动 + `board/messages.md` 留言（保留）；近实时靠 `/loop` 或 `watch.sh`（保留）。
- 适用：比赛现场 3 人 3 机、跨机异步。
- 诚实边界：跨机无 push 通知，这是 git 协同的固有代价，不强行假装实时。

### 形态 B — 单人子代理编排（一人备赛 / 赛前搭链路）
- 引擎：**新增编排 skill（如 `/elec-orchestrate`）**，在单会话内用 **Agent / Workflow** fan-out：
  - 读同一 DAG，找出当前可并行的任务（依赖已满足）。
  - 对每个可并行任务起一个子代理（`run_in_background` 或 Workflow `parallel`/`pipeline`），子代理调对应 skill 的执行 + 门。
  - 多模态任务（`needs: multimodal`）留在主会话（lead/Claude）跑，不下放。
  - 写文件并行时用 `isolation: worktree` 防冲突，或按 `writes` 白名单错开目录。
- 人工门：子代理遇 `signoff` 不自行拍板 → 回主会话用 AskUserQuestion 找用户。
- 适用：一个人想一口气把"读题→…→骨架"链路在本机跑通，不必模拟 3 台机器。

### 形态切换
- 不互斥：`.elec-mode = solo | team`（不入库）。`solo` 走形态 B；`team` 走形态 A。
- 两形态产出的状态（gates/signoffs/board）格式一致，可互相接力（一个人先 solo 搭好，再切 team 上人）。

---

## 7. 强制手段汇总（"强制 > 自觉"）

| 不变量 | 强制点 | 层 |
|---|---|---|
| 不越界写别人目录 | CODEOWNERS + pre-commit(`check_ownership.py`) + frontmatter `writes` | L3 |
| 不跳确定性门 | `board.py done` 校验 `gates/<gate>.yaml`==PASS | L2 |
| 不跳人工签字 | `board.py done` 校验 `signoffs.yaml`==approved | L5 |
| 多模态不下放给非 Claude lane | frontmatter `needs: multimodal` + 编排器路由 | L4 |
| 契约改后必重生成/校验 | pre-commit 钩 `gen_protocol.py`/`pinmux_check.py` | L1/L2 |

---

## 8. 落地点（已实装，每层可独立回滚）

- **P1 能力机读化 ✅**：11 个 `SKILL.md` 补 frontmatter（`lane/needs/reads/writes/gate/signoff/allowed-tools`），正文 lane/needs 散文改为指向 frontmatter 的一行。纯加字段，触发行为不变。
- **P2 门→状态 ✅**：`pinmux_check.py`/`power_budget.py`/`gen_protocol.py` 加 `--report`（写 `design/gates/<gate>.yaml`）；通用记录器 `tools/gate_report.py`（如 `compile`）；共享库 `tools/gatelib.py`；`board.py done` 校验门+签字（未过 exit 3，`--force` 留痕）；`tools/gate_check.py` 与 done 共用 `gatelib.check_spec` 判据。
- **P3 文件控制强制 ✅**：`.github/CODEOWNERS`（PR 级）+ `tools/check_ownership.py`（按 `.elec-lane` 拦越界）+ `.githooks/pre-commit`（归属 + pinmap/protocol 契约门）；`tools/bootstrap.sh` 设 `core.hooksPath=.githooks`。
- **P4 结构化签字 ✅**：人工门 skill（plan-solution/select-parts/power-design/interconnect/firmware-scaffold）正文改为 AskUserQuestion 取确认 → `tools/signoff.py approve <signoff>` 写 `design/signoffs.yaml`。
- **P5 形态 B ✅**：新增 `/elec-orchestrate`（单人单会话子代理 fan-out），与 `/elec-design`（3 机协同）共用同一 DAG/门/签字；形态切换 `.elec-mode`。
- **回归**：`sh tools/selftest.sh` 扩到 11 步，新增门-状态耦合、`--report`+`gate_check`、归属强制三项，全绿。

---

## 9. 开放项决议（实现采用的选择）

1. **frontmatter 字段名**：采用设计稿命名 `reads/writes/gate/signoff`（+ `lane/needs/allowed-tools`）。
2. **形态 B 编排**：当前用 **Agent 工具**（`/elec-orchestrate` 内 `Task`/`run_in_background` fan-out），轻、与现有 board DAG 直接对接；DAG 已是单一来源，后续若要确定性 pipeline 可平滑换 Workflow。
3. **pre-commit 接入**：仓库内 `.githooks/` + `bootstrap.sh` 设 `core.hooksPath`（不引入 `pre-commit` 框架依赖，纯 sh，零额外安装）。
4. **门-状态校验位置**：抽到 `tools/gatelib.py`，`board.py done` 与 `tools/gate_check.py` 共用——避免逻辑漂移（采纳设计稿"后者"建议）。
