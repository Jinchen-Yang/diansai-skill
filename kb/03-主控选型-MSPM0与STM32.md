---
title: "🧠 主控选型 · TI MSPM0 与 STM32"
tags:
  - 电赛/硬件
  - 主控
aliases:
  - "主控选型对比：TI MSPM0G3507 vs STM32（电赛小车/运动控制）"
  - "03 主控选型 · TI MSPM0 与 STM32"
created: 2026-06-13
---

> [!nav] 导航
> [[00-总览MOC|📖 总览]] · ⬅ [[02-历年小车与控制类赛题|02 历年小车与控制类赛题]] · [[04-电机驱动与执行机构|04 电机驱动与执行机构]] ➡

# 🧠 主控选型 · TI MSPM0 与 STM32

> [!abstract] 本篇速览
> MSPM0G3507 vs STM32 选型、外设、开发环境、电赛取舍

## 为什么 2024–2025 电赛大量转向 MSPM0

全国大学生电子设计竞赛分两条线：**赛区赛/省赛由 TI 杯冠名**（TI 提供经费与器件支持），**国赛**则有 TI、瑞萨、立创等多家。2024 年起 TI 杯省赛官方推荐器件列表把 **MSPM0 系列（MSPM0C / MSPM0L / MSPM0G）** 与 MSP430、C2000、TIVA 并列为重点支持，G 系列（如 **MSPM0G3507**）成为"运动控制 / 小车 / 循迹"类赛题的主力主控。原因可归纳为：

- **生态绑定与报销**：TI 杯赛区用 TI 器件可获器件支持，nuedc 培训网建有 MSPM0 学习中心、配套 LaunchPad 与教程，评审与开源风向都偏 TI。
- **模拟外设极其丰富**："mixed-signal MCU"。片内集成 **2 路 12-bit 4Msps ADC + 1 路 12-bit DAC + 3 路高速比较器（带基准 DAC）+ 2 路零漂移斩波运放 + 1 路通用运放**，这是 STM32 主流型号给不到的密度，对"信号源/测量/控制"综合赛题能少焊很多外围。
- **性价比**：MSPM0G3507（80MHz/128KB/32KB）单片约 6–10 元，立创"天猛星/地猛星"开发板 5 片套装参考价 **29.9 元**起（约合单板 6 元级），LaunchPad 官方约百元级；练手成本极低。
- **运动控制对口**：内置 **QEI 正交编码器接口 + 22 路 PWM + 死区控制高级定时器 + MATHACL 数学加速器**，PID 测速闭环开箱即用。

## MSPM0G3507 关键参数（来自 TI 数据手册）

| 类别 | 规格 |
|---|---|
| 内核 | Arm **Cortex-M0+** 32-bit，最高 **80 MHz**（SysConfig 默认常配 32MHz，需手动拉到 80MHz），带 MPU、**无 FPU** |
| Flash / SRAM | **128 KB**（带 ECC） / **32 KB**（带奇偶校验） |
| ADC | **2× 12-bit、4 Msps、同步采样**，最多 17 路外部通道，可硬件触发 |
| DAC | **1× 12-bit、1 Msps**，带输出缓冲 |
| 比较器 COMP | **3× 高速比较器**，高速模式传播延迟约 **32 ns**，内置参考 DAC |
| 运放 OPA | **2× 零漂移零交叉斩波运放**（0.5 µV/°C，PGA 最高 32×）+ **1× 通用运放** |
| 定时器 | **7 个**：2× 16-bit 高级控制定时器（**带死区**，电机用）、1× 32-bit 通用、若干 16-bit 通用；其中**一个 16-bit 通用定时器支持 QEI** |
| PWM | **最多 22 路** |
| 通信 | **4× UART**（1 路支持 LIN/IrDA/DALI）、**2× SPI**（最高 32 Mbit/s）、**2× I2C**（FM+ 1Mbit/s）、**1× CAN 2.0A/B + CAN-FD** |
| 其他 | 7 通道 DMA、**MATHACL 数学加速器**（DIV/SQRT/MAC/TRIG）、AES、CRC、TRNG、RTC |
| GPIO | 最多 **60**（随封装 24/28/44/60），2 路 5V 容忍开漏、2 路 20mA 高驱动 |
| 封装 | LQFP64(PM) / LQFP48(PT) / VQFN48(RGZ) / **VQFN32(RHB)** / VSSOP28(DGS) |
| 供电 / 温度 | 1.62–3.6V，-40~125°C |

> 注意：M0+ **没有硬件 FPU**，浮点 PID 走软件浮点会偏慢；用 MATHACL 加速 DIV/SQRT，或把环路改定点/查表，是电控代码的关键优化点。

### 运动控制相关外设落地（DriverLib / SysConfig）

- **编码器测速**：把一个通用定时器设为 **QEI 模式**，时钟源选 `BUSCLK`、分频 1、Load=65535；用 `DL_TimerG_startCounter()` 启动，`DL_Timer_getTimerCount()` 读计数，固定周期取两次差值即转速；方向由 QEI 硬件判别 A/B 相位。亦可退化用 GPIO 中断模拟编码器计数。
- **电机 PWM**：高级定时器输出互补 PWM + 死区，配合 TB6612/DRV8701 等驱动；频率/占空比在 SysConfig 里设 Load/Compare 值。
- **PID 闭环**：ADC 读电流/电池，QEI 读速度，MATHACL 算环路，UART 收 K230 偏差 —— 单片即可跑完整循迹小车。

## 开发环境

| 工具 | 说明 | 取舍建议 |
|---|---|---|
| **CCS Theia**（VS Code 内核） | TI 官方主推，CCS 12.7.1 / Theia 1.4+ 内置兼容 SysConfig，免额外配置 | 新生态首选，调试器/SysConfig 一体 |
| **Keil MDK 5.38+** | 从 SDK 导入工程，首次需初始化；国内最熟 | 已有 STM32 Keil 习惯者过渡最顺 |
| **IAR** | 需单独装 standalone SysConfig | 不推荐新手 |
| **MSPM0 SDK** | 含 DriverLib 源码、`empty_driverlib_src` 等大量例程，支持 TI Arm-Clang/GCC/IAR/Keil | 务必"导入例程"而非空工程起手 |
| **SysConfig** | 图形化配引脚/外设/时钟，自动冲突检测，可云端 dev.ti.com 用 | 等价于 CubeMX，强烈建议全程用 |
| **DriverLib** | 寄存器之上的驱动层，函数前缀 `DL_`（如 `DL_GPIO_`、`DL_TimerG_`、`DL_UART_`） | 比标准库更接近 HAL 风格 |

**下载/调试器**：LaunchPad 板载 **XDS110**（Debug 设置选 CMSIS-DAP，会多出两个带 XDS110 字样的 COM 口）；立创板多用 **CMSIS-DAP**。Keil 下 CMSIS-DAP / ST-Link / J-Link / XDS110 / UniFlash 均可烧录。

## 开发板选型

| 开发板 | 价格量级 | 特点 |
|---|---|---|
| **LP-MSPM0G3507**（TI 官方 LaunchPad） | 百元级 | 板载 XDS110 调试/能量测量、3 键 2 LED（含 RGB）、温度+光照传感器、4Msps ADC 外部缓冲、BoosterPack 接口；功能全、最权威 |
| **立创·天猛星 TMX-MSPM0G3507** | 5 片 ≈29.9 元 | 板载 DAP，wiki 有 CCS-Theia/Keil 入门 + PID 套件 + 编码器/电机教程，中文资料最全，练手首选 |
| **立创·地猛星 DMX / 番茄派核心板** | 单板个位数元 | 精简核心板，做小车主控省空间、便宜 |

## STM32 作为练手与备用：选型对比

| 型号 | 内核/主频 | Flash/SRAM | FPU | 电赛定位 |
|---|---|---|---|---|
| **F103C8T6** | M3 / 72MHz | 64KB/20KB | 无 | 最便宜练手，资料海量；算力/外设偏弱 |
| **F407ZGT6** | M4 / 168MHz | 1MB/192KB | 单精度 | 图像/高速处理，性能约 F103 的 2–3 倍 |
| **G431** | **M4F / 170MHz** | 128KB/32KB | 单精度 | DSP+FPU，电机控制甜点，体积小，最接近 MSPM0G3507 定位 |
| **H7（如 H743）** | M7 / 480MHz | 大 | 双精度 | 算力过剩、贵、上手重，电赛小车基本无必要 |

**生态**：CubeMX（图形配置）+ **HAL/LL 库** 是主流，资料/开源远多于 MSPM0；Keil 或 CLion 均可。

## 取舍明确建议

- **TI 杯省赛/赛区赛**：**主控直接上 MSPM0G3507**。器件支持、官方推荐、模拟外设密度、QEI+PWM+MATHACL 一体，对"循迹小车+测量"综合题最划算。先用立创天猛星把 SysConfig+DriverLib+QEI/PWM/UART 跑通，再上自制板。
- **STM32 角色**：**练手 + 备用**。开发期用熟悉的 F103/G431 + CubeMX 验证算法（PID、滤波、K230 协议），降低风险；若临场 MSPM0 出问题或赛题不限器件，G431 是最平滑的替补（同为 M4F/128KB/32KB，但有 FPU）。
- **算法注意**：MSPM0 无 FPU，PID/姿态解算用 MATHACL 或定点化；G431 有 FPU 可直接跑 float。
- **与 K230 通信**：用 **UART** 最稳。MSPM0 有 4 路 UART（留 1 路给 printf 调试），K230 大核空出 UART1/2/4 可用；约定固定帧头+校验的二进制协议（如 `0xAA 偏差 类型 校验`），MSPM0 侧用环形缓冲解析，避免丢帧。115200 起步，循迹回传可上 460800。

## 一句话结论

> 电赛赛区赛主控 **MSPM0G3507**（模拟外设强、便宜、官方撑腰、运动控制外设齐），STM32 **G431/F103 留作练手与备用**；先在立创天猛星 + CCS Theia/SysConfig 上把 QEI 测速、PWM 调速、UART 收 K230 三件套打通。


---

## 🔑 关键要点（速记）

- 主控选 MSPM0G3507：Cortex-M0+ 80MHz、128KB Flash/32KB SRAM，定位是模拟外设极强的 mixed-signal MCU，对电赛'循迹小车+测量'综合题最划算。
- 模拟外设密度是核心优势：2×12-bit 4Msps ADC、12-bit 1Msps DAC、3 高速比较器、2 斩波运放+1 通用运放，STM32 主流型号给不到。
- 运动控制外设齐全：QEI 正交编码器接口、22 路 PWM、带死区高级定时器、MATHACL 数学加速器，PID 测速闭环开箱即用。
- M0+ 没有硬件 FPU——浮点 PID 要用 MATHACL 加速 DIV/SQRT 或改定点/查表；这是 MSPM0 电控代码最大的性能注意点。
- 开发环境：CCS Theia（内置 SysConfig 免配置，官方主推）或 Keil（从 SDK 导入工程），全程用 SysConfig 图形化配置 + DriverLib（DL_ 前缀，类 HAL 风格）。
- 为什么 2024–2025 转向 MSPM0：TI 杯省赛官方推荐 MSPM0C/L/G、器件支持报销、nuedc 学习中心、立创板 5 片 29.9 元起的极致性价比。
- 练手板首选立创天猛星 TMX-MSPM0G3507（板载 DAP、中文 wiki 全、PID/编码器套件齐）；权威首选 TI LaunchPad LP-MSPM0G3507（板载 XDS110）。
- STM32 定位为练手+备用：开发期用熟悉的 F103/G431 + CubeMX 验证算法降风险；G431（M4F/170MHz/128KB/32KB，有 FPU）是最平滑的替补。
- 与 K230(CanMV) 通信用 UART 最稳：MSPM0 留 1 路 UART 做 printf 调试，K230 大核空出 UART1/2/4；约定固定帧头+校验二进制协议 + 环形缓冲解析防丢帧。
- 落地三件套：QEI 测速（BUSCLK/Load=65535，DL_TimerG_startCounter + DL_Timer_getTimerCount 差值法）、高级定时器互补 PWM 调速、UART 收 K230 偏差，单片跑完整循迹小车。


---

## 🔗 相关笔记

- [[04-电机驱动与执行机构|04 电机驱动与执行机构]] — 编码器电机、TB6612/DRV8701、PWM调速、麦轮运动学、测速
- [[05-感知传感器选型|05 感知传感器选型]] — 灰度/电磁循迹、IMU 姿态解算、TOF 测距、里程计
- [[08-软件架构与调试工程化|08 软件架构与调试工程化]] — 分层架构、时间片调度器、FSM、VOFA+/JustFloat 调参


---

## 📚 参考资料 / 链接

- [MSPM0G3507 产品页与数据手册（TI 官方）](https://www.ti.com/product/MSPM0G3507) — 权威参数来源：80MHz Cortex-M0+、128KB/32KB、2×12-bit 4Msps ADC、12-bit 1Msps DAC、3 比较器、2 斩波运放+1 通用运放、7 定时器/22 PWM/QEI、4 UART/2 SPI/2 I2C/1 CAN-FD、最多 60 GPIO、封装清单
- [LP-MSPM0G3507 LaunchPad 评估板（TI 官方）](https://www.ti.com/tool/LP-MSPM0G3507) — 板载调试探针、按键/LED/温度光照传感器、4Msps ADC 缓冲、BoosterPack
- [2024 年 TI 杯省级电赛芯片推荐列表（nuedc 培训网）](https://www.nuedc-training.com.cn/index/news/details/new_id/322) — 官方推荐 MSPM0C/L/G 系列 + MSP430/C2000/TIVA
- [TI MSPM0 MCU 学习中心（nuedc 培训网）](https://www.nuedc-training.com.cn/index/huodong/mspm0_index) — 电赛官方 MSPM0 学习资源与开发板入口
- [MSPM0G3507 硬件资源总结（CSDN）](https://blog.csdn.net/FavorFavorFavor/article/details/149125831) — 内核/主频/Flash/SRAM/定时器/PWM/ADC/UART 等中文汇总，注明默认 32MHz 与不建议使用引脚
- [MSPM0G3507 定时器：定时中断/输出比较 PWM/正交编码器计数（CSDN 天猛星系列）](https://blog.csdn.net/wo4fisher/article/details/148566498) — QEI/PWM/定时器 SysConfig 配置实战
- [CCS 配置 MSPM0G3507（七）编码器 TIMER-QEI（CSDN）](https://blog.csdn.net/kaneki_lh/article/details/140231496) — QEI 模式时钟源 BUSCLK、Load=65535、DL_TimerG_startCounter/DL_Timer_getTimerCount
- [基于 MSPM0G3507 编码器测速补充（CSDN）](https://blog.csdn.net/weixin_60991529/article/details/140912609) — 测速差值法与方向判别细节
- [MSPM0G3507 UART 收发、printf 重定向、环形缓冲自定义协议解析（CSDN）](https://blog.csdn.net/wo4fisher/article/details/148623504) — 与视觉模块/K230 串口通信的协议解析参考
- [将 SysConfig 与 MSPM0 配合使用（TI SDK 官方文档·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/1_10_01_05/docs/chinese/tools/sysconfig_guide/doc_guide/doc_guide-srcs/sysconfig_guide_CN.html) — SysConfig 图形化配置引脚/外设/时钟，冲突检测
- [适用于 MSPM0 的 Arm Keil MDK IDE 指南（TI SDK 官方·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/latest/docs/chinese/tools/keil_ide_guide/doc_guide/doc_guide-srcs/keil_ide_guide_CN.html) — Keil 下从 SDK 导入工程的流程
- [适用于 MSPM0 的 CCS Theia IDE 指南（TI SDK 官方·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/1_20_01_06/docs/chinese/tools/ccs_theia_ide_guide/doc_guide/doc_guide-srcs/ccs_theia_ide_guide_CN.html) — CCS Theia 内置 SysConfig 免配置
- [立创·天猛星 MSPM0G3507 开发板技术文档中心（lckfb wiki）](https://wiki.lckfb.com/zh-hans/tmx-mspm0g3507/) — CCS-Theia/Keil 入门、PWM/编码器/电机/PID 套件中文教程
- [编码器驱动（立创天猛星 PID 入门套件 wiki）](https://wiki.lckfb.com/zh-hans/tmx-mspm0g3507/training/easy-pid-beginner-kit/encoder-drives.html) — 编码器接入与测速实操
- [LCKFB-TMX-MSPM0G3507 开发板（立创商城）](https://item.szlcsc.com/44281600.html) — 天猛星开发板 5 片套装参考价约 29.9 元
- [Keil 编程 MSPM0G3507（CMSIS-DAP/ST-Link/J-Link/XDS110/UniFlash）（CSDN）](https://blog.csdn.net/weixin_41784968/article/details/147376846) — 多种调试器/下载器烧录方式
- [CanMV K230 UART 例程（嘉楠官方文档）](https://www.kendryte.com/k230_canmv/zh/main/zh/example/peripheral/uart.html) — K230 UART 资源：5 个硬件 UART，小核占 UART0、大核占 UART3，用户可用 UART1/2/4
- [STM32 F103/F407/F429/F767 资源对比（腾讯云社区）](https://cloud.tencent.com/developer/article/1370264) — F103 M3/72MHz 无 FPU，F407 M4/168MHz 单精度 FPU 等对比
- [STM32F103 与 G431 硬件差异深度解析（CSDN）](https://openvela.csdn.net/69c49fb854b52172bc646fe9.html) — G431 M4F/170MHz/128KB/32KB，最接近 MSPM0G3507 的 STM32 备选
- [WeAct MSPM0G3507 开发板介绍（CNX Software）](https://www.cnx-software.com/2025/02/14/weact-mspm0g3507-development-board-texas-instruments-mspm0g3507srhbr-cortex-m0-mixed-signal-mcu/) — mixed-signal MCU 定位与第三方板交叉验证


> [!nav] [[00-总览MOC|📖 总览]] · ⬅ [[02-历年小车与控制类赛题|02 历年小车与控制类赛题]] · [[04-电机驱动与执行机构|04 电机驱动与执行机构]] ➡