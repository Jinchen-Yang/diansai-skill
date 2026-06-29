---
name: elec-orchestrate
description: 单人一机·会话内子代理编排——一个人想在本机一口气把电控设计链路（读题→方案→选材→供电→接线→骨架）自动推进时使用。读同一条流水线 DAG，用子代理并行跑可并行的步骤，复用同一套确定性门与人工签字。与 elec-design（3 机 git 协同形态）共用 DAG/门/签字，区别只在"谁来跑下一个任务"。
lane: lead
needs: []
reads:
  - STATUS.md
  - board/
  - design/
  - design/gates/
  - design/signoffs.yaml
writes:
  - STATUS.md
gate: none
signoff: none
allowed-tools: Read, Bash, Glob, Grep, Task, AskUserQuestion
---

# elec-orchestrate —— 单人子代理编排（形态 B）

> 这是**单人一机**的自动编排：你（主会话=lead）读流水线 DAG，对**当前可并行的就绪任务**起子代理（`Task` / `run_in_background`）去跑，自己只做秒级调度 + 守人工门。
> 想看 3 机 git 协同（每人各一会话、靠 pull 交接）用 `/elec-design` + `/board`。两形态**共用同一 DAG（`tools/board.py`）、同一确定性门（`design/gates/`）、同一签字（`design/signoffs.yaml`）**，状态可互相接力。

## 适用判据
- `.elec-mode` 为 `solo`（或用户明说"我一个人/一台机器，自动往下跑"）。没有就**问用户**本次是单人还是 3 人；单人写 `echo solo > .elec-mode`，3 人转 `/elec-design`。

## 每次被调用的动作

1. **探状态（只读）**：
   - `python tools/board.py status`（没初始化先 `python tools/board.py init`）。
   - `python tools/board.py list` 看**所有就绪任务**（依赖已满足的）。
2. **挑可并行的就绪任务**，按两条规则分流：
   - **`needs: multimodal` 的步骤**（`read-problem`、`select-parts` 解析 PDF）——**留在主会话自己跑**（子代理可能是非多模态模型）。读对应 `SKILL.md` 的 frontmatter 判断 `needs`。
   - 其余 `kind: skill` 的就绪任务——**各起一个子代理**并行跑，子代理的任务＝"执行该 skill 的步骤 + 跑确定性门写报告"。互相不写同一目录（按各 skill frontmatter 的 `writes` 错开；必要时 `isolation: worktree`）。
   - `kind: manual` 的任务（连线/整定/bring-up）——**摊给用户**去做，不能子代理代劳。
3. **守人工门（不下放）**：任何带 `signoff` 的步骤，子代理跑完只产出物料；**回到主会话用 AskUserQuestion 找用户确认**，再 `python tools/signoff.py approve <signoff> --by lead`。子代理不得自己签字。
4. **标完成（带门校验）**：每个任务完成前先 `python tools/gate_check.py <id>` 自检（确定性门 PASS + 签字 approved）；过了再 `python tools/board.py done <id> --by lead`——这会按 DAG 自动派生下游，新一轮就绪任务回到第 1 步。
5. **循环**直到只剩 `manual` 任务（等人）或全完成；把"现在等用户做什么、子代理在跑什么"汇报清楚。

## 子代理怎么起（要点）
- 给子代理的 prompt 里点名要它跑哪个 skill、读哪些 `reads`、写哪些 `writes`、最后跑哪个门（`--report`）。
- 子代理**不做签字、不碰别的 lane 目录**；产物落在该 skill 的 `writes` 内。
- 重活、耗时的（固件骨架、视觉骨架）适合 `run_in_background`，主会话同时推进不依赖它的步骤（抢跑）。

## 门-状态是硬约束
- `board.py done` 与 `gate_check.py` 用**同一判据**（`tools/gatelib.py`）：确定性门未 PASS / 签字未 approved，就不让标完成（除非 `--force` 留痕）。所以子代理"觉得跑完了"不算数，**门和签字说了算**。

## 与 elec-design 的分工
- `/elec-design`：3 机协同的**人工**编排（提示用户敲命令、靠 `/board` 跨机交接）。
- `/elec-orchestrate`：单人单会话的**子代理**编排（自动 fan-out）。
- 不互斥：一个人可先 `solo` 把链路自动跑通，再切 `team`（`echo team > .elec-mode`）上人继续。
