---
title: "STM32 开发板选型（电赛小车主控视角）"
tags:
  - 电赛/硬件
  - 主控/STM32
  - 开发板
created: 2026-06-15
source: 资料采集 agent · STM32 主控线
---

# STM32 开发板选型（电赛小车主控视角）

> 速览：练手用最小系统板（BluePill/BlackPill）便宜，学习用国产教学板（正点原子/野火）资料全，原型/官方风用 Nucleo/Discovery（板载 ST-Link）。
> 做小车主控选板看三点：**①够不够引脚引出 ②有没有板载调试器 ③资料/例程多不多。**

## 一、最小系统板（便宜、做主控塞车上）

| 板 | 芯片 | 内核/主频 | Flash/SRAM | 价格量级 | 板载调试器 | 适合做小车主控？ |
|---|---|---|---|---|---|---|
| **BluePill 蓝板** | STM32F103C8T6 | M3/72MHz | 64KB/20KB | ¥5~15 | **无**（需外接 ST-Link/DAP 或串口 ISP） | 适合：便宜、小、引脚够循迹小车；缺 FPU、需外接下载器、市面多盗料 |
| **BlackPill 黑板** | STM32F411CEU6（或 F401） | M4F/100MHz | 512KB/128KB | ¥15~25 | **无**（USB Type-C，可 DFU 烧录） | 适合：比蓝板强、**有 FPU**、Flash 大、USB-C；做小车主控比 BluePill 更香 |
| **WeAct G431 核心板** | STM32G431CBU6 | M4F/170MHz | 128KB/32KB | ¥20~35 | 视版本 | 运动控制甜点芯的小核心板，做小车主控理想，体积小、有 FPU |

> 提示：BluePill/BlackPill 市场盗料、丝印造假多（C8T6 实为缩水片、F411 假料），买正品要认准卖家。做正式作品建议买带板载调试器的教学板或自制最小系统。

## 二、国产教学板（资料/例程最全，学习首选）

国内"STM32 三巨头"：**正点原子、野火、安富莱**——教程、例程、配套视频极全，中文资料最丰富。

| 品牌 | 代表板（系列） | 芯片档位 | 特点 | 适合 |
|---|---|---|---|---|
| **正点原子** | 战舰/精英(F103)、探索者(F407)、阿波罗(F429/F767)、北极星(H743) | F103~H7 全覆盖 | 教程通俗、面向初学者、配套视频海量、社区活跃 | 入门学习、跟教程做实验 |
| **野火（EmbedFire）** | 指南者/霸道(F103)、F407/F429/H743/H750 系列 | F103~H7 | 文档深入、讲原理透彻、HAL 与标准库双版本文档齐全 | 想搞懂底层原理 |
| **安富莱** | STM32-V5/V6/V7（F407/F429/H7） | F4~H7 | 工业级、外设全、emWin/RTOS 资料强 | 进阶/工业方向 |

电赛用法：**教学板适合开发期在桌上验证算法**（PID、滤波、串口协议、IMU），跑通后再移植到车上的最小系统板或自制板。教学板体积大、外设多但接口杂，**不建议直接装车**。

## 三、ST 官方板（板载调试器，原型友好）

| 系列 | 定位 | 板载调试器 | 特点 | 电赛角色 |
|---|---|---|---|---|
| **Nucleo**（如 NUCLEO-G431RB、F411RE、F103RB） | 主流原型板，最便宜的官方板 | **板载 ST-Link/V2-1**（一根 USB 烧+调+虚拟串口） | Arduino + Morpho 双排引脚、便宜、跨型号统一；mbed/CubeIDE 支持好 | **推荐**：要 G431/F411 又想省事时直接买对应 Nucleo，板载调试器省心 |
| **Discovery**（如 STM32F4-Disco、G431B-ESC） | 带丰富板载外设的评估板 | 板载 ST-Link | 自带传感器/屏/音频等；G431B-ESC1 是**电机驱动评估板**（带三相逆变，适合 BLDC/FOC） | 评估特定方案（如 FOC 无刷电机）时用 |

> **NUCLEO-G431RB** 对电赛运动控制很对口：G431 甜点芯 + 板载 ST-Link，开发期插上 USB 即可，无需外接下载器。
> **G431B-ESC1**（Discovery 电调板）适合要做无刷/FOC 的进阶队伍。

## 四、选板速查（电赛小车）

- **预算紧、练手、循迹小车主控**：BluePill(F103) 或更推荐 **BlackPill(F411，有 FPU)**；需自备 ST-Link/DAP。
- **要 FPU + 体积小 + 做正式主控**：**WeAct G431 核心板** 或 **NUCLEO-G431RB**（后者板载调试器更省事）。
- **学习阶段、跟教程**：**正点原子 / 野火**（F103 或 F407 教学板），资料最全。
- **要一块板吃图像(DCMI)+多电机+大缓冲**：正点原子/野火 **F407 探索者** 类板。
- **做无刷/FOC**：**STM32 G431B-ESC1** 电调评估板。

## 参考链接

- [Blue Pill vs Black Pill：F103 转 F411（Hackaday）](https://hackaday.com/2021/01/20/blue-pill-vs-black-pill-transitioning-from-stm32f103-to-stm32f411/) — 蓝板/黑板差异，F411 100MHz/512KB/128KB/M4
- [WeAct BlackPill STM32F411CEU6 开发板](https://botland.store/stm32-discovery/19769-stm32f411ceu6-blackpill-v31-development-board-with-stm32f411ceu6-microcontroller-weact-studio-5904422347536.html) — 黑板 v3.1 规格/USB-C
- [NUCLEO-F411RE 开发板（RS）](https://kr.rs-online.com/web/p/microcontroller-development-tools/8224052) — Nucleo 板载 ST-Link/V2-1
- [Nucleo-G431RB（Zephyr 文档）](https://docs.zephyrproject.org/latest/boards/st/nucleo_g431rb/doc/index.html) — G431RB Nucleo 板规格
- [细数 STM32 开发板：官方板/正点原子/野火/安富莱](https://www.cxymm.net/article/annic9/76850561) — 国产三巨头与官方板盘点
- [学习 STM32 的经验分享（面包板社区）](https://www.eet-china.com/mp/a13043.html) — 选板与学习路径建议
- [野火 STM32 开发实战指南（在线文档）](https://doc.embedfire.com/mcu/stm32/f103zhinanzhe/std/zh/latest/) — 野火教学板配套文档
