# STATUS — 任务板

> 用法：干活前 `git pull`；更新**自己 lane 那一节**后 `git commit -am "status: ..."` 再 `git push`。
> 阻塞 / 跨 lane 同步点写到末尾。契约版本变更必须在此标注，提醒三 lane 重新 pull。

> **系统就绪**：9 段 skill 全部实装并自测通过（`sh tools/selftest.sh`）。
> 完整走查样例在 `examples/sending-medicine-2023/`（problem→solution→bom→power→pinmap→wiring→firmware→vision→test_plan）。
> 比赛时：把当年题目丢进 `inputs/problem/`、配件表丢进 `inputs/partslist/`，从 `/elec-design` 起跑真实流程。

**当前阶段**：① 读题（待 `inputs/problem/` 投喂当年题目）
**契约版本**：`protocol v0.1`（已生成）· `pinmap` 未生成（样例在 contracts/pinmap.example.yaml）

---

## lead（控制 + 编排）
- [ ] 待用户把当年题目丢进 `inputs/problem/` → 跑 `/read-problem`
- [ ] 待题目就绪后 → `/plan-solution` → `/setup-env`

## 硬件 lane
- [ ] 待 `design/wiring.svg`（接线图，来自 `/interconnect`）

## 控制 lane
- [ ] 待 `firmware/` 骨架（Build Pass C）
- [x] 可先读 `contracts/protocol.h` 了解帧协议

## 算法 lane
- [ ] 待 `vision/` 骨架（Build Pass C）
- [x] 可先按 `contracts/protocol.py` 起 K230 端收发

## 阻塞 / 同步点
- （无）
