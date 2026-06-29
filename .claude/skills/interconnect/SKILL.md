---
name: interconnect
description: 生成模块接线图、引脚映射与接线表（scope-A 核心交付，解放硬件 lane）。当用户要"出接线图/连线图""分配引脚/pinmap""怎么接线""harness/线束"时使用。把 BOM 里各模块的对 MCU 引脚映射到主控可用引脚，产出 contracts/pinmap.yaml（经 pinmux_check 门）+ design/wiring.svg + harness.md，需逐网人工核对。
lane: lead
needs: []
reads:
  - design/bom.csv
  - design/power.yaml
  - lib/modules/
  - contracts/mcu/
  - contracts/pinmap.schema.yaml
  - contracts/pinmap.example.yaml
writes:
  - contracts/pinmap.yaml
  - design/wiring.svg
  - design/harness.md
  - design/gates/pinmux.yaml
  - STATUS.md
gate: pinmux
signoff: wiring-net-review
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# interconnect —— 模块接线图（流水线 ⑥）

> 能力声明见 frontmatter。lane=lead（产物落 `contracts/`、`design/`，归 lead）；YAML 任何模型都能产，正确性交确定性门。
> **确定性门** `pinmux`（`pinmux_check.py --report` 写 PASS）；**人工门** signoff `wiring-net-review`（逐网核对后 approve）。两者齐了才放行下游。

这是 scope-A 的心脏：人照它连线。**正确性靠确定性门 + 人工逐网核对，不靠模型"觉得对"。**

## 前置
`design/bom.csv`（选了哪些模块）+ `design/power.yaml`（供电轨）+ `lib/modules/`（接法块）+ `contracts/mcu/<MCU>.yaml`（引脚能力）。

## 步骤
1. **列对 MCU 网络**：对 BOM 每个模块，读其 `lib/modules/<block>.yaml`，取 `to_mcu: true` 的脚（PWM/GPIO/UART/I2C/ADC/QEI…）。没有现成块就按 KB `03/04/05` 引脚说明补一个最小块到 `lib/modules/`。
2. **分配主控引脚**：从 `contracts/mcu/<MCU>.yaml` 给每条网络挑一个**支持该功能、且未被占**的引脚；同类外设实例（UART/I2C/QEI…）注意不超数量上限。I2C/SPI 总线多模块**共享同一对引脚**（只占一次）。
3. 写 `contracts/pinmap.yaml`（结构见 `contracts/pinmap.schema.yaml`，照 `contracts/pinmap.example.yaml`）。
4. **跑确定性门（写报告）**：`python tools/pinmux_check.py contracts/pinmap.yaml --report --by <lane>`。FAIL（撞脚/非法功能/超限）就改分配，重跑直到 PASS——PASS 会把门报告写入 `design/gates/pinmux.yaml`。
5. **渲染**：`python tools/render_wiring.py contracts/pinmap.yaml design/wiring` → `design/wiring.svg`（接线图）+ `design/harness.md`（接线表）。
6. **人工门（高危·必做·结构化签字）**：让用户**逐网核对** harness.md，重点：电源/GND、K230 串口 TX↔RX 交叉、I2C 上拉、舵机独立供电、SWD 没被占。用 **AskUserQuestion** 取得核对确认后落签：
   ```
   python tools/signoff.py approve wiring-net-review --by lead --note "逐网核对通过"
   ```
   `board.py done interconnect` 需 `pinmux` 门 PASS + `wiring-net-review` 签字齐才放行——硬件 lane 才接得到 `hw-wiring` 任务。
7. 更新 `STATUS.md`：硬件 lane 段贴 `design/wiring.svg`、阶段→可连线；契约版本记 `pinmap vX`。

## 注意
- pinmap 是**神圣契约**（CLAUDE.md）：改完必过 pinmux_check 才提交，并通知控制 lane 重 pull（固件 SysConfig 据此生成）。
- MCU 能力表 `verified:false` 时，pinmux PASS 只保证逻辑自洽；**真实引脚复用要 lead 用 SysConfig 核**（读手册=多模态）。
- 接线图一出，硬件 lane 即可开工——这是解放人手的解锁件，**优先最先交付**。
