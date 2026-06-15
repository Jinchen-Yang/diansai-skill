# 电机驱动 IC 与调速

> 资料采集 · 执行/电源/通信线。对象：电赛小车直流有刷电机的 H 桥驱动 IC 选型、接线、PWM 调速。
> 配套：仓库 `kb/04-电机驱动与执行机构.md`（更全的底盘/测速）、`lib/modules/tb6612fng.yaml`。

## 1. 一张表选驱动 IC

按"持续电流"从小到大排（电赛追踪/循迹小车单电机额定 <1A、堵转 2~3.5A，**按堵转选**）：

| 芯片 | 拓扑/通道 | 电压范围(VM) | 持续/峰值电流 | 逻辑电平(VCC) | 外置MOS | PWM 频率 | 封装 | 备注 |
|---|---|---|---|---|---|---|---|---|
| **TB6612FNG** | 双 H 桥(2 电机) | 2.5~13.5V(实用 ≤10V) | **1.2A / 3.2A** 单通道 | 2.7~5.5V(支持 3.3V) | 否(集成) | 推荐 **15~20kHz**(可达 100kHz) | SSOP24 | 电赛事实标配，1 芯片驱 2 电机，外围只需 2 个旁路电容 |
| **DRV8871** | 单 H 桥(1 电机) | 6.5~45V | **3.6A 峰值** | 逻辑兼容 3~5V | 否 | ≤100kHz | SOIC8 | 单电机高压、内置电流限制(ILIM 电阻) |
| **DRV8701E/P** | 单 H 桥**栅极驱动** | 5.9~45V | 由外置 MOS 决定，**可 >10A** | 3~5V | **是(4×NMOS)** | **≤100kHz** | VQFN24 | 智能车/大功率首选；E 型 PH/EN、P 型双 PWM；需自己画 MOS + 死区 |
| **A4950 / AS4950** | 单全桥(1 电机) | 8~40V | **1.8A 连续 / 3.5A 峰值** | 3~5V | 否 | — | SOIC8 | VREF+ISEN 电流限制；常作 L298N 替代 |
| **AT8236** | 单 H 桥(国产) | 5.5~36V | **4A 连续 / 6A 峰值**(Rds_on≈200mΩ) | 3~5V | 否 | — | ESOP8 | 国产替代 DRV8870，VREF 限流，便宜 |
| **L298N** | 双 H 桥(BJT) | 5~46V | 2A/通道，**压降 2~3V、发热严重** | 5V | 否 | <40kHz | Multiwatt15 | **老旧、效率低、不推荐**，仅入门 |
| **BTS7960 / IBT-2** | 双半桥模块 | 6~27V | **43A** | 3.3/5V | 集成 | <25kHz | 模块 | 超大功率(爬坡/越野/大车) |

> 通道数：要驱 2 个轮电机时，TB6612/L298N/BTS7960 一片搞定；DRV8871/DRV8701/A4950/AT8236 是**单通道**，两个电机要 2 片。

### 选型口诀
- 循迹/追踪小车(GA25-370、JGB37) → **TB6612FNG**（峰值 3.2A 够、几乎不发热、外围最简）。
- 电机偏大 / 要电流闭环 → **AT8236**（国产 4A）或 **DRV8701**（外置 MOS、智能车级可靠）。
- 大功率/爬坡(>5A) → **BTS7960** 模块。
- **坚决避开 L298N**（BJT 压降大、发热、效率低）。

## 2. TB6612FNG 接线（最常用）

```
MCU --PWMA--> PWMA      MCU --AIN1/AIN2--> A 路方向
MCU --PWMB--> PWMB      MCU --BIN1/BIN2--> B 路方向
MCU --IO----> STBY      (置 1 工作, 置 0 全停待机)
VM = 电机电源(电池直供, ≤10V)      VCC = 逻辑 3.3/5V      GND 共地(必须)
AO1/AO2 -> 电机 A      BO1/BO2 -> 电机 B
旁路: VM 处 0.1µF + ≥10µF 电解
```

**真值表（单通道，以 A 为例）**：

| AIN1 | AIN2 | PWMA | 动作 |
|---|---|---|---|
| 1 | 0 | PWM | 正转(调速) |
| 0 | 1 | PWM | 反转(调速) |
| 1 | 1 | × | **刹车**(电机两端短路，能耗制动，停得快) |
| 0 | 0 | × | **滑行**(高阻，惯性滑动) |
| × | × | 0 | 停 |

铁律：**PWMA/PWMB 不可悬空**（悬空会乱转）；STBY 必须拉高才工作。

## 3. DRV8701 接线要点（外置 MOS 方案）

关键脚：`VM` 电机电源(0.1µF+≥10µF 旁路)；`GH1/GH2`、`GL1/GL2` 驱动高/低侧 NMOS 栅极；`SH1/SH2` 接半桥中点(高侧 MOS 源极 + 低侧 MOS 漏极)；`SP/SN/SO` 电流采样放大；`IDRIVE` 单电阻设栅极驱动电流。
- **DRV8701E 用 PH/EN**（方向/使能），**DRV8701P 用 IN1/IN2 双 PWM**。
- PWM **不超过 100kHz**，支持 100% 占空比。VGS 栅压约 9.5V。
- 外置 4×NMOS 必须**自己保证死区**（MCU 高级定时器死区插入或芯片配置），否则上下管直通烧管。

## 4. PWM 调速原理

- **平均电压法**：`V_avg = D · V_motor`（D = 占空比 = t_on/T），转速 ≈ 正比于 V_avg。
- **频率选择**：TB6612 推荐 **15~20kHz**——>20kHz 避开人耳啸叫；过高则开关损耗大、占空比分辨率下降。
  - MSPM0/STM32 算法：`PWM 频率 = 定时器时钟 / (ARR+1)`，如 `80MHz / 4000 = 20kHz`。
- **互补 PWM + 死区**：H 桥同侧上下管不能同时导通（直通短路）。集成芯片(TB6612/AT8236)内部已加死区；**栅极驱动方案(DRV8701)必须靠 MCU 高级定时器(如 MSPM0 TIMA)插死区**。
- **刹车 vs 滑行**：两端同拉高=刹车(能耗制动，急停用)；两端同拉低=滑行(省电巡航用)。

```c
// MSPM0/STM32 通用: 设占空比, duty 0~1
void motor_set(int8_t dir, float duty){       // dir: +1 正, -1 反, 0 停
    if(dir > 0){ AIN1=1; AIN2=0; }
    else if(dir < 0){ AIN1=0; AIN2=1; }
    else { AIN1=1; AIN2=1; }                   // 刹车
    uint32_t ccr = (uint32_t)(duty * ARR);     // ARR=PWM周期计数
    PWM_setDuty(TIMx, CH, ccr);
}
```

## 参考链接

- [TB6612FNG 官方页 - Toshiba](https://toshiba.semicon-storage.com/us/semiconductor/product/motor-driver-ics/brushed-dc-motor-driver-ics/detail.TB6612FNG.html) — 1.2A/3.2A，VM≤13.5V
- [TB6612FNG 数据手册 PDF - SparkFun 镜像](https://cdn.sparkfun.com/datasheets/Robotics/TB6612FNG.pdf) — 真值表/电气参数
- [TB6612FNG 引脚与规格 - components101](https://components101.com/ics/tb6612fng-motor-driver-ic-pinout-datasheet-equivalent-circuit-specs)
- [TB6612 模块官方接线/真值表 - 立创开发板 Wiki](https://wiki.lckfb.com/zh-hans/dmx/module/control/tb6612-motor-drive-module.html)
- [DRV8701 数据手册 PDF - TI](https://www.ti.com/lit/ds/symlink/drv8701.pdf) — 5.9~45V、4×NMOS、PH/EN 或 PWM
- [DRV8701 产品页 - TI](https://www.ti.com/product/DRV8701)
- [DRV8701 the brushed DC motor gate driver with PH/EN and PWM - EDN](https://www.edn.com/drv8701-the-brushed-dc-motor-fate-driver-with-ph-en-and-pwn/)
- [DRV8701 开源 PCB - 立创开源](https://oshwhub.com/LFI329/drv8701)
- [BTS7960(IBT-2) 数据手册 PDF - DFRobot](https://dfimg.dfrobot.com/enshop/image/data/DRI0018/BTS7960.pdf) — 43A、RPWM/LPWM/R_EN/L_EN
- [BTS7960 接线说明 - Ovaga](https://www.ovaga.com/blog/transistor/bts7960-motor-driver-datasheet-and-circuit-diagram)
- [AT8236 4A 单通道有刷驱动 - CSDN](https://blog.csdn.net/YHPsophie/article/details/149743725)
- [AS4950/A4950 H 桥替代 L298N - CSDN](https://blog.csdn.net/u012535488/article/details/115367281)
- [DC Motor Drivers 对比 - DroneBot Workshop](https://dronebotworkshop.com/dc-motor-drivers/)
