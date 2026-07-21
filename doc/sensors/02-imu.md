# IMU 惯性测量与姿态解算

> 提供**航向角(yaw)** 和**姿态(roll/pitch)**。小车主要用 yaw 走直线 / 定角度转弯。
> 选型对照表（陀螺噪声、价位）详见 `kb/05-感知传感器选型.md`；本篇讲"怎么接、用哪个库、怎么解算、怎么校准"。

---

## 一、选型速查（接口 + 库 + 适用）

| 型号 | 轴 | 接口 | 直出角度? | 库 / 用法 | 适用 |
|---|---|---|---|---|---|
| **MPU6050** | 6 | I2C(≤400k) | 否(自解算或 DMP) | jrowberg i2cdevlib / 各 MCU 移植 | 练手、资料最多 |
| ICM-20602 | 6 | I2C/SPI(10M) | 否 | 自写读寄存器 | 智能车经典、低噪 |
| **ICM-42688-P** | 6 | I2C(1M)/SPI(24M) | 否 | 自写 SPI 驱动 | 高动态自解算主力，噪声最低 |
| MPU9250 | 9 | I2C/SPI | 否 | 带磁力计，已停产难买 | 不推荐新设计 |
| **JY901S(维特)** | 9 | UART/I2C | **是(内置卡尔曼直出欧拉角)** | 串口读帧即可 | 软件主攻、开箱即用 |

> 两种路线：①**省事**用 JY901S，UART 直接读 roll/pitch/yaw（9 轴带磁补，航向不漂）；②**自解算**用 MPU6050/ICM，自己跑互补/卡尔曼。

---

## 二、MPU6050 接线与寄存器要点（I2C）

| 引脚 | 接法 |
|---|---|
| VCC | **3.3V**（GY-521 模块板载 LDO，也可 5V；裸芯片只能 3.3V） |
| GND | 共地 |
| SDA | I2C_SDA（需上拉，模块通常已板载 4.7k） |
| SCL | I2C_SCL（需上拉） |
| AD0 | 地址选择：接 GND → **0x68**，接 VCC → 0x69（两片 MPU 共总线靠这个区分） |
| INT | 数据就绪中断，可选，接 GPIO 做精确定时采样 |

- 上电后写 `PWR_MGMT_1(0x6B)=0x00` 解除睡眠；设 `GYRO_CONFIG`/`ACCEL_CONFIG` 量程；读 `0x3B` 起的 14 字节一次取出加速度/温度/陀螺。
- 可与 OLED 等其它 I2C 设备**共用一条总线**（地址不同即可，SDA/SCL 只占一次脚）。

### DMP vs 软件融合
- **DMP**（板载数字运动处理器）：芯片内部融合直出四元数/欧拉角，调库即用、最省事，但输出 **≤200Hz、精度一般**，移植偏麻烦。
- **软件融合**：自己读原始数据跑互补/卡尔曼/Mahony，灵活、可上高采样率，推荐。

### 库链接（DMP 移植到 STM32）
- `jrowberg/i2cdevlib` — Arduino 经典 MPU6050+DMP 库，含 STM32 目录（仍在完善）。
- `utomm/STM32_HAL_MPU6050_DMP` — STM32 HAL + DMP6.12 可用示例。
- `fMeow/STM32_DMP_Driver` — 从 TI/Arduino 移植的两版 DMP 驱动。
- 纯读原始值接线/初始化：ControllersTech / 野火 MPU6050 教程。

---

## 三、姿态解算方法（性价比排序）

| 方法 | 难度 | 说明 |
|---|---|---|
| **一阶/二阶互补滤波** | 低 | 调参即上线，roll/pitch 够用，**首选** |
| Mahony 互补 | 中 | PI 调 Kp/Ki，四元数输出，智能车常用 |
| Madgwick | 中 | 梯度下降，参数少 |
| 卡尔曼滤波 | 中 | 单轴角度估计经典，计算量略大 |
| MPU6050 DMP | 极低 | 调库即用但 ≤200Hz、精度一般 |

互补滤波最小实现（俯仰角，α≈0.98）：
```c
float acc_pitch = atan2f(ay, az) * 57.2958f;        // 加速度算角度(长期准)
pitch = 0.98f * (pitch + gyro_x * dt) + 0.02f * acc_pitch; // 陀螺积分(短期准)+融合
```

> 走直线/定角转弯：只用 **yaw 角速度积分 / 模块直出 yaw** 作航向反馈，构成"航向环 + 编码器速度环"双 PID。

---

## 四、零漂校准（必做）
- **陀螺零偏**：开机让车**静止 1~2 秒**，对每轴陀螺求平均当作零偏，之后每次读数减掉它。不校准 yaw 会持续漂。
- 纯 6 轴（无磁力计）的 yaw 是陀螺积分得来，**会缓慢漂移**——转弯靠"相对角度增量"即可（转 90° = 当前 yaw + 90°），长时间绝对航向需 9 轴磁力计或 JY901S。
- JY901S 出厂已标，必要时做加速度计校准 + 磁力计椭球校准；静态精度 0.05°、动态 0.1°。

## 五、本册陷阱
- I2C **必须上拉**（模块多已板载，自己飞线裸芯片要加 4.7k 到 3.3V）。
- 两片 MPU 共总线靠 AD0 改地址；和 OLED/TOF 共总线注意地址别撞。
- 安装要**牢固不晃**，振动会污染加速度计；安装方向决定哪个轴是 yaw。
- DMP 库移植坑多（Keil 下常见未定义函数）；图省事且能上 UART 就直接 JY901S。

## 参考链接
- [jrowberg/i2cdevlib (MPU6050 DMP)](https://github.com/jrowberg/i2cdevlib)
- [utomm/STM32_HAL_MPU6050_DMP](https://github.com/utomm/STM32_HAL_MPU6050_DMP)
- [fMeow/STM32_DMP_Driver](https://github.com/fMeow/STM32_DMP_Driver)
- [ControllersTech：STM32 接 MPU6050(GY-521)](https://controllerstech.com/how-to-interface-mpu6050-gy-521-with-stm32/)
- [野火 MPU6050 姿态检测（寄存器/IIC）](https://doc.embedfire.com/mcu/stm32/f103zhinanzhe/std/zh/latest/book/MPU6050.html)
- [MPU6050 Mahony 互补滤波(Kp/Ki)](https://blog.csdn.net/lqj11/article/details/107423334)
- [MPU6050 DMP+互补+卡尔曼对比](https://blog.csdn.net/m0_75090944/article/details/143416749)
- [JY901S 三轴姿态角解析](https://blog.csdn.net/qq_27378595/article/details/132031556)
- [STM32 JY901 串口DMA空闲中断收包](https://blog.csdn.net/weixin_45751396/article/details/119641721)
- [ICM42688 量程/接口/灵敏度](https://blog.csdn.net/weixin_43705900/article/details/129883270)
