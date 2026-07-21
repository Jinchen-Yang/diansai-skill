# 测速与里程：编码器 / 磁编码器 / 霍尔

> 提供**纵向位移（走了多远）**和**轮速（速度环反馈）**。航向交给 IMU，编码器只管里程。

---

## 一、增量编码器（A/B 正交）—— 小车主力

### 原理
输出 A、B 两路方波，**相位差 90°**：
- 计数 = 走过的脉冲数 → 换算位移/速度；
- A 超前 B 还是 B 超前 A → **判方向**（正反转）。
- 分辨率 = 线数(PPR)；正交可**四倍频(×4)**——A/B 上下沿都计数，分辨率翻 4 倍。

### 接法（电机自带霍尔编码器，如 GA25/JGB37）
| 引脚 | 接法 |
|---|---|
| M+/M- | 接电机驱动（TB6612 等），**与编码器供电分开** |
| ENC_VCC | 编码器供电 3.3V/5V（看模块） |
| ENC_GND | 共地 |
| ENC_A | 主控**定时器 QEI 通道**（如 TIMx_CH1） |
| ENC_B | 主控**定时器 QEI 通道**（如 TIMx_CH2） |

### 用定时器编码器接口（QEI）—— 硬件计数，零 CPU 占用
STM32 把定时器配成 **Encoder Mode**（TI1/TI2 接 A/B），硬件自动按方向加减计数，`CNT` 寄存器实时就是位置；MSPM0 用 TIMG 的 QEI 配置。常用 ×4 模式（双沿双通道）拿最高分辨率。

> 强烈优先 QEI 硬件计数，**不要用外部中断逐脉冲软件计数**（高转速会丢脉冲、占满 CPU）。

### 测速（差值法 / M 法）
固定控制周期 Δt 读一次 CNT，做差得增量：
```c
// 每个控制周期(如 10ms)调用一次
int16_t dcnt = (int16_t)(TIMx->CNT - last_cnt); // int16 自动处理溢出/方向
last_cnt = TIMx->CNT;
float rps = (float)dcnt / (ppr * 4) / dt;        // 轮转速 r/s
float v   = rps * 3.14159f * D;                  // 线速度 m/s，D=轮径
```
- **M 法**（定时数脉冲）：高速准、低速误差大；
- **T 法**（测脉冲间隔时间）：低速准、高速误差大；
- **M/T 法**：两者结合，全速段都准（高级，按需）。小车定周期差值法（M 法）一般够用。

### 位移（定距离走 N 米）
累加增量：`s += dcnt/(ppr*4) * π·D`，到达目标距离停车。

### 与 IMU 航向融合（解耦最稳）
```c
float ds  = (ds_left + ds_right) / 2.0f;  // 两轮平均线位移
float yaw = imu_yaw;                        // 朝向用 IMU，不用轮速差(漂移快)
x += ds * cosf(yaw);
y += ds * sinf(yaw);
```
> 编码器算"走多远"，IMU 算"朝哪"，两者解耦；不要用左右轮速差积分航向（误差累积快）。

---

## 二、AS5600 磁编码器（I2C 绝对角度）
- 12-bit 单圈绝对角度，分辨率 **0.088°(360/4096)**；芯片上方放一颗径向充磁磁铁即可非接触测角。
- I2C 读 `RAW_ANGLE(0x0C/0x0D)` 高低字节拼 12-bit，0~4095 映射 0~360°。
- 接法：VCC(3.3/5V)/GND/SDA/SCL（I2C 需上拉），DIR 脚定旋转正方向。
- 用途：旋转关节/云台/测单轴绝对角；做轮速里程需对角度差分并处理过零跳变（0↔4095）。
- 库：Arduino `RobTillaart/AS5600`、`Seeed AS5600`；STM32 自写 I2C 读寄存器。

---

## 三、霍尔测速（无编码器时的简易方案）
- 转盘贴磁钢 + 霍尔开关，每过一颗磁钢出一个脉冲，**单路只能测速、不能判方向**。
- 接 GPIO 外部中断计数或定时器捕获测脉冲间隔（T 法）。
- 精度受磁钢数限制，远不如正交编码器；仅在电机无编码器时凑合用。

---

## 四、本册陷阱
- 编码器**优先 QEI 硬件计数**，外部中断软件计数高速丢脉冲。
- A/B 接反 → 计数方向反，软件取负或交换两脚即可。
- 编码器逻辑电平要和 MCU 对上：很多霍尔编码器输出 5V 上拉，接 3.3V 非容忍脚要电平转换/确认容忍。
- 线数(PPR)、是否四倍频、轮径 D 三个参数错一个速度/里程就全错——**实测标定**：让车走固定 1m 看累计计数反推。
- AS5600 与其它 I2C 设备共线注意地址(0x36)冲突；磁铁安装高度/对心影响精度。
- ENC_A/ENC_B 必须落在主控带定时器输入捕获/QEI 能力的脚（见 `contracts/mcu/MSPM0G3507.yaml`）。

## 参考链接
- [ControllersTech：STM32 定时器编码器模式](https://controllerstech.com/incremental-encoder-with-stm32/)
- [STM32 Timer Encoder Mode (DeepBlue)](https://deepbluembedded.com/stm32-timer-encoder-mode-stm32-rotary-encoder-interfacing/)
- [STM32循迹小车（二）编码器测速（四倍频/公式）](https://blog.csdn.net/weixin_49821504/article/details/130444327)
- [增量编码器测速 M/T 法 (STM32, PMC 论文)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9324733/)
- [2024电赛H题 编码器+MPU6050 双反馈](https://blog.csdn.net/m0_63210745/article/details/140764261)
- [AS5600 磁编码器使用（Arduino，含滤波）](https://blog.csdn.net/qqliuzhitong/article/details/121795481)
- [AS5600 获取角度（0x0C/0x0D 寄存器）](https://blog.csdn.net/Lagligelang/article/details/123849543)
