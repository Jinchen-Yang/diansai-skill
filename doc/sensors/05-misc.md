# 人机外设：OLED 显示 / 按键 / 蜂鸣器（可选）

> 比赛现场调参、状态显示与提示用。不影响控制核心，但能大幅提升调试效率（看实时偏差/状态比盲调快得多）。

---

## 一、SSD1306 OLED（0.96" 128×64，调试神器）

### 接口与接线
两种版本，按引脚数区分：

| 版本 | 引脚 | 接法 |
|---|---|---|
| **I2C 版（4 脚，常用）** | VCC/GND/SCL/SDA | I2C 总线，需上拉（模块多已板载），地址 **0x3C**（SA0=0）或 0x3D(SA0=1) |
| SPI 版（7 脚） | VCC/GND/D0(SCK)/D1(MOSI)/RES/DC/CS | 硬件 SPI，刷新更快，占脚多 |

> 地址坑：HAL 里 7-bit 地址 0x3C 要左移成 8-bit **0x78** 传给 `HAL_I2C_Master_Transmit`（0x3D→0x7A）。OLED 不显示十有八九是地址或上拉问题。

### 库
- **u8g2 (olikraus/u8g2)**：最通用，支持 I2C/SPI/软件 SPI，可移植到 STM32（u8glib 已废弃，用 u8g2）。字库丰富。
- **afiskon/stm32-ssd1306**：轻量 STM32 HAL 库，支持 SSD1306/SH1106，I2C/SPI 都行，省资源。
- Arduino：`Adafruit_SSD1306` + `Adafruit_GFX`。

### 用法要点
- 默认用阻塞发送（`HAL_I2C_Master_Transmit`/`HAL_SPI_Transmit`）即可；刷新成为瓶颈再上 DMA。
- 显示实时偏差、PID 输出、状态机当前态、传感器原始值——现场标定效率翻倍。
- **更高效的调参用 VOFA+**：通过串口把多路浮点波形发到 PC 上位机画曲线，比 OLED 看波形强（见 `kb/08`）。OLED 适合显示离散状态/数值。

---

## 二、按键（输入 + 消抖）
- 接法：一端接 GPIO（**开内部上拉**），一端接 GND，按下读到低电平。
- **机械抖动**必须消抖，两种做法：
  - **软件延时消抖**：检测到电平变化后延时 10~20ms 再确认（简单，阻塞）。
  - **定时器扫描消抖（推荐）**：每 5~10ms 在时间片里扫一次，连续 N 次同状态才确认，非阻塞，还能区分单击/双击/长按。
```c
// 时间片里每 10ms 调用，连续读到稳定才触发
static uint8_t cnt = 0, stable = 1;
uint8_t now = HAL_GPIO_ReadPin(KEY_PORT, KEY_PIN);
if (now != stable) { if (++cnt >= 3) { stable = now; cnt = 0; if (!stable) on_key_down(); } }
else cnt = 0;
```

---

## 三、蜂鸣器（提示音）
| 类型 | 驱动 | 接法 | 特点 |
|---|---|---|---|
| **有源蜂鸣器** | GPIO 高低电平开关 | 一个 IO 控通断（经三极管放大电流，蜂鸣器电流 > IO 直驱能力时） | 内置振荡，给电就响，**只能单一频率**，简单 |
| **无源蜂鸣器** | PWM 给不同频率 | 定时器 PWM 输出 | 能发不同音调（可做提示旋律），需自己出方波 |

> 电流注意：蜂鸣器（尤其有源带线圈）电流常超过 MCU 单脚直驱能力，**用 NPN 三极管/MOS 放大**，IO 控基极，别直接拉爆 IO。续流二极管视感性负载加。

---

## 四、本册陷阱（人机外设共性）
- OLED 与 MPU6050/TOF 共用一条 I2C：地址要互不冲突（OLED 0x3C、MPU 0x68、TOF 0x29），上拉一组即可。
- 按键不消抖会一次按下触发多次；用时间片扫描法最省事且可扩展长按/双击。
- 蜂鸣器、OLED 接哪种脚要看复用：无源蜂鸣器要定时器 PWM 脚，OLED I2C 要 I2C 复用脚（对照 `contracts/pinmap.yaml`）。
- 这些都是"锦上添花"，引脚紧张时优先保证循迹/IMU/编码器，人机外设可砍。

## 参考链接
- [olikraus/u8g2 移植到 STM32 (I2C/SPI)](https://controllerstech.com/how-to-port-u8g2-graphic-lib-to-stm32/)
- [afiskon/stm32-ssd1306 库](https://github.com/afiskon/stm32-ssd1306)
- [SSD1306 OLED I2C with STM32 (HAL/CubeMX，地址 0x78)](https://controllerstech.com/oled-display-using-i2c-stm32/)
- [OLED 不显示排查：地址与上拉](https://zbotic.in/oled-display-not-working-i2c-address-library-troubleshoot/)
- 仓库内 VOFA+/软件架构：`kb/08-软件架构*.md`
