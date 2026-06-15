# TI 电赛主控总览（MSPM0 为主线，附 MSP430 / C2000 / TIVA）

> 资料采集 agent · TI 主控线整理。面向 NUEDC 电赛小车电控流水线，供 select-parts / setup-env / firmware-scaffold 等 skill 参考。
> 与 `kb/03-主控选型-MSPM0与STM32.md` 互补：本目录更细、更偏"怎么用 / SDK / 现成轮子"。

## 一句话定位

- **TI 杯赛区赛/省赛**：主控直接上 **MSPM0G3507**（80MHz M0+、模拟外设极强、QEI+死区PWM+MATHACL 一体、官方器件支持/可报销）。
- 其余 TI 系列（MSP430 / C2000 / TIVA）多为历史或特殊场景，电赛小车新项目基本被 MSPM0 取代，只需了解定位。

## 为什么 2024–2025 大量转向 MSPM0

| 驱动因素 | 说明 |
|---|---|
| **TI 杯生态绑定 + 报销** | 赛区赛/省赛由 TI 杯冠名，用 TI 器件可获器件支持；nuedc 培训网建有 MSPM0 学习中心 + 配套 LaunchPad + 中文教程，评审与开源风向都偏 TI |
| **官方推荐器件** | 2024 起 TI 杯推荐列表把 MSPM0C/L/G 与 MSP430/C2000/TIVA 并列重点支持，G 系列成"运动控制/小车/循迹"主力 |
| **模拟外设密度爆表** | mixed-signal MCU：片内 2×12bit 4Msps ADC + 12bit DAC + 3 高速比较器 + 2 斩波运放 + 1 通用运放，STM32 主流型号给不到，综合赛题少焊外围 |
| **运动控制对口** | 内置 QEI 正交编码器接口 + 22 路 PWM + 带死区高级定时器 + MATHACL 数学加速器，PID 测速闭环开箱即用 |
| **极致性价比** | G3507 单片约 6–10 元；立创天猛星/地猛星 5 片套装 ≈29.9 元起，练手白菜价；LaunchPad 官方百元级 |

## TI MCU 系列定位速查

| 系列 | 内核 / 主频 | 典型定位 | 电赛角色（小车视角） |
|---|---|---|---|
| **MSPM0**（C/L/G） | Arm Cortex-M0+ / 24–80MHz | 通用低功耗 + 强模拟，"mixed-signal MCU" | **主力**。G3507 是循迹小车/运动控制标配 |
| **MSP430**（F5/FR 系列） | 16-bit RISC / 8–25MHz | 超低功耗、FRAM | 老牌低功耗题（能量计量、便携测量）；小车少用，新项目让位 MSPM0 |
| **C2000**（F28xx 如 F280049） | C28x + CLA / 100–200MHz | 实时数字电源 / 高性能电机 FOC | 电力电子、逆变器、无刷 FOC 等高端控制题；小车循迹用不上，门槛高 |
| **TIVA / Tiva C**（TM4C123/1294） | Cortex-M4F / 80–120MHz | 通用高性能 M4F，有 FPU | 旧电赛常见 M4F 备选；现被 MSPM0G + 生态压制，新项目少选 |

> 选型结论：**小车/循迹/运动控制 → MSPM0G3507**；能量/超低功耗便携题可看 MSP430(FR)；数字电源/无刷 FOC 才考虑 C2000。TIVA/MSP432 已基本退役。

## MSPM0 家族内部三档（详见 01）

| 子系列 | 主频 | Flash / SRAM | ADC | CAN-FD | 定位 |
|---|---|---|---|---|---|
| **MSPM0C**（如 C1104） | 24–32MHz | ≤16–32KB / ≤4KB | 1×12bit 1Msps | 无 | 极简、最便宜，替代 8 位机/逻辑胶水 |
| **MSPM0L**（如 L1306/L1117） | 32MHz | ≤64KB / ≤4KB | 1×12bit 1Msps | 无 | 入门通用，小外设、低成本 |
| **MSPM0G**（如 **G3507**） | **80MHz** | ≤128KB / 32KB | 2×12bit 4Msps（或 14bit 250ksps） | **有** | 高性能 + 强模拟 + 运动控制，**电赛小车主力** |

口诀：**算力/外设/引脚要多 → G；只要便宜够用 → L；极简 → C**。需要 >32MHz 必上 G。

## 上手最短路径（小车）

1. 买 **立创·天猛星 TMX-MSPM0G3507**（板载 DAP、中文 wiki 全、配 PID/编码器/电机套件）。
2. 装 **CCS Theia**（内置 SysConfig 免配置）或 **Keil MDK**（从 MSPM0 SDK 导入工程）。
3. 用 **SysConfig** 图形化配引脚/时钟/外设（类 CubeMX，带引脚冲突检测）。
4. 跑通三件套：**QEI/输入捕获测速 → 高级定时器互补PWM调速 → UART 收 K230 偏差**（详见 04）。
5. 注意 M0+ **无 FPU**：浮点 PID 用 **MATHACL 加速**或定点(IQMath)化。

## 参考链接

- [MSPM0G3507 产品页与数据手册（TI 官方）](https://www.ti.com/product/MSPM0G3507)
- [Application Note: M0L or M0G — How to Pick the Right MSP MCU（TI slaae67）](https://www.ti.com/lit/pdf/slaae67)
- [MSPM0 MCUs Quick Reference Guide（TI slaae70）](https://www.ti.com/lit/slaae70)
- [TI MSPM0 MCU 学习中心（nuedc 培训网）](https://www.nuedc-training.com.cn/index/huodong/mspm0_index)
- [MSPM0G3507 开发板（nuedc 培训网）](https://www.nuedc-training.com.cn/index/huodong/mspm0_card9)
- [TI puts an Arm Cortex-M0+ in your project — MSPM0L/MSPM0G 家族概览（Hackster.io）](https://www.hackster.io/news/texas-instruments-puts-an-arm-cortex-m0-in-your-project-for-just-0-39-with-its-mspm0l-and-mspm0g-50b4bd23d5e5)
