---
title: "STM32 外设怎么用（小车关键三件套 + 引脚复用陷阱）"
tags:
  - 电赛/硬件
  - 主控/STM32
  - 外设
created: 2026-06-15
source: 资料采集 agent · STM32 主控线
---

# STM32 外设怎么用（电赛小车视角）

> 速览：循迹小车主控三件套 = **定时器 PWM 调速 + 定时器编码器接口测速 + UART 收视觉**；
> 加常用的 **ADC（电池/灰度）+ I2C（IMU/OLED）**。最后单列 **引脚复用陷阱**——电控最容易踩的坑。
> 下文以 HAL + CubeMX 为主线，附第 6 节高质量开源库清单。

## 一、定时器 PWM 调速（驱动电机）

原理：定时器产生 PWM，占空比 = 电机速度/力度；接 TB6612 / DRV8701 / 双路 H 桥驱动。

CubeMX/HAL 关键步骤：
1. CubeMX 里把某定时器（如 TIM1/TIM2/TIM3）某通道设为 **PWM Generation CHx**。
2. 配 **PSC（预分频）+ ARR（自动重装值）** 决定 PWM 频率：`f_pwm = f_tim / ((PSC+1)*(ARR+1))`。电机一般 **10~20 kHz**（避开人耳啸叫，又不过高）。ARR 取 999 或 7199 之类，方便占空比映射 0~ARR。
3. 代码启动：`HAL_TIM_PWM_Start(&htimX, TIM_CHANNEL_x);`
4. 改速度（改占空比）：`__HAL_TIM_SET_COMPARE(&htimX, TIM_CHANNEL_x, ccr);`，ccr ∈ [0, ARR]。
5. 双轮差速：两个通道分别给左右轮；正反转由驱动芯片的方向 GPIO（IN1/IN2）或互补 PWM 控制。

要点：**高级定时器 TIM1/TIM8 支持带死区的互补 PWM**（CHx + CHxN），适合 H 桥/无刷；普通 TIM2/3/4 单路 PWM 配方向脚即可，循迹小车足够。

## 二、定时器编码器接口测速（闭环必备）

原理：把定时器设为 **Encoder Mode**，硬件对编码器 A/B 两相正交信号自动计数并判方向——**不占用 CPU 中断**，比 GPIO 中断计数稳得多。

HAL 关键步骤（以 TIM2/TIM3/TIM4 等支持编码器的通用定时器为例）：
1. CubeMX：定时器 → **Combined Channels → Encoder Mode**；A/B 相接该定时器的 **CH1、CH2**（如 TIM2 的 PA0/PA1）。
2. 计数方向由硬件按 A/B 相位自动判定（DIR 位），无需软件判向。
3. 启动：`HAL_TIM_Encoder_Start(&htimX, TIM_CHANNEL_ALL);`
4. 读计数：`int16_t cnt = (int16_t)__HAL_TIM_GET_COUNTER(&htimX);`（用 `TIMx->CNT` 亦可）。
5. **测速（M 法/差值法）**：固定周期（如 10ms，由另一个定时器中断触发）读一次计数，本次减上次 = 该周期脉冲数 → 换算转速：
   `转速(rpm) = Δcnt / (线数 × 倍频 × 减速比) / 周期(s) × 60`。
   编码器接口默认 **4 倍频（计 A/B 全部边沿）**，换算时记得乘 4（或读数右移 2 还原单倍）。
6. 把 ARR 设大（如 65535）让计数器自由跑，用 `int16_t` 强转自动处理溢出/反向。

要点：**编码器测速 + PWM 调速 + PID** 三者组合 = 速度闭环。低速时 M 法脉冲太少误差大，可改 T 法（测脉冲间隔）或 M/T 混合。

## 三、UART 收视觉模块（K230 等）

原理：视觉模块（K230 CanMV / OpenMV）把巡线偏差、色块、数字结果按固定帧发给主控；主控用 UART 收。

HAL 关键步骤：
1. CubeMX 配 **USARTx 异步模式**，波特率与视觉端一致（**115200 起步，循迹高回报率可上 460800**）。注意 **TX/RX 必须属于同一 USART 实例**（见第 5 节陷阱）。
2. **强烈建议 DMA + 空闲中断（IDLE）接收 + 环形缓冲**，而非阻塞 `HAL_UART_Receive`：
   - `HAL_UARTEx_ReceiveToIdle_DMA(&huartX, buf, len);` 配合 `HAL_UARTEx_RxEventCallback` 处理不定长帧——这是收视觉帧最稳的姿势。
   - 或经典 **环形缓冲（ring buffer）+ 逐字节中断**，在主循环里按帧头/长度/校验解析，避免丢帧（见第 6 节库）。
3. 协议：约定 **固定帧头 + 数据 + 校验**（如 `0xAA 偏差 类型 校验`），主控侧状态机解析。本库的契约见 `contracts/protocol.*`（由 lead 维护，三 lane 共用）。
4. 留一路 UART 做 **printf 调试 / VOFA+ 上位机**（重定向 `fputc`/`_write` 到该 UART）。

## 四、ADC 与 I2C（常用外设）

**ADC（读灰度传感器 / 电池电压 / 电流）**：
- 多通道用 **ADC + DMA + 扫描模式**：DMA 把各通道结果搬进数组，CPU 直接读数组，不阻塞。`HAL_ADC_Start_DMA(&hadc, (uint32_t*)buf, n);`
- 电池电压：经分压电阻接 ADC 通道，`Vbat = adc/4095 × Vref × 分压比`。注意 Vref（一般 3.3V）与分压比。
- 灰度循迹：多路灰度传感器模拟量进多个 ADC 通道，DMA 一把读完做阈值判断。
- G431/F407 的 ADC 是 12bit 高速（5Msps/2.4Msps），通道多，混合信号题很合适。

**I2C（接 MPU6050 IMU / OLED 显示）**：
- CubeMX 配 I2Cx（标准 100kHz / 快速 400kHz）；SCL/SDA 要接上拉（板上常已有）。
- MPU6050：`HAL_I2C_Mem_Read/Write` 读寄存器，取三轴加速度+角速度；姿态解算用 **DMP 库**（板载硬件解算，省 CPU）或软件互补滤波/卡尔曼。
- OLED（SSD1306）：I2C 接，显示调试信息/状态，现场调参很方便。
- I2C 易因从机卡死导致总线锁死，软件要有超时与总线复位逻辑。

## 五、⚠️ 引脚复用陷阱（电控最容易踩的坑，单独成节）

STM32 同一物理引脚通常可复用为多种功能：**GPIO / USART(TX/RX) / PWM(TIMx_CHy) / SPI / I2C / ADC** 等。一个引脚同一时刻只能干一件事——分配引脚时极易冲突，这是电控调试最常见的"为什么不工作"。

### 5.1 三类典型冲突

1. **同脚多用冲突**：例 TIM1 的 CH1~CH4 = PA8/PA9/PA10/PA11，而 USART1 的 TX/RX = PA9/PA10——**想同时用 TIM1 四通道 PWM 和 USART1，PA9/PA10 必然撞车**。
2. **同一外设实例的引脚必须配套**：USART1 的 TX 和 RX **必须都属于 USART1**——不能把 USART1_TX 配在某脚、却拿 USART2_RX 当它的 RX。同理 SPI 的 SCK/MOSI/MISO、I2C 的 SCL/SDA、定时器编码器的两相 CH1/CH2 都必须同实例。**这是新手最易犯的错**：随手抓两个空脚当串口收发，结果分属不同 USART，永远收不到。
3. **特殊功能占用**：SWD 调试脚（PA13/PA14）、晶振脚（PC14/PC15、PD0/PD1 或 PH0/PH1）、BOOT 脚——别随便拿来当普通 IO，否则烧不进/调试断/不起振。

### 5.2 怎么避免（确定性门优先）

- **用 CubeMX 配引脚**：它会**自动检测并标红冲突**，把一个脚分给两个外设会报警；时钟树/复用关系也由它算。**这是第一道确定性门**，等价于 TI 的 SysConfig 冲突检测。
- **F1 系列特有：AFIO 重映射**。F103 默认复用脚固定，可通过 **AFIO 重映射（AFIO_MAPR）**把外设挪到另一组脚（部分重映射/完全重映射）解冲突——例如把 USART1 从 PA9/PA10 重映射到 PB6/PB7，让出 PA9/PA10 给定时器。配置顺序：开 GPIO 时钟 → 开外设时钟 → **开 AFIO 时钟** → 设重映射位。F4/G4/H7 改用更灵活的 **AF 复用编号（GPIO_AFx）**，每个脚有一张 AF 映射表，在 CubeMX 里点选即可，无需手动 AFIO。
- **分配引脚的纪律**（电赛实操）：
  1. 先把**不可动**的脚锁死：SWD 调试(PA13/14)、晶振、给视觉的 UART、给电机的 PWM、给编码器的两相。
  2. 再排 ADC/灰度、I2C(IMU/OLED)、备用 GPIO。
  3. 每加一个外设就看 CubeMX 有没有标红；冲突就重映射或换实例。
  4. **同一外设的配套脚务必同实例**——配完逐脚核对 TX↔RX、SCK/MOSI/MISO、SCL/SDA、编码器 CH1/CH2 是不是一家人。
- **本库流程**：引脚分配最终落在 `contracts/pinmap.yaml`，必须过 `tools/pinmux_check.py`（确定性门）；但"检查通过 ≠ 接线对"，原理图/封装/网络仍要**人工逐网核对**（人工门）。

### 5.3 一张"哪些脚能干啥"怎么查

- **最权威**：CubeMX 选好型号封装后，**点引脚会弹出该脚所有可选复用功能**——直接照它配最不会错。
- **数据手册（Datasheet）的 "Pinouts and pin description / Alternate function mapping" 表**：列每个脚的所有 AF。
- 国产板（正点原子/野火）的原理图和"引脚分配表"可参考其默认接法。

## 六、现成好用的开源库 / 示例（点名几个高质量的）

| 用途 | 库 / 链接 | 说明 |
|---|---|---|
| **UART 环形缓冲（收视觉帧）** | [controllerstech/stm32-uart-ring-buffer](https://github.com/controllerstech/stm32-uart-ring-buffer) | 经典 head/tail 环形缓冲，配套教程，HAL 工程直接用 |
| **UART DMA 空闲接收** | [ControllersTech: Ring buffer + UART DMA 教程](https://controllerstech.com/ring-buffer-using-head-and-tail-in-stm32/) | 不定长帧非阻塞接收，收视觉最稳姿势 |
| **PID 控制器** | [Majid-Derhambakhsh/PID-Library](https://github.com/Majid-Derhambakhsh/PID-Library) / [mbedlab/PID-Library](https://github.com/mbedlab/PID-Library) | Cortex-M 通用 PID，Kp/Ki/Kd、PonM 等，移植简单 |
| **命令行调试 Shell** | [NevermindZZT/letter-shell](https://github.com/NevermindZZT/letter-shell) | letter-shell 3.0，串口敲函数现场调参/调试，电赛现场神器 |
| **MPU6050 DMP 姿态融合** | [G-Yong/STM32_MPU6050_DMP](https://github.com/G-Yong/STM32_MPU6050_DMP) | STM32 上跑 MPU6050 DMP 硬件姿态解算 |
| **无刷 FOC（进阶）** | [SimpleFOC / Arduino-FOC](https://github.com/simplefoc/Arduino-FOC)（支持 STM32 Nucleo/BluePill/G431-ESC1） | 想做无刷/FOC 的队伍，G431B-ESC1 板有现成移植 |
| **官方电机库** | ST **MCSDK（Motor Control SDK）** | ST 官方 FOC/六步换相库，配 CubeMX，适合 G4/F4 做无刷 |
| **教学例程** | 正点原子 / 野火 配套例程 + [野火在线文档](https://doc.embedfire.com/mcu/stm32/) | 编码器/PWM/ADC/MPU6050/串口全有，中文最全 |

> 注意：开源库**作参考语料**，直接拿来用前要核对引脚、时钟、HAL 版本是否匹配你的型号；FOC/MCSDK 偏重，循迹小车一般用普通有刷电机 + 编码器 + PID 即可，无需 FOC。

## 参考链接

- [STM32 PWM 教程（ControllersTech）](https://controllerstech.com/pwm-in-stm32/) — HAL_TIM_PWM_Start、占空比、DMA PWM
- [STM32 定时器编码器模式（DeepBlueEmbedded）](https://deepbluembedded.com/stm32-timer-encoder-mode-stm32-rotary-encoder-interfacing/) — Encoder Mode 配置、TIMx->CNT 读数、4 倍频、测速差值法
- [STM32 定时器系列教程：PWM/输入捕获/编码器（ControllersTech）](https://controllerstech.com/stm32-hal/timer-tutorials/) — 定时器全功能 HAL 教程
- [STM32 定时器编码器：位置与速度估计（SteppeSchool）](https://www.steppeschool.com/blog/stm32-timer-encoder-mode) — 编码器测速换算
- [STM32 AFIO 重映射功能及标准库配置（CSDN）](https://blog.csdn.net/2301_79779075/article/details/140507687) — AFIO 重映射步骤与时钟使能
- [STM32 端口复用和重映射 AFIO（CSDN）](https://blog.csdn.net/qq_38410730/article/details/79828852) — TIM1 通道与 USART 引脚冲突实例
- [STM32 ADC 多通道 DMA 采集（CSDN）](https://blog.csdn.net/weixin_57058018/article/details/135845980) — ADC+DMA 多通道电压采集
- [野火 MPU6050 姿态检测文档](https://doc.embedfire.com/mcu/stm32/f4/hal_general/zh/latest/doc/chapter44/chapter44.html) — I2C 读 MPU6050 + 姿态解算
- [硬件 I2C 读取 MPU6050（自平衡小车实战）](https://c.miaowlabs.com/A26.html) — I2C+IMU 在小车中的应用
- [STM32 UART 环形缓冲源码（controllerstech GitHub）](https://github.com/controllerstech/stm32-uart-ring-buffer) — 环形缓冲实现
