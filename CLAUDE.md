# elec_race — 电控设计智能体（仓库操作规约）

本仓库 = NUEDC 小车队的"设计指挥部"：既是知识库，也是一套 **Claude Code 驱动**的 skill 流水线。
**推理由 Claude Code 完成**（Claude Code 是运行时，背后接大模型：lead 用 Claude，队友可接 DeepSeek / GLM 等 API）。**我们不在 skill / 工具代码里直接写大模型 API 调用**——脏活交给 `tools/` 下的纯 Python 脚本（无 LLM 依赖），推理交给 Claude Code 背后的模型。

完整流水线：读题 → 方案+需求 → 环境 → 选材 → 供电 → 接线图 → 固件/视觉骨架 → 测试标定。

## 团队与 lane（重要）

3 人，各一台电脑、各一个 Claude Code 会话，**只通过本 git 仓库 + 文件 + 契约协同**（不靠模型对话）：

- **lead（控制+软件负责人，Claude Max）**：控制 lane + 顶层编排；独占维护 `contracts/`、`env/`；负责所有"读 PDF/数据手册"等**多模态**任务。
- **硬件 lane（队友，可能用 DeepSeek/GLM）**：照 `design/wiring.svg` 连线/焊接/供电；只写 `design/`。
- **算法 lane（队友，可能用 DeepSeek/GLM）**：K230 视觉；只写 `vision/`。

### 目录归属（防 git 冲突，铁律）

| 目录 | 谁可写 |
|---|---|
| `contracts/`、`env/`、`.claude/`、`tools/`、`lib/` | 只 lead |
| `design/` | 硬件 lane（+ lead 跑设计 skill 时） |
| `firmware/` | 控制 lane |
| `vision/` | 算法 lane |
| `kb/`（知识库 00~10 + 资源链接总表）、`README.md` | 人工维护，**skill 只读不改** |

- 全员在 `main`，**小步频繁提交**；干活前先 `git pull`。
- `STATUS.md` 各 lane 只编辑**自己那一节**。

## 两个神圣契约（只 lead 改，其余 lane 只读）

- `contracts/protocol.*` — K230↔MCU UART 帧协议。**改 `protocol.yaml` 后必须 `python tools/gen_protocol.py` 重新生成 `.h/.py`**，三 lane 再 pull。
- `contracts/pinmap.yaml` — 引脚映射。**改完必须 `python tools/pinmux_check.py <file>` 通过**才提交。

契约尽量早冻结、少改：改一次，控制和算法都要 pull 重对。

## 确定性门优先（不靠模型"觉得对"）

- 引脚正确性 → `tools/pinmux_check.py`；协议一致性 → `gen_protocol.py` 自检；固件 → 编译。
- **"检查通过" ≠ "设计对"**：原理图连接、封装/引脚这类**静默错误**必须人工逐网核对（见各 skill 的"人工门"）。
- 电源按**电机堵转电流**算，不是标称。

## KB 只作"参考语料"

知识库都在 **`kb/`** 下（`kb/00~10` 与 `kb/资源链接总表.md`），是参考知识（引脚说明 / 赛事章程 / 开发流程分工 / 金奖经验），skill **用 Read 查阅（路径如 `kb/03-...`），不复制进库、不当需求来源、不当器件库存**。下文及各 skill 里的 "KBxx"/"第xx篇" 简写均指 `kb/` 内对应文件。候选器件来自**主办方当年配件表**（用户丢进 `inputs/partslist/`）。常用对照：

> 01 赛事章程/限制条款 · 02 历年赛题 · 03 主控引脚事实 · 04 电机驱动 · 05 传感器 · 06 PID · 07 K230 帧协议 · 08 软件架构(4层/时间片/FSM/VOFA) · 09 备赛+金奖经验 · 10 实战 Playbook + 现场 checklist + 环境清单

## 工作流入口

- `/elec-design` — 看全流程编排、当前该做哪一步、3-lane 怎么并行。
- 各阶段 skill：`/read-problem` `/setup-env` `/select-parts` `/power-design` `/interconnect` `/firmware-scaffold` `/vision-scaffold` `/test-checklist`（部分在后续 Build Pass 实装）。
- 用户每年把**当年题目**与**主办方配件表**（PDF/文本）丢进 `inputs/problem/`、`inputs/partslist/`。

## 能力标注（异构模型）

每个 `SKILL.md` 头部标 `lane` 与 `needs`：

- `needs: multimodal` 的步骤（读题、读配件表/手册）**只在 lead/Claude lane 跑**；DeepSeek/GLM lane 跳过，消费 lead 产出的结构化结果（`design/*.yaml`）。
- 其余步骤任何模型可跑，正确性交**确定性门 + 人工门**。

## 人机并行（比赛现场时间紧）

**主会话只做秒级调度，重活丢后台子代理**（`run_in_background`）；先交付能解放人手的件（接线图），人执行时 agent 抢跑下一步。谁手头空了就向对应 skill 要"下一个不依赖别人的活"。
