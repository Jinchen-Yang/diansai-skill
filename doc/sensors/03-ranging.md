# 测距：TOF 激光 / 超声波 / 红外

> 用于避障、到边检测、停车对位。精准定位优先 TOF，省钱粗测用超声，只判有无障碍用红外。

---

## 一、选型速查

| 传感器 | 量程 | 精度 | 接口 | 频率 | 备注 |
|---|---|---|---|---|---|
| **VL53L0X** 激光TOF | ≤2m | ±3% / 1mm 分辨率 | I2C | 默认~30Hz | 不受目标颜色/反射率影响、窄视场、精准 |
| **VL53L1X** 激光TOF | ≤4m | 高 | I2C | 可达50Hz | L0X 升级，更远更快，支持 ROI 多区域 |
| HC-SR04 超声波 | 2cm~4m | ±1~3mm(理想) | Trig/Echo(GPIO+定时器) | ~20Hz | 最便宜，波束宽(~15°)，软表面/温度易误测 |
| 红外避障 | cm 级 | 二值 | GPIO | 快 | 只判有无障碍、不测距，电位器调距离 |

---

## 二、VL53L0X / VL53L1X（I2C 激光 TOF）

### 接线
| 引脚 | 接法 |
|---|---|
| VCC | 2.6~5V（模块带稳压，常用 3.3V/5V） |
| GND | 共地 |
| SDA/SCL | I2C，需上拉（模块多已板载） |
| **XSHUT** | 关断/复位脚，**多片共总线改地址必接**（拉低使该片休眠） |
| GPIO1/INT | 数据就绪中断，可选 |

默认 7-bit 地址 **0x29**（8-bit 写 0x52 / 读 0x53）。

### 量程模式与精度权衡（VL53L0X）
通过 **timing budget（单次测量时间预算）** 调精度/速度：
- 默认 ~33ms；高精度模式可设 200ms（精度更高但更新慢）。**经验：timing budget ×4 → 精度约 ×2**。
- 测距模式：单次 polling、连续 polling、连续中断、定时（带间隔）。还有 long range（开到 ~2m）。
- L1X 支持 short/medium/long 三档距离模式 + ROI 选感兴趣区。

### 多片共一条 I2C 总线（地址相同必须改址）
所有 TOF 默认都是 0x29，直接挂会冲突。标准流程：
1. 上电时用 **XSHUT 把所有片拉低**（全部休眠）。
2. 逐片放出来：拉高第 1 片 XSHUT，调库 `setAddress(新地址)` 改成不冲突的地址。
3. 再放第 2 片、改址……以此类推。改完各片地址唯一即可同总线并存。

### 库
- Arduino：`pololu/vl53l0x-arduino`、`pololu/vl53l1x-arduino`（含 `ContinuousMultipleSensors` 多片示例）。
- STM32：`stm32duino/VL53L0X` / `VL53L1X`（构造函数带 I2C 实例、XSHUT 脚、INT 脚、地址参数），或 ST 官方 API（ULD / Full API）。
- 立创 wiki 有 VL53L0X STM32 驱动与接线。

```cpp
// Pololu 库：连续测量 + 读距离(mm)
sensor.init();
sensor.setMeasurementTimingBudget(50000);  // 50ms，平衡速度/精度
sensor.startContinuous();
uint16_t mm = sensor.readRangeContinuousMillimeters();
```

---

## 三、HC-SR04 超声波（Trig/Echo + 定时器测脉宽）

### 原理与公式
给 Trig 一个 >10µs 高脉冲触发，模块发 8 个 40kHz 超声波；Echo 输出一个**高电平**，其宽度 = 往返飞行时间。
`距离cm = echo_us / 58`（声速 ≈ 340m/s，`331.4 + 0.6·T`℃，要高精度可按温度补偿）。

### 接法与测量方式
| 引脚 | 接法 |
|---|---|
| VCC | **5V**（HC-SR04 多需 5V 才正常工作） |
| GND | 共地 |
| Trig | MCU 输出脚，给 >10µs 触发脉冲（3.3V 电平足够触发，**可直连**） |
| Echo | MCU 输入脚，测高电平脉宽 |

测脉宽两法：
1. **定时器输入捕获（推荐）**：定时器配 1MHz（1µs/计数），上升沿捕获起点、下降沿捕获终点，差值即 echo_us，不阻塞。
2. 简易：GPIO 轮询 + while 卡等高电平 + 微秒计时（阻塞，仅练手）。

### 电平注意（关键坑）
- Trig 是 MCU→模块，3.3V 输出足以触发，直连 OK。
- **Echo 是模块→MCU，输出 5V**，多数 STM32/MSPM0 引脚**不是 5V 容忍**，必须降压：分压电阻（如 1k+2k 把 5V→3.3V）或电平转换芯片，否则可能损坏 IO。先查主控该脚是否 5V 容忍。

### 库 / 参考
DeepBlueEmbedded / ControllersTech 有 STM32 输入捕获测距库；Arduino 用 `NewPing` 或直接 `pulseIn`。

---

## 四、红外避障
- 反射式红外对管 + LM393 比较器，**只输出 0/1**（有无障碍），电位器调触发距离，接 **GPIO**。
- 适合防撞/到边触发，不能当测距用。受环境光、目标颜色影响大。

---

## 五、本册陷阱（含 I2C/电平共性）
- **I2C 必须上拉**（SDA/SCL 各一个 4.7k 到 VCC，模块通常已板载；多设备共总线只需一组上拉）。
- **I2C 地址冲突**：TOF 默认全 0x29，多片必须 XSHUT 逐片改址；与 MPU6050(0x68)/OLED(0x3C) 共线时确认地址互不相同。
- **5V/3.3V 电平**：HC-SR04 的 Echo 输出 5V，必须分压/电平转换再进 3.3V MCU；TOF/红外模块带稳压，逻辑电平看模块（多为 3.3V，仍要确认）。
- 超声波波束宽（~15°）、对软/斜面易漏测；TOF 视场窄但怕强环境红外光（阳光）。
- 测距更新率有限（超声 ~20Hz、TOF 默认 ~30Hz），控制环里别假设它能很快——按帧到达更新，不要盲等。

## 参考链接
- [VL53L0X 数据手册 (ST)](https://www.st.com/resource/en/datasheet/vl53l0x.pdf)
- [VL53L0X 官方页 ST](https://www.st.com/en/imaging-and-photonics-solutions/vl53l0x.html)
- [pololu/vl53l0x-arduino (Single 示例)](https://github.com/pololu/vl53l0x-arduino/blob/master/examples/Single/Single.ino)
- [pololu/vl53l1x-arduino 多片示例 ContinuousMultipleSensors](https://github.com/pololu/vl53l1x-arduino/blob/master/examples/ContinuousMultipleSensors/ContinuousMultipleSensors.ino)
- [stm32duino/VL53L0X 库](https://github.com/stm32duino/VL53L0X)
- [VL53L0X/L1X 模式与 timing budget 讲解](https://wolles-elektronikkiste.de/en/vl53l0x-and-vl53l1x-tof-distance-sensors)
- [立创 VL53L0X STM32 驱动与接线](https://wiki.lckfb.com/zh-hans/dkx-stm32f103c8t6/module/sensor/vl53l0x-laser-distance-sensor.html)
- [STM32 HC-SR04 输入捕获库 (DeepBlue)](https://deepbluembedded.com/stm32-ultrasonic-sensor-input-capture-library/)
- [HC-SR04 与 STM32 (ControllersTech，含电平转换)](https://controllerstech.com/hcsr04-ultrasonic-sensor-and-stm32/)
