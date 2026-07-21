---
title: "STM32 主控选型总览（电赛运动控制小车视角）"
tags:
  - 电赛/硬件
  - 主控/STM32
created: 2026-06-15
source: 资料采集 agent · STM32 主控线
---

# STM32 主控选型总览（电赛小车视角）

> 速览：把 F103 / F407 / G431 / H743 四条主线讲清楚，给出电赛"循迹小车 + 运动控制 + 视觉串口"场景下的选型结论。
> 配套参考库内已有 `kb/03-主控选型-MSPM0与STM32.md`（以 MSPM0 为主轴），本系列从 STM32 侧补全。

## 一、内核家族速记（先认内核再认型号）

STM32 型号命名 `STM32 + 系列字母 + 数字`，系列字母大致对应内核与定位：

| 系列 | 内核 | 典型主频 | FPU | 定位 | 电赛角色 |
|---|---|---|---|---|---|
| F0 / G0 / C0 | Cortex-M0 / M0+ | 48~64 MHz | 无 | 低端、便宜 | 简单题/省钱，外设弱，少用 |
| F1（F103） | Cortex-M3 | 72 MHz | 无 | 经典入门 | **练手首选**，资料海量 |
| F3 / G4（G431） | Cortex-M4F | 72 / 170 MHz | 单精度 | DSP+FPU 混合信号、电机控制 | **运动控制甜点**，对标 MSPM0G3507 |
| F4（F407/F411/F429） | Cortex-M4F | 84~180 MHz | 单精度 | 性能主力 | 图像/高速/多外设主控 |
| F7 / H7（H743/H750） | Cortex-M7 | 216~480 MHz | 双精度 | 高性能 | 算力过剩，电赛小车基本不需要 |
| L 系列（L4/L5） | M4F / M33 | 中 | 单精度 | 低功耗 | 电赛少用（小车不在乎功耗） |

> 关键概念 **FPU（硬件浮点单元）**：有 FPU 才能高速跑 `float` 的 PID / 姿态解算 / 滤波。
> M3（F103）**无 FPU**，浮点走软件模拟会慢；M4F / M7 有硬件 FPU，可直接 `float`。
> 这与 MSPM0G3507（M0+ 无 FPU，要靠 MATHACL 或定点化）形成对照——**这正是 G431 相对 MSPM0 的最大算力优势**。

## 二、四个主力型号对比

| 型号 | 内核/主频 | Flash / SRAM | FPU | 封装常见 | 单片价格量级* | 电赛定位与取舍 |
|---|---|---|---|---|---|---|
| **F103C8T6** | M3 / 72 MHz | 64KB / 20KB | 无 | LQFP48 | ¥1~3（正品更高） | 最便宜、资料最多的练手芯。算力/外设偏弱，做循迹小车够用但浮点 PID 略吃力。BluePill 的灵魂 |
| **F407ZGT6 / VET6** | M4F / 168 MHz | 1MB / 192KB(+64K CCM) | 单精度 | LQFP144/100 | ¥15~30 | 资源大、外设多、有 DCMI 摄像头接口。适合一块主控吃下图像+控制+多电机的"大而全"方案 |
| **G431（C8/CB/RB）** | **M4F / 170 MHz** | 32~128KB / 32KB | 单精度 | LQFP32/48/64 | ¥5~8 | **运动控制甜点**：M4F+DSP+FPU、2×16bit 电机专用 PWM 定时器、2×12bit 5Msps ADC、3 运放 4 比较器。体积小、混合信号强，**最接近 TI MSPM0G3507 的定位**，且有 FPU |
| **H743（如 ZIT6/VIT6）** | M7 / 480 MHz | 最大 2MB / 1MB | 双精度 | LQFP100/144 | ¥30~60 | 算力过剩、贵、上手重、功耗/布线更挑。电赛小车几乎没必要，除非跑重图像/AI 推理 |

\* 价格仅为量级参考，受行情/正盗料波动很大；以立创商城（LCSC）当日价为准。

## 三、为什么 G431 最接近 MSPM0G3507 的定位

电赛 TI 杯赛区赛主推 MSPM0G3507（详见 `kb/03`）。若要在 STM32 阵营找一个"功能定位等价物"，答案是 **G431**：

| 维度 | MSPM0G3507 (TI) | STM32G431 (ST) |
|---|---|---|
| 内核 | M0+ @80MHz，**无 FPU** | **M4F @170MHz，有单精度 FPU** |
| Flash/SRAM | 128KB / 32KB | 128KB / 32KB（CB 型号） |
| 定位 | mixed-signal 混合信号 MCU | mixed-signal 混合信号 MCU |
| ADC | 2×12bit 4Msps | 2×12bit 5Msps |
| DAC / 运放 / 比较器 | 1 DAC / 3 OPA / 3 COMP | 多达 4 DAC / 3 OPA / 4 COMP |
| 电机定时器 | 高级定时器带死区 + QEI | 2×16bit 电机专用 PWM 定时器（TIM1/TIM8 带死区）+ 编码器接口 |
| 数学加速 | MATHACL（弥补无 FPU） | 硬件 FPU + CORDIC + FMAC（DSP 算子加速） |
| 生态 | TI CCS/SysConfig/DriverLib | ST CubeMX/HAL/LL |

**结论**：两者都是"为电机/电源/测量而生"的混合信号 M 系列单片，外设画风高度一致。
G431 的差异化优势是 **有硬件 FPU**——浮点 PID、姿态解算、卡尔曼可直接 `float` 跑，省去 MSPM0 的定点化负担。因此：
- **TI 杯省赛/赛区赛**（用 TI 器件可获支持）：主控上 MSPM0G3507；
- **不限器件 / 国赛 / 练手期 / MSPM0 临场出问题**：G431 是最平滑的等位替补，且开发更顺手（CubeMX 生态、FPU）。

## 四、选型决策树（电赛小车）

1. **只是练手 / 验证 PID 与协议 / 预算极紧** → **F103C8T6 + BluePill**（资料最多，缺 FPU 但循迹够用）。
2. **正经做循迹/运动控制主控，要 FPU 跑浮点闭环，体积要小** → **G431**（首选）。
3. **一块板要同时吃 摄像头(DCMI) + 多路电机 + 大缓冲 + 复杂状态机** → **F407**。
4. **要跑重图像处理 / 神经网络 / 大数据吞吐** → 才考虑 **H743**（一般电赛把视觉交给 K230，主控无需 H7）。
5. **TI 杯赛区赛、想要器件支持与官方风向** → 主控 **MSPM0G3507**，STM32 留作练手/备用。

## 五、与本系列其它文档

- `01-toolchain-sdk.md` — CubeMX / HAL / LL / SPL、Keil / CubeIDE / CLion / PlatformIO、ST-Link / J-Link / DAP-Link。
- `02-boards.md` — BluePill / BlackPill / 正点原子 / 野火 / Nucleo / Discovery 开发板选型。
- `03-peripherals-howto.md` — PWM 调速 / 编码器测速 / UART 收视觉 / ADC / I2C，**及引脚复用陷阱**。

## 参考链接

- [STM32G4 系列产品页（ST 官方）](https://www.st.com/en/microcontrollers-microprocessors/stm32g4-series.html) — M4F/170MHz、DSP+FPU、混合信号、电机控制定位
- [STM32G431V8 产品页（ST 官方）](https://www.st.com/en/microcontrollers-microprocessors/stm32g431v8.html) — 2×16bit 电机 PWM 定时器、2×12bit 5Msps ADC、3 运放 4 比较器
- [STM32G4 产品概览 PDF（ST 官方）](https://www.st.com/resource/en/product_presentation/microcontrollers-stm32g4-series-product-overview.pdf) — 213 DMIPS、CORDIC/FMAC/MATH 加速器
- [STM32F103C8T6 产品页 / LCSC 价格](https://www.lcsc.com/product-detail/C8734.html) — M3/72MHz、64KB/20KB、价格参考
- [STM32H743 / STM32H7 系列对比与替代](https://www.htelec.com/blog/STM32H743IIT6-STM32H7-Series-Comparison-Alternatives) — M7/480MHz 高性能定位
- [STM32F407 vs STM32F103 对比](https://www.eiyu.com/comparison/stm32f407igt7_stm32f103c8t6) — F407 168MHz/带 FPU vs F103 72MHz/无 FPU
- [STM32F4 系列选型详解](https://www.linkedin.com/pulse/detailed-explanation-stm32f4-series-mcu) — F4 系列内部分档
- [本库 kb/03 主控选型 · TI MSPM0 与 STM32](../../kb/03-主控选型-MSPM0与STM32.md) — MSPM0 主轴对照
