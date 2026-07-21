# MSPM0G3507 外设怎么用（小车运动控制视角）

> 给 firmware-scaffold / interconnect 用：把"测速 / 调速 / 收 K230 / 引脚复用 / 无FPU"落到 DriverLib + SysConfig。
> 所有外设都先在 SysConfig 图形化配，生成 `ti_msp_dl_config.c` 的 init，再写业务代码。控制参数=占位待整定，引脚据 `contracts/pinmap.yaml`，外设 init 需人工核对。

---

## 1. QEI 编码器测速

### 方案 A：硬件 QEI（精度高，但本芯片通常只有一路）
- 把一个通用定时器（TIMG）设为 **QEI 模式**。
- 时钟源选 **`BUSCLK`**，分频 1，**Load = 65535**（计数满量程，便于差值）。
- `DL_TimerG_startCounter()` 启动；固定周期（如 10/20ms）用 `DL_Timer_getTimerCount()` 读计数。
- **差值法测速**：本次计数 − 上次计数（注意 65535 环绕处理）→ 单位时间脉冲数 → 转速。
- **方向**：由 QEI 硬件根据 A/B 相位自动判别（计数增/减）。

### 方案 B：定时器输入捕获 / GPIO 双边沿中断模拟（双电机时给第二个电机用）
- 本芯片硬件 QEI 一般只有一路；**双电机闭环**时第二路用此法。
- A、B 相配 GPIO 上升沿（或双边沿）中断，中断里累加 `temp_count`；A 相上升沿时**读 B 相电平判方向**（B 低→一个方向，B 高→另一个方向），AB 都计可做 4 倍频。
- 20ms 定时器中断里把 `temp_count` 搬到 `count` 并清零 → 即该周期速度。
- 用到：`DL_GPIO_getEnabledInterruptStatus()`、`DL_GPIO_readPins()`、`DL_GPIO_clearInterruptStatus()`、`DL_TimerA_getPendingInterrupt()`。
- 把"按键扫描 + 编码器更新"集中放 20ms 定时中断，统一管周期任务。

---

## 2. 高级定时器互补 PWM + 死区（驱动 TB6612 / DRV8701）

- 用 **TIMA（高级控制定时器）**：支持**互补 PWM 对**（如 `TIMA0_C0` 与 `TIMA0_C0N`）+ **可编程死区插入** + 故障处理。
- SysConfig 里：选 TIMA → 设时钟源/分频 → 设 **Load**（决定频率）和 **Compare**（决定占空比）→ 开互补输出 + 死区时间。
- **驱动 TB6612**：MCU 给 2 路 PWM + 4 路方向 GPIO（AIN1/AIN2/BIN1/BIN2 控正反转），PWM 给 PWMA/PWMB；死区主要用于半桥/H桥防直通（DRV8701 等 MOSFET 栅驱更需要）。
- 频率经验：有刷电机 PWM 常 10–20kHz（避开啸叫、兼顾响应）。
- 用到：`DL_TimerA_startCounter()`、`DL_TimerA_setCaptureCompareValue()`（改占空比）。

---

## 3. UART 收 K230（视觉偏差）

- 波特率：**115200 起步，循迹回传可上 460800**（双方一致）。
- **二进制协议**：固定帧头 + 数据 + 校验，例如 `0xAA | 偏差 | 类型 | 校验和`（具体以 `contracts/protocol.*` 为准，由 lead 维护、`gen_protocol.py` 生成）。
- **环形缓冲防丢帧**：UART RX 中断（或 DMA）把字节塞进 ring buffer，主循环/时间片里**找帧头→按长度取帧→校验→解析**；不要在中断里做重活。
- **留 1 路 UART 给 printf 调试 / VOFA+**（MSPM0 有 4 路 UART，富余）。K230(CanMV) 侧：小核占 UART0、大核占 UART3，用户可用 **UART1/2/4**。
- 用到：`DL_UART_Main_enable()`、`DL_UART_Main_receiveData()` / `DL_UART_Main_transmitData()`、RX 中断或 DMA。

---

## 4. ADC（灰度/电池/电流）

- 2×12bit 4Msps，最多 17 通道，可多通道序列 + 硬件触发 + DMA。
- 灰度循迹/电池电压/电流采样常用；多通道可用 DMA 搬运减负。
- 用到：`DL_ADC12_startConversion()`、`DL_ADC12_getMemResult()`，配合 DMA。
- 电流调理可走片内 **OPA(PGA)**，过流保护走 **COMP + 内部参考 DAC**。

---

## 5. MATHACL / 无 FPU 优化（关键性能点）

- **M0+ 无硬件 FPU**：`float` PID 走软件浮点慢，高频环路会吃满 CPU。
- 两条优化路：
  1. **MATHACL 数学加速器**：硬件做 DIV / SQRT / MAC / 三角（CORDIC 类），用 `DL_MathACL_*` 调用，给浮点/三角运算提速。
  2. **定点化（IQMath）**：用 SDK 的 IQMath 库把浮点算法平滑移植成定点（Q 格式），且可挂 MATHACL 硬件加速——计算密集实时控制首选。
- 实践：PID 主体可定点化；必须 float 的少量运算用 MATHACL；避免在 1kHz 控制中断里频繁做 `double`/库 `sin/sqrt`。

---

## 6. printf 重定向 + VOFA+ 调参

- 把 `fputc`/底层 IO 重定向到一路调试 UART；用 **VOFA+ / JustFloat** 协议把多路变量实时画曲线，整 PID 极方便。
- 调试 UART 与 K230 通信 UART 分开两路，互不干扰。

---

## 7. 引脚复用陷阱（重点，电控最易错处）

MSPM0 用 **IOMUX**：每个数字 IO 对应一个 **PINCMx 寄存器**，靠其中 **PF（Pin Function）控制位**选该物理脚当前复用成哪个功能。

### 规则要点
- **同一物理引脚（PAx / PBx）可复用多种功能**：GPIO / UART(TX/RX) / SPI / I2C / **PWM(TIMx 的 CCPx 通道)** / ADC 通道 / COMP / QEI 等——但**同一时刻只能选一个**。
- **外设实例与引脚是受限映射**：不是任意脚都能当任意外设。例如某 `UARTn` 的 TX/RX **必须从该实例允许的候选引脚集合里选**；某 `TIMx_CCPy`（PWM）也只能落在该通道允许的脚上。**不能随便指定**。
- **ADC 通道是固定物理脚**（ADC0 的某通道 = 某固定 PAx），与数字复用争用要规划。
- 几个脚特殊：5V 容忍开漏脚、20mA 高驱动脚、调试 SWD 脚（SWCLK/SWDIO，被占会烧不进）、晶振脚——分配时避让。

### 落地做法（铁律）
1. **一律用 SysConfig 配引脚**，它会**自动做冲突检测**：同一脚分给两个外设、或外设选了它不支持的脚，会直接报红。
2. 配完把生成的 `ti_msp_dl_config.c`（PINCM 设置 + 各 init）与 `contracts/pinmap.yaml` **逐网人工核对**——"SysConfig 不报错" ≠ "接线对"，封装/网络这类静默错误必须人工逐网过（呼应仓库"人工门"）。
3. 电机 PWM 优先落在 **TIMA 互补对**所在脚；编码器留给 QEI/输入捕获脚；UART 收 K230 与 printf 各占一对 TX/RX；SWD 调试脚不要复用。
4. DriverLib 侧引脚配置体现为对应 `PINCMx` 的功能选择（SysConfig 已生成，一般不手撸）。

> 这是 MSPM0 电控调试翻车高发区：现象常是"程序没问题但某外设不工作 / 烧不进 / 串口乱"，根因多是引脚选了不支持该外设的脚、或两外设抢同一脚、或占了 SWD。**先查 SysConfig 冲突 + 逐网核对，再怀疑代码。**

## 参考链接

- [编码器驱动（天猛星 PID 入门套件 wiki）](https://wiki.lckfb.com/zh-hans/tmx-mspm0g3507/training/easy-pid-beginner-kit/encoder-drives.html)
- [CCS 配置 MSPM0G3507（七）编码器 TIMER-QEI（CSDN）](https://blog.csdn.net/kaneki_lh/article/details/140231496)
- [MSPM0G3507 定时器：定时中断/输出比较 PWM/正交编码器计数（CSDN）](https://blog.csdn.net/wo4fisher/article/details/148566498)
- [MSPM0G3507 之 IOMUX 功能概述（基于 DriverLib）（CSDN）](https://blog.csdn.net/wo4fisher/article/details/147161815)
- [MSPM0G3507 UART 收发/printf 重定向/环形缓冲协议解析（CSDN）](https://blog.csdn.net/wo4fisher/article/details/148623504)
- [MATHACL 数学加速器（DriverLib API·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/2_06_00_05/docs/chinese/driverlib/mspm0g1x0x_g3x0x_api_guide/html/group___m_a_t_h_a_c_l.html)
- [MSPM0 IQMath 用户指南（TI 官方·中文）](https://software-dl.ti.com/msp430/esd/MSPM0-SDK/1_10_01_05/docs/chinese/middleware/iqmath/doc_guide/doc_guide-srcs/Users_Guide_CN.html)
- [CanMV K230 UART 例程（嘉楠官方，UART0/3 被占，用户用 1/2/4）](https://www.kendryte.com/k230_canmv/zh/main/zh/example/peripheral/uart.html)
- [半小时入门 MSPM0G3507 之 PWM 串口（阿里云开发者社区）](https://developer.aliyun.com/article/1626025)
