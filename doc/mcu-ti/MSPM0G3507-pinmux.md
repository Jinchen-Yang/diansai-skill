# MSPM0G3507 真实引脚复用表（IOMUX / PINCM）

> **来源**：TI 官方数据手册 `MSPM0G3507-datasheet.pdf`（ZHCSSC4C，2023-02 / rev 2025-10）
> 表 6-2「引脚属性」+ 表 6-3「信号说明」，由 `pdfplumber` 抽取后人工整理。
> 全文文本见同目录 [`MSPM0G3507-datasheet.txt`](./MSPM0G3507-datasheet.txt)。
>
> 下表为 **LQFP64(PM) 封装的功能全集**（PT48/RGZ48/RHB32/DGS28 为其子集，小封装会少掉部分 PA2x/PBxx 引脚）。

## IOMUX 机制与铁律

- 每个数字 I/O 都映射到一个引脚控制寄存器 **PINCMx**，用 `PINCM.PF` 选功能。方括号里的数字 `[n]` 就是该功能对应的 **PF 编号**（GPIO 恒为 `PF=1`，故下表不再列）。
- **一个引脚同一时刻只能接一个 IOMUX 数字功能**（但可同时叠加一个非 IOMUX 的模拟/WAKE 信号——需自行确认不冲突）。
- 模拟功能（OPA/COMP 输入输出、ADC、DAC、VREF）走专用模拟通道：`PINCM.PF=0 且 PINCM.PC=0`。
- **同一外设实例的多个信号必须各自落在"支持该实例"的引脚上**：例如要用 `UART1`，其 TX/RX 必须分别选在带 `UART1_TX`/`UART1_RX` 的引脚里——这就是"一个脚可能是串口脚、但必须 TX 和 RX 同属一个实例"的本质，分配时务必对照本表 + SysConfig 冲突检测。

## 表：每脚可用功能（数字复用 `[PF]` + 模拟）

| 引脚 | IO 结构 | 模拟功能 | 数字复用功能 `[PF]` |
|---|---|---|---|
| PA0 | 5V容限开漏 | — | UART0_TX[2] / I2C0_SDA[3] / TIMA0_C0[4] / TIMA_FAL1[5] / TIMG8_C1[6] / FCC_IN[7] · 默认 BSL I2C_SDA |
| PA1 | 5V容限开漏 | — | UART0_RX[2] / I2C0_SCL[3] / TIMA0_C1[4] / TIMA_FAL2[5] / TIMG8_IDX[6] / TIMG8_C0[7] · 默认 BSL I2C_SCL |
| PA2 | 标准 | ROSC | TIMG8_C1[2] / SPI0_CS0[3] / TIMG7_C1[4] / SPI1_CS0[5] |
| PA3 | 标准 | LFXIN | TIMG8_C0[2] / SPI0_CS1[3] / UART2_CTS[4] / TIMA0_C2[5] / COMP1_OUT[6] / TIMG7_C0[7] / TIMA0_C1[8] / I2C1_SDA[9] |
| PA4 | 标准 | LFXOUT | TIMG8_C1[2] / SPI0_POCI[3] / UART2_RTS[4] / TIMA0_C3[5] / LFCLK_IN[6] / TIMG7_C1[7] / TIMA0_C1N[8] / I2C1_SCL[9] |
| PA5 | 标准 | HFXIN | TIMG8_C0[2] / SPI0_PICO[3] / TIMA_FAL1[4] / TIMG0_C0[5] / TIMG6_C0[6] / FCC_IN[7] |
| PA6 | 标准 | HFXOUT | TIMG8_C1[2] / SPI0_SCK[3] / TIMA_FAL0[4] / TIMG0_C1[5] / HFCLK_IN[6] / TIMG6_C1[7] / TIMA0_C2N[8] |
| PA7 | 标准 | — | COMP0_OUT[2] / CLK_OUT[3] / TIMG8_C0[4] / TIMA0_C2[5] / TIMG8_IDX[6] / TIMG7_C1[7] / TIMA0_C1[8] |
| PA8 | 标准 | — | UART1_TX[2] / SPI0_CS0[3] / UART0_RTS[4] / TIMA0_C0[5] / TIMA1_C0N[6] |
| PA9 | 高速 | — | UART1_RX[2] / SPI0_PICO[3] / UART0_CTS[4] / TIMA0_C1[5] / RTC_OUT[6] / TIMA0_C0N[7] / TIMA1_C1N[8] / CLK_OUT[9] |
| PA10 | 高驱动 | — | UART0_TX[2] / SPI0_POCI[3] / I2C0_SDA[4] / TIMA1_C0[5] / TIMG12_C0[6] / TIMA0_C2[7] / I2C1_SDA[8] / CLK_OUT[9] · 默认 BSL UART_TX |
| PA11 | 高驱动 | — | UART0_RX[2] / SPI0_SCK[3] / I2C0_SCL[4] / TIMA1_C1[5] / COMP0_OUT[6] / TIMA0_C2N[7] / I2C1_SCL[8] · 默认 BSL UART_RX |
| PA12 | 高速 | — | UART3_CTS[2] / SPI0_SCK[3] / TIMG0_C0[4] / **CAN_TX[5]** / TIMA0_C3[6] / FCC_IN[7] |
| PA13 | 高速 | COMP0_IN2- | UART3_RTS[2] / SPI0_POCI[3] / UART3_RX[4] / TIMG0_C1[5] / **CAN_RX[6]** / TIMA0_C3N[7] |
| PA14 | 高速 | COMP0_IN2+ / A0_12 | UART0_CTS[2] / SPI0_PICO[3] / UART3_TX[4] / TIMG12_C0[5] / CLK_OUT[6] |
| PA15 | 标准 | A1_0 / DAC_OUT / OPA0_IN2+ / OPA1_IN2+ / COMP0_IN3+ / COMP1_IN3+ | UART0_RTS[2] / SPI1_CS2[3] / I2C1_SCL[4] / TIMA1_C0[5] / TIMG8_IDX[6] / TIMA1_C0N[7] / TIMA0_C2[8] |
| PA16 | 标准 | A1_1 / OPA1_OUT | COMP2_OUT[2] / SPI1_POCI[3] / I2C1_SDA[4] / TIMA1_C1[5] / TIMA1_C1N[6] / TIMA0_C2N[7] / FCC_IN[8] |
| PA17 | 标准(唤醒) | A1_2 / OPA1_IN1- / COMP0_IN1- | UART1_TX[2] / SPI1_SCK[3] / I2C1_SCL[4] / TIMA0_C3[5] / TIMG7_C0[6] / TIMA1_C0[7] |
| PA18 | 标准(唤醒) | A1_3 / OPA1_IN1+ / COMP0_IN1+ / GPAMP_IN- | UART1_RX[2] / SPI1_PICO[3] / I2C1_SDA[4] / TIMA0_C3N[5] / TIMG7_C1[6] / TIMA1_C1[7] · 默认 BSL_Invoke |
| **PA19** | 高速 | — | **SWDIO[2]**（调试，勿占） |
| **PA20** | 标准 | — | **SWCLK[2]**（调试，勿占） |
| PA21 | 标准 | A1_7 / COMP2_IN1- / VREF- | UART2_TX[2] / TIMG8_C0[3] / UART1_CTS[4] / TIMA0_C0[5] / TIMG6_C0[6] · ⚠注:内部测试连接,禁注入电流 |
| PA22 | 标准 | A0_7 / GPAMP_OUT / OPA0_OUT | UART2_RX[2] / TIMG8_C1[3] / UART1_RTS[4] / TIMA0_C1[5] / CLK_OUT[6] / TIMA0_C0N[7] / TIMG6_C1[8] |
| PA23 | 标准 | COMP1_IN1- / VREF+ | UART2_TX[2] / SPI0_CS3[3] / TIMA0_C3[4] / TIMG0_C0[5] / UART3_CTS[6] / TIMG7_C0[7] / TIMG8_C0[8] |
| PA24 | 标准 | A0_3 / OPA0_IN1- | UART2_RX[2] / SPI0_CS2[3] / TIMA0_C3N[4] / TIMG0_C1[5] / UART3_RTS[6] / TIMG7_C1[7] / TIMA1_C1[8] |
| PA25 | 标准 | A0_2 / OPA0_IN1+ | UART3_RX[2] / SPI1_CS3[3] / TIMG12_C1[4] / TIMA0_C3[5] / TIMA0_C1N[6] |
| PA26 | 标准 | A0_1 / COMP0_IN0+ / OPA0_IN0+ / GPAMP_IN+ | UART3_TX[2] / SPI1_CS0[3] / TIMG8_C0[4] / TIMA_FAL0[5] / **CAN_TX[6]** / TIMG7_C0[7] |
| PA27 | 标准 | A0_0 / COMP0_IN0- / OPA0_IN0- | RTC_OUT[2] / SPI1_CS1[3] / TIMG8_C1[4] / TIMA_FAL2[5] / **CAN_RX[6]** / TIMG7_C1[7] |
| PA28 | 高驱动 | — | UART0_TX[2] / I2C0_SDA[3] / TIMA0_C3[4] / TIMA_FAL0[5] / TIMG7_C0[6] / TIMA1_C0[7] |
| PA29 | 标准 | — | I2C1_SCL[2] / UART2_RTS[3] / TIMG8_C0[4] / TIMG6_C0[5] |
| PA30 | 标准 | — | I2C1_SDA[2] / UART2_CTS[3] / TIMG8_C1[4] / TIMG6_C1[5] |
| PA31 | 高驱动 | — | UART0_RX[2] / I2C0_SCL[3] / TIMA0_C3N[4] / TIMG12_C1[5] / CLK_OUT[6] / TIMG7_C1[7] / TIMA1_C1[8] |
| PB0 | 标准 | — | UART0_TX[2] / SPI1_CS2[3] / TIMA1_C0[4] / TIMA0_C2[5] |
| PB1 | 标准 | — | UART0_RX[2] / SPI1_CS3[3] / TIMA1_C1[4] / TIMA0_C2N[5] |
| PB2 | 标准 | — | UART3_TX[2] / UART2_CTS[3] / I2C1_SCL[4] / TIMA0_C3[5] / UART1_CTS[6] / TIMG6_C0[7] / TIMA1_C0[8] |
| PB3 | 标准 | — | UART3_RX[2] / UART2_RTS[3] / I2C1_SDA[4] / TIMA0_C3N[5] / UART1_RTS[6] / TIMG6_C1[7] / TIMA1_C1[8] |
| PB4 | 标准 | — | UART1_TX[2] / UART3_CTS[3] / TIMA1_C0[4] / TIMA0_C2[5] / TIMA1_C0N[6] |
| PB5 | 标准 | — | UART1_RX[2] / UART3_RTS[3] / TIMA1_C1[4] / TIMA0_C2N[5] / TIMA1_C1N[6] |
| PB6 | 标准 | — | UART1_TX[2] / SPI1_CS0[3] / SPI0_CS1[4] / TIMG8_C0[5] / UART2_CTS[6] / TIMG6_C0[7] / TIMA1_C0N[8] |
| PB7 | 标准 | — | UART1_RX[2] / SPI1_POCI[3] / SPI0_CS2[4] / TIMG8_C1[5] / UART2_RTS[6] / TIMG6_C1[7] / TIMA1_C1N[8] |
| PB8 | 标准 | — | UART1_CTS[2] / SPI1_PICO[3] / TIMA0_C0[4] / COMP1_OUT[5] |
| PB9 | 标准 | — | UART1_RTS[2] / SPI1_SCK[3] / TIMA0_C1[4] / TIMA0_C0N[5] |
| PB10 | 标准 | — | TIMG0_C0[2] / TIMG8_C0[3] / COMP1_OUT[4] / TIMG6_C0[5] |
| PB11 | 标准 | — | TIMG0_C1[2] / TIMG8_C1[3] / CLK_OUT[4] / TIMG6_C1[5] |
| PB12 | 标准 | — | UART3_TX[2] / TIMA0_C2[3] / TIMA_FAL1[4] / TIMA0_C1[5] |
| PB13 | 标准 | — | UART3_RX[2] / TIMA0_C3[3] / TIMG12_C0[4] / TIMA0_C1N[5] |
| PB14 | 标准 | — | SPI1_CS3[2] / SPI1_POCI[3] / SPI0_CS3[4] / TIMG12_C1[5] / TIMG8_IDX[6] / TIMA0_C0[7] |
| PB15 | 标准 | — | UART2_TX[2] / SPI1_PICO[3] / UART3_CTS[4] / TIMG8_C0[5] / TIMG7_C0[6] |
| PB16 | 标准 | — | UART2_RX[2] / SPI1_SCK[3] / UART3_RTS[4] / TIMG8_C1[5] / TIMG7_C1[6] |
| PB17 | 标准 | A1_4 / COMP1_IN2- | UART2_TX[2] / SPI0_PICO[3] / SPI1_CS1[4] / TIMA1_C0[5] / TIMA0_C2[6] |
| PB18 | 标准 | A1_5 / COMP1_IN2+ | UART2_RX[2] / SPI0_SCK[3] / SPI1_CS2[4] / TIMA1_C1[5] / TIMA0_C2N[6] |
| PB19 | 标准 | A1_6 / COMP2_IN1+ / OPA1_IN0+ | COMP2_OUT[2] / SPI0_POCI[3] / TIMG8_C1[4] / UART0_CTS[5] / TIMG7_C1[6] |
| PB20 | 标准 | A0_6 / OPA1_IN0- | SPI0_CS2[2] / SPI1_CS0[3] / TIMA0_C2[4] / TIMG12_C0[5] / TIMA_FAL1[6] / TIMA0_C1[7] / TIMA1_C1N[8] |
| PB21 | 标准 | COMP2_IN0+ | SPI1_POCI[2] / TIMG8_C0[3] |
| PB22 | 标准 | COMP2_IN0- | SPI1_PICO[2] / TIMG8_C1[3] |
| PB23 | 标准 | — | SPI1_SCK[2] / COMP0_OUT[3] / TIMA_FAL0[4] |
| PB24 | 标准 | A0_5 / COMP1_IN1+ | SPI0_CS3[2] / SPI0_CS1[3] / TIMA0_C3[4] / TIMG12_C1[5] / TIMA0_C1N[6] / TIMA1_C0N[7] |
| PB25 | 标准 | A0_4 | UART0_CTS[2] / SPI0_CS0[3] / TIMA_FAL2[4] |
| PB26 | 标准 | COMP1_IN0+ | UART0_RTS[2] / SPI0_CS1[3] / TIMA0_C3[4] / TIMG6_C0[5] / TIMA1_C0[6] |
| PB27 | 标准 | COMP1_IN0- | COMP2_OUT[2] / SPI1_CS1[3] / TIMA0_C3N[4] / TIMG6_C1[5] / TIMA1_C1[6] |

## 小车视角速查（从上表归纳）

- **UART 实例与候选脚**（留 1 路做 printf/VOFA）：
  - UART0_TX: PA0/PA10/PA28/(PB0)；UART0_RX: PA1/PA11/PA31/(PB1)
  - UART1_TX: PA8/PA17/PB4/PB6；UART1_RX: PA9/PA18/PB5/PB7
  - UART2_TX: PA21/PA23/PB15/PB17；UART2_RX: PA22/PA24/PB16/PB18
  - UART3_TX: PA14/PA26/PB2/PB12；UART3_RX: PA13/PA25/PB3/PB13
- **PWM 电机调速**：高级定时器 **TIMA0/TIMA1** 的 `Cx`（正向）/`CxN`（互补，带死区）成对；如 TIMA0_C0(PA8) + TIMA0_C0N(PA9)。舵机 50Hz 也可用 TIMA/TIMG 任一通道。
- **编码器测速（QEI）**：用 **TIMG8** 做正交解码——A/B 落在 `TIMG8_C0`/`TIMG8_C1`，索引 `TIMG8_IDX`(PA1/PA7/PA15/PB14)。⚠ **硬件正交解码通常仅 TIMG8 这一路**，双电机第二路需用另一定时器输入捕获或 GPIO 中断模拟（见 `04-peripherals-howto.md`）。
- **I2C**（接 MPU6050/OLED，需上拉）：I2C0_SDA/SCL（PA0/1、PA10/11…）；I2C1_SDA/SCL（PA3/4、PA15/16/17/18…）。
- **SPI**：SPI0 / SPI1，各有 SCK/PICO/POCI/CSx 一组候选脚。
- **CAN-FD**：CAN_TX = PA12 或 PA26；CAN_RX = PA13 或 PA27。
- **ADC**：ADC0 通道 A0_x、ADC1 通道 A1_x（见上表"模拟功能"列与数据手册表 6-3）；灰度/电池分压接这些脚。
- **调试 SWD**：SWDIO=PA19、SWCLK=PA20 —— **永久保留，分配时跳过**。
- **5V 容限**：仅 PA0/PA1（开漏）天然 5V 容限，其余脚最大 ~VDD+0.3；接 5V 传感器（HC-SR04 Echo 等）需电平处理。

> ⚠ 不同封装引脚不全：小封装（RHB32/DGS28）会缺很多 PA2x/PBxx。落到具体板子时以该封装引出 + SysConfig 为准。

## 参考链接
- 本目录 `MSPM0G3507-datasheet.pdf`（TI ZHCSSC4C）表 6-2 / 6-3 / 6-4 / 7.1
- TI 产品页：https://www.ti.com/product/MSPM0G3507
- 详见技术参考手册 (TRM) 的 "IOMUX" 一章
