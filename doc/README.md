# `doc/` — 器件 / 开发板 / SDK 工程速查资料库

> **定位**：由多智能体蜂群全网采集、提炼后的**"怎么用 / 选什么 / 有哪些现成轮子"工程速查层**，
> 用来充实资料库、支撑本仓库的电控设计 skill 流水线。
> 与 `kb/`（深度选型 + 赛事知识 + 金奖经验）互补：**KB 管"为什么选"，doc 管"怎么用"**。
>
> ⚠ **定位说明**：本目录是**参考语料**（同 `kb/`，skill 只读不改）。器件参数/价格/堵转电流等
> 多为公开渠道交叉核对的经验值，**最终以当年主办方配件表与器件数据手册为准**；
> 引脚分配最终以 `contracts/pinmap.yaml` + `tools/pinmux_check.py` + SysConfig/CubeMX 冲突检测 + 逐网人工核对为准。

## 采集方式

5 个并行子代理（模拟硬件/控制/算法多 lane 现实分工）大范围 WebSearch（中英）+ WebFetch 权威源，
各自把所属领域提炼成结构化中文文档（表格 / 要点 / 关键代码片段），文末均附"参考链接"。

## 目录索引

### 🧠 主控 · TI 线 — [`mcu-ti/`](./mcu-ti/)
电赛主力主控。MSPM0G3507 为运动控制/循迹小车首选。
| 文件 | 内容 |
|---|---|
| [00-overview](./mcu-ti/00-overview.md) | TI 电赛主控总览：为何 2024-2025 转 MSPM0、MSPM0 vs MSP430/C2000/TIVA、C/L/G 三档 |
| [01-mspm0g3507](./mcu-ti/01-mspm0g3507.md) | 关键参数 + 外设清单（M0+/80MHz 无FPU、4Msps ADC、QEI、22 PWM、MATHACL、4UART/2SPI/2I2C/1CAN-FD），外设→小车功能→DriverLib 映射 |
| [02-toolchain-sdk](./mcu-ti/02-toolchain-sdk.md) | MSPM0 SDK/DriverLib(`DL_`)、SysConfig、CCS Theia vs Keil、XDS110/CMSIS-DAP/BSL 烧录 |
| [03-boards](./mcu-ti/03-boards.md) | LaunchPad/天猛星 TMX/地猛星 DMX/WeAct + 现成开源小车轮子 |
| [04-peripherals-howto](./mcu-ti/04-peripherals-howto.md) | QEI 测速 / 互补 PWM+死区 / UART 收 K230 / MATHACL 无FPU 优化 / **引脚复用陷阱(IOMUX·PINCMx)** |
| 📄 [MSPM0G3507-datasheet.pdf](./mcu-ti/MSPM0G3507-datasheet.pdf) | TI 官方数据手册原件（采集交付数据） |

### 🧠 主控 · STM32 线 — [`mcu-stm32/`](./mcu-stm32/)
练手 + 备用主控。G431（M4F 有 FPU）是 MSPM0G3507 最平滑替补。
| 文件 | 内容 |
|---|---|
| [00-overview](./mcu-stm32/00-overview.md) | 内核家族表、F103/F407/G431/H743 对比、为何 G431 最接近 MSPM0、选型决策树 |
| [01-toolchain-sdk](./mcu-stm32/01-toolchain-sdk.md) | 寄存器/SPL/LL/HAL 四层库、CubeMX、Keil/CubeIDE/CLion/PlatformIO、ST-Link/J-Link/DAP |
| [02-boards](./mcu-stm32/02-boards.md) | BluePill/BlackPill/WeAct、正点原子/野火/安富莱、Nucleo/Discovery |
| [03-peripherals-howto](./mcu-stm32/03-peripherals-howto.md) | PWM/编码器/UART 三件套、ADC/I2C、**引脚复用陷阱(AFIO 重映射 vs AF 编号)**、开源库点名 |

### 👁 视觉 — [`vision/`](./vision/)
| 文件 | 内容 |
|---|---|
| [00-overview](./vision/00-overview.md) | K230/OpenMV/ESP32-CAM/树莓派/Jetson 六方案对比 + 选型口诀 |
| [01-k230-canmv](./vision/01-k230-canmv.md) | K230 芯片(RISC-V+KPU)、CanMV(MicroPython) 从零上手、KPU 模型部署入口 |
| [02-k230-vision-tasks](./vision/02-k230-vision-tasks.md) | 巡线/色块/AprilTag/二维码/数字识别 任务关键代码与参数 |
| [03-uart-to-mcu](./vision/03-uart-to-mcu.md) | **K230 五个 UART：UART0(小核)/UART3(大核)占用，用户可用 UART1/2/4**、FPIOA、帧协议、接线 |

### 📡 感知传感器 — [`sensors/`](./sensors/)
| 文件 | 内容 |
|---|---|
| [00-overview](./sensors/00-overview.md) | 四类感知分工 + **按接口分类表(ADC/GPIO/I2C/SPI/UART/定时器，决定占主控哪种脚)** |
| [01-line-tracking](./sensors/01-line-tracking.md) | 灰度循迹(数字/模拟/智能) + 电磁循迹(LC 选频/运放/差比和，结合 MSPM0 内置 OPA+COMP) |
| [02-imu](./sensors/02-imu.md) | MPU6050(I2C/DMP/软件融合)、互补/Mahony/Madgwick/卡尔曼、零漂校准、进阶 ICM/JY901 |
| [03-ranging](./sensors/03-ranging.md) | VL53L0X/L1X(多片 XSHUT 改址)、HC-SR04(**Echo 5V 需分压**)、红外 |
| [04-encoder](./sensors/04-encoder.md) | 增量编码器(正交/四倍频/QEI/M·T·M-T 测速)、AS5600 磁编码、霍尔 |
| [05-misc](./sensors/05-misc.md) | SSD1306 OLED(地址坑)、按键消抖、蜂鸣器 |

### ⚙ 驱动 / 电源 / 通信调试 — [`driver-power-comm/`](./driver-power-comm/)
| 文件 | 内容 |
|---|---|
| [00-motor-driver](./driver-power-comm/00-motor-driver.md) | TB6612/DRV8701/A4950/L298N/BTS7960 等 7 款驱动 IC 对比、接线真值表、PWM 调速 |
| [01-actuators](./driver-power-comm/01-actuators.md) | 直流减速电机(含编码器/堵转电流)、舵机(**独立供电/共地三铁律**)、步进 |
| [02-power](./driver-power-comm/02-power.md) | 电池、LDO vs DCDC 决策、**多路隔离分轨**、**按堵转电流算电流预算**(→ `tools/power_budget.py`) |
| [03-comm-protocols](./driver-power-comm/03-comm-protocols.md) | UART/I2C/SPI/CAN 对比 + 帧协议设计 + 环形缓冲解析 C 代码(→ `contracts/protocol.*`) |
| [04-debug-tools](./driver-power-comm/04-debug-tools.md) | VOFA+/JustFloat 帧格式、逻辑分析仪/示波器/SWD |

## 与流水线的衔接

| 流水线步骤 (skill) | 主要参考 |
|---|---|
| `/select-parts` 选材 | `mcu-*`、`sensors/`、`driver-power-comm/00-01` |
| `/power-design` 供电 | `driver-power-comm/02-power` |
| `/interconnect` 接线/引脚 | 各篇"引脚复用陷阱"节、`sensors/00` 接口分类、`vision/03` |
| `/firmware-scaffold` 固件 | `mcu-*/04或03 外设用法`、`driver-power-comm/03-04` |
| `/vision-scaffold` 视觉 | `vision/` 全部 |
| `/test-checklist` 测试 | `driver-power-comm/04-debug-tools`、各篇标定要点 |

## 已知留待人工/多模态终核的点

- **引脚真实复用**：各 MCU 篇的复用说明须以 SysConfig(MSPM0)/CubeMX(STM32) 冲突检测 + 数据手册 IOMUX 表终核；
  本环境缺 `pdftotext`，MSPM0 数据手册 PDF 已收录但未逐页渲染抽取，参数来自 TI 产品页交叉核对。
- **堵转电流 / 价格**：经验值，最终以实测 + 当年配件表为准。
- **MSPM0 硬件 QEI 通常仅一路**：双电机闭环第二路需输入捕获/GPIO 中断模拟（见 `mcu-ti/04`）。
- **K230 UART 占用**：UART0/UART3 被系统占，用户仅 UART1/2/4（见 `vision/03`，已据嘉楠官方核对）。
