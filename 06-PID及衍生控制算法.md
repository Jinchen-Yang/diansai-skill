---
title: "🎯 PID 及衍生控制算法"
tags:
  - 电赛/算法
  - 控制
aliases:
  - "控制算法核心：PID 工程实战与整定（小车/循迹/平衡）"
  - "06 PID 及衍生控制算法"
created: 2026-06-13
---

> [!nav] 导航
> [[00-总览MOC|📖 总览]] · ⬅ [[05-感知传感器选型|05 感知传感器选型]] · [[07-K230视觉与主控通信|07 K230 视觉与主控通信]] ➡

# 🎯 PID 及衍生控制算法

> [!abstract] 本篇速览
> 位置式/增量式/串级/模糊PID、前馈、LQR、滤波、整定方法 + C代码

## PID 原理与离散化

连续 PID：$u(t)=K_p e(t)+K_i\int_0^t e(\tau)d\tau+K_d\dfrac{de(t)}{dt}$，离散采样周期 $T$。本队 MSPM0G3507 建议把控制环放在定时器中断里跑定频（电机速度环 100–200 Hz，平衡内环 200–500 Hz，循迹外环 50–100 Hz），`dt` 必须严格恒定，否则积分/微分系数失真。

> 工程上把 $K_i = K_p\cdot T/T_i$、$K_d = K_p\cdot T_d/T$ 折进系数，代码里直接调 `Kp/Ki/Kd` 三个数即可，不必显式出现 $T$。

### 位置式 PID vs 增量式 PID

| 维度 | 位置式 | 增量式 |
|---|---|---|
| 公式 | $u(k)=K_p e(k)+K_i\sum_{i=0}^{k}e(i)+K_d[e(k)-e(k-1)]$ | $\Delta u(k)=K_p[e(k)-e(k-1)]+K_i e(k)+K_d[e(k)-2e(k-1)+e(k-2)]$ |
| 输出 | 绝对量（直接给 PWM/角度） | 增量（需 `u+=Δu` 累加） |
| 积分饱和 | 需积分限幅+抗饱和 | 增量本身不累计，天然抗饱和 |
| 计算/存储 | 需累加历史 | 仅 3 次采样 |
| 误动作 | 输出错则跳变大 | 误动作影响小，便于手自动无扰切换 |
| 适用 | 直立环/角度环/舵机转角等"位置型"执行器 | 步进电机、阀门、带积分部件对象；小车速度环匀速 |

```c
typedef struct {
    float Kp, Ki, Kd;
    float err, last_err, prev_err;   // e(k), e(k-1), e(k-2)
    float integral, out;
    float out_max, out_min, int_max; // 限幅
} PID_t;

// 位置式：带积分限幅 + 输出限幅
float PID_Pos(PID_t *p, float target, float actual) {
    p->err = target - actual;
    p->integral += p->err;
    if (p->integral >  p->int_max) p->integral =  p->int_max;   // 积分限幅
    if (p->integral < -p->int_max) p->integral = -p->int_max;
    p->out = p->Kp*p->err + p->Ki*p->integral
           + p->Kd*(p->err - p->last_err);
    p->last_err = p->err;
    if (p->out >  p->out_max) p->out =  p->out_max;             // 输出限幅
    if (p->out <  p->out_min) p->out =  p->out_min;
    return p->out;
}

// 增量式：只输出 Δu，外部累加
float PID_Inc(PID_t *p, float target, float actual) {
    p->err = target - actual;
    float dout = p->Kp*(p->err - p->last_err)
               + p->Ki*p->err
               + p->Kd*(p->err - 2*p->last_err + p->prev_err);
    p->prev_err = p->last_err;
    p->last_err = p->err;
    p->out += dout;
    if (p->out > p->out_max) p->out = p->out_max;
    if (p->out < p->out_min) p->out = p->out_min;
    return p->out;
}
```

## 工程改进（必上的"补丁包"）

- **输出/积分限幅**：见上。MSPM0 PWM 用 `DL_TimerA_setCaptureCompareValue`，限幅范围对应占空比上下限。
- **积分分离**：误差大时关掉积分，只 PD，避免启动超调。`if(fabs(err) > eps) ki_factor = 0; else ki_factor = 1;` 乘到积分项上。
- **抗积分饱和 (anti-windup, back-calculation)**：先算未限幅输出 `u_raw`，限幅得 `u_sat`，把差值回馈扣减积分：`integral -= (u_raw - u_sat)/Kc`（$K_c\approx K_p$）。比单纯限幅更平滑。
- **变积分**：误差大→积分系数小，误差小→系数大，是积分分离的连续推广。
- **不完全微分**：对微分项加一阶低通抑制传感器噪声：$D(k)=\alpha D(k-1)+(1-\alpha)K_d[e(k)-e(k-1)]$，$\alpha\in[0.6,0.9]$，循迹/编码器毛刺多时必加。
- **微分先行**：微分只对测量值 $y$ 求导而非误差，避免设定值阶跃时微分冲击：$u=K_p e+K_i\!\int\! e-K_d\dfrac{dy}{dt}$。设定值常变的位置环很有用。
- **死区处理**：$|e|<\delta$ 时输出置 0（或保持），抑制稳态抖动/电机嗡鸣。循迹接近中线、平衡车微抖时用。
- **梯形积分**：$\sum$ 用 $\dfrac{e(k)+e(k-1)}{2}$ 替代矩形，积分更精确。
- **输出斜率限制 (slew-rate)**：限制 `Δout` 每周期最大变化，防电机电流冲击。

## 串级/级联 PID

核心：**外环输出当内环的设定值**；内环频率 ≥ 外环 2–5 倍。

| 应用 | 外环 | 内环 |
|---|---|---|
| 编码电机精确定位 | 位置环(P/PD) | 速度环(PI/增量) |
| 两轮平衡车 | 直立角度环(PD)+速度环(PI) | （角度环输出叠加）→ PWM |
| 循迹小车 | 转向偏差环(PD) | 左右轮速度环(PI) |

平衡车经典叠加（角度环为主，速度/转向修正）：

```c
// 直立环(PD, 位置式)：维持车身竖直
float Balance(float angle, float gyro){     // gyro 已是角速度，直接当D项
    float err = angle - MECH_ZERO;          // 机械中值
    return Kp_b*err + Kd_b*gyro;            // 微分先行：用陀螺仪角速度
}
// 速度环(PI)：调平动速度，注意输出方向与直立相反/低通
float Velocity(int enc_l, int enc_r){
    static float v_lp=0, vi=0;
    float v = (enc_l+enc_r) - target_speed;
    v_lp = 0.7f*v_lp + 0.3f*v;              // 一阶低通去毛刺
    vi += v_lp; vi = LIMIT(vi, -INT_MAX, INT_MAX);
    return Kp_v*v_lp + Ki_v*vi;
}
// 转向环(PD)：用 Z 轴陀螺仪
float Turn(float yaw_rate, float set){ return Kp_t*set + Kd_t*yaw_rate; }
// 合成：注意符号，三环叠加后限幅给左右轮
pwm_l = Balance + Velocity - Turn;
pwm_r = Balance + Velocity + Turn;
```

## 循迹/巡线控制

**偏差计算（八路灰度加权位置式）**：给每个传感器一个位置权重（如 `-7,-5,-3,-1,1,3,5,7`），按命中（或模拟量）加权求质心：
$$pos=\dfrac{\sum_i w_i\cdot s_i}{\sum_i s_i}$$
全部丢线时保持上一次偏差符号（防冲出）。归一化到 $[-1,1]$ 便于复用 PID。模拟量灰度（如 AD 八路）比数字开关量更平滑，配合不完全微分效果最好。

**转向 PID（位置式 PD）**：`turn = Kp*pos + Kd*(pos - last_pos)`；积分一般不要或很小，避免弯道积累。

**速度自适应（弯道减速）**：按偏差/曲率降速，直道提速：
```c
float v_target = V_MAX - K_slow * fabs(pos);   // 偏差越大越慢
if (v_target < V_MIN) v_target = V_MIN;
pwm_l = SpeedPID_L(v_target - turn);
pwm_r = SpeedPID_R(v_target + turn);
```

## 前馈控制（feedforward）

前馈+PID 复合：$u=u_{ff}+u_{pid}$。电机速度环前馈用稳态模型 $u_{ff}=k_f\cdot v_{ref}+b$（$k_f$、$b$ 由"PWM-转速"标定曲线拟合），让响应"先到位"，PID 只补残差，跟随性大幅提升。位置/速度前馈在伺服里使前馈与闭环传函之积趋近 1，实现输出复现输入。工程关键是**前馈系数标定**+**前馈加入后 PID 重新整定**。

## 模糊 PID（fuzzy 在线整定 ΔKp ΔKi ΔKd）

输入 $e$、$ec$（误差变化率），输出 $\Delta K_p,\Delta K_i,\Delta K_d$。四步：**模糊化→隶属函数→规则表→解模糊**。
- **论域/模糊子集**：$\{NB,NM,NS,ZO,PS,PM,PB\}$，论域常取 $[-3,3]$ 或 $[-6,6]$，用量化因子把实际 $e$ 映射进论域。
- **隶属函数**：三角形（trimf）最省算力，单片机首选；中间密两端疏。
- **规则表**：`if e is NB and ec is NB then ΔKp is PB`。经验：$|e|$ 大→增 $K_p$、去 $K_i$；$|e|$ 小→增 $K_i$ 稳态。
- **解模糊**：重心法 $u^*=\dfrac{\sum \mu_i u_i}{\sum \mu_i}$。
- **在线整定**：$K_p=K_{p0}+\Delta K_p$（$K_i,K_d$ 同理）。
单片机上可把 7×7 规则表预存数组，查表+线性插值，避免实时浮点推理。资源紧张时优先用普通串级 PID，模糊 PID 作为加分项。

## 自适应/Bang-Bang/LQR

- **Bang-Bang**：误差大时直接满输出（±PWM_MAX），接近目标切回 PID，加快大偏差响应（启动/急转）。
- **LQR/状态反馈**（平衡/倒立摆）：状态 $x=[\theta,\dot\theta,x,\dot x]^T$，反馈律 $u=-Kx$，$K$ 由代价 $J=\int(x^TQx+u^TRu)dt$ 最小化解 Riccati 得到。$Q$ 对角增大→该状态收敛更快但耗控制量，$R$ 增大→更省力更慢。可在 MATLAB `lqr(A,B,Q,R)` 离线求 $K$，把四个增益直接写进单片机，本质就是"四状态加权 PD"。

## 配套滤波

| 滤波 | 公式/要点 | 用途 |
|---|---|---|
| 一阶低通(RC) | $y_k=\alpha y_{k-1}+(1-\alpha)x_k$ | 速度/灰度去高频噪声 |
| 滑动平均 | N 点窗口求均值 | 平滑、相位滞后 |
| 限幅滤波 | 单次跳变超阈值则丢弃 | 抗脉冲尖峰 |
| 中值滤波 | 取窗口中位数 | 抗椒盐/偶发野值 |
| 互补滤波 | $\theta=\beta(\theta+\omega\,dt)+(1-\beta)\theta_{acc}$，$\beta\approx0.98$ | MPU6050 角度融合，算力小 |
| 卡尔曼 | 预测-更新，最优估计 | 角度融合更平滑，算力大 |

平衡车角度首选**互补滤波**（够用、省算力）；K230 回传的视觉偏差建议**一阶低通+限幅**再喂 PID。

## 整定方法（落地流程）

**试凑法（推荐先用）**：
1. 仅 P：从小加大 $K_p$ 到响应快但临界振荡，回退到约 60%。
2. 加 D：抑制超调/振荡，$K_d$ 太大引入噪声放大。
3. 加 I：消除稳态误差，从小加，过大则超调回摆。口诀：先 P 后 D 再 I。

**临界比例度法 / Ziegler-Nichols**：纯 P 增益加到等幅振荡，记临界增益 $K_u$、临界周期 $T_u$：

| 控制器 | $K_p$ | $T_i$ | $T_d$ |
|---|---|---|---|
| P | $0.5K_u$ | — | — |
| PI | $0.45K_u$ | $T_u/1.2$ | — |
| PID | $0.6K_u$ | $0.5T_u$ | $0.125T_u$ |

换算回代码系数：$K_i=K_p\cdot T/T_i$，$K_d=K_p\cdot T_d/T$。Z-N 结果偏激进（超调约 25%），小车上一般再把 $K_p$ 打 7–8 折更稳。**经验范围**：速度环 PI 先调、位置/角度环 PD 先调；串级先整内环、再整外环。

> 联调建议：MSPM0 用串口/CCS Graph 或上位机实时画 `target/actual` 曲线，K230 经 UART 把视觉偏差发给主控，主控只做滤波+PID，分工清晰、便于分别整定。


---

## 🔑 关键要点（速记）

- 位置式PID输出绝对量、适合直立环/角度环/舵机；增量式只输出Δu、天然抗饱和、适合速度环匀速控制——两者C模板已给，按执行器类型选型。
- 串级PID铁律：外环输出=内环设定值，内环频率取外环2–5倍；平衡车=直立PD(微分用陀螺仪角速度/微分先行)+速度PI+转向PD三环叠加后限幅给左右轮。
- 必上工程补丁：积分限幅+输出限幅(地基)、积分分离(防启动超调)、back-calculation抗饱和(integral-=（u_raw-u_sat)/Kc)、不完全微分(α取0.6–0.9抑噪)、微分先行、死区(防抖)、梯形积分。
- 循迹偏差用八路灰度加权位置式 pos=Σ(wi·si)/Σsi 并归一化到[-1,1]，转向用PD(少用或不用I)，弯道按|pos|减速：v=Vmax−Kslow·|pos|；全丢线保持上次偏差符号防冲出。
- 前馈+PID复合 u=u_ff+u_pid：速度环前馈用标定的PWM-转速曲线 u_ff=kf·v_ref+b，让响应先到位、PID补残差，跟随性显著提升；加前馈后必须重新整定PID。
- 模糊PID四步(模糊化→三角隶属函数→7×7规则表→重心法解模糊)在线整出ΔKp/ΔKi/Δkd，单片机用预存查表+插值；资源紧时优先普通串级PID，模糊作加分项。
- 平衡/倒立摆可用LQR：状态[θ,θ̇,x,ẋ]，u=−Kx，MATLAB lqr(A,B,Q,R)离线求K写进单片机；Q大状态收敛快但费控制量、R大更省力更慢，本质是四状态加权PD。
- 滤波选型：平衡车角度首选互补滤波(θ=β(θ+ω·dt)+(1−β)θ_acc，β≈0.98，省算力)；速度/视觉偏差用一阶低通+限幅；野值多加中值/限幅滤波。
- 整定流程：试凑法先P(加到临界振荡回退60%)→后D(抑超调)→再I(消静差)；Z-N临界比例度法测Ku/Tu后 PID取Kp=0.6Ku、Ti=0.5Tu、Td=0.125Tu，小车上Kp再打7–8折更稳。
- 联调分工：K230经UART把视觉偏差发给MSPM0G3507，主控只做滤波+PID并定频中断跑环(速度100–200Hz/平衡内环200–500Hz)，用串口上位机实时画target/actual曲线分别整定各环。


---

## 🔗 相关笔记

- [[05-感知传感器选型|05 感知传感器选型]] — 灰度/电磁循迹、IMU 姿态解算、TOF 测距、里程计
- [[04-电机驱动与执行机构|04 电机驱动与执行机构]] — 编码器电机、TB6612/DRV8701、PWM调速、麦轮运动学、测速
- [[08-软件架构与调试工程化|08 软件架构与调试工程化]] — 分层架构、时间片调度器、FSM、VOFA+/JustFloat 调参
- [[02-历年小车与控制类赛题|02 历年小车与控制类赛题]] — 2011→2024 逐题解析：送药小车、目标追踪、倒立摆、循迹车，命题规律与趋势


---

## 📚 参考资料 / 链接

- [位置式PID与增量式PID区别浅析（含公式与C代码）](https://blog.csdn.net/as480133937/article/details/89508034) — 经多源核对的位置式/增量式公式与C代码主源
- [增量式PID的两种计算方式及C代码](https://blog.csdn.net/a1247812862/article/details/89140556) — 增量式系数 A/B/C 展开
- [深入浅出PID控制算法（三）增量式与位置式C语言实现与电机控制](https://blog.csdn.net/kilotwo/article/details/79952530) — 电机控制经验与代码
- [经典位置式与增量式PID原理 - 知乎](https://zhuanlan.zhihu.com/p/586532545) — 原理交叉验证
- [抗积分饱和-积分分离-增量型-梯形积分-PID控制器代码 - 知乎](https://zhuanlan.zhihu.com/p/137684786) — 四类工程改进代码（403需手动访问）
- [抗积分饱和 PID——Anti-Windup - 知乎](https://zhuanlan.zhihu.com/p/436897732) — back-calculation 抗饱和原理
- [PID控制常见手段：抗积分饱和+带死区+不完全微分+微分先行](https://blog.csdn.net/u012415132/article/details/145184518) — 不完全微分/微分先行/死区公式
- [PID的常见5种积分处理方式](https://blog.csdn.net/weixin_44035751/article/details/107928330) — 积分分离/变积分/梯形积分
- [平衡小车制作（五）（六）（七）：位置式PID、直立环速度环、串级调参](https://blog.csdn.net/weixin_44270218/article/details/113786386) — 平衡车串级PID与整定完整教程
- [两轮机器人串级PID详解 - 知乎](https://zhuanlan.zhihu.com/p/688498130) — 角度环+角速度环+速度环结构
- [给新手的两轮自平衡小车开发实战指南](https://c.miaowlabs.com/E08.html) — 增量式系数A/B/C、采样周期选取、串级结构
- [小车快速循迹 串级PID算法 干货](https://blog.csdn.net/h18637233775/article/details/139881471) — 循迹串级PID与偏差加权
- [STM32循迹小车（三）灰度传感器循迹](https://blog.csdn.net/weixin_49821504/article/details/130444390) — 八路灰度加权位置式偏差
- [基于STM32和PID算法实现小车循迹](https://blog.csdn.net/2301_79565212/article/details/135003430) — 转向PID与速度自适应
- [模糊控制PID详解](https://blog.csdn.net/weixin_41270987/article/details/134075049) — 模糊化/隶属/规则/解模糊四步
- [模糊PID中论域的选择和模糊规则的选取](https://blog.csdn.net/u014535666/article/details/100633972) — 论域与量化因子选择
- [PID控制器开发笔记之十二：模糊PID控制器的实现 - 博客园](https://www.cnblogs.com/foxclever/p/9940253.html) — 模糊PID查表C实现
- [PID控制器开发笔记之九：基于前馈补偿的PID控制器](https://www.cnblogs.com/foxclever/p/9311124.html) — 前馈+PID复合 U=Up+Uf
- [现代PMSM FOC控制：从PID、系统辨识到LQR/MPC - 博客园](https://www.cnblogs.com/guohaomeng/p/19088492) — LQR/状态反馈系统化资料
- [Inverted Pendulum: State-Space Methods (UMich CTMS)](https://ctms.engin.umich.edu/CTMS/index.php?example=InvertedPendulum&section=ControlStateSpace) — LQR Q/R 与状态反馈权威推导
- [MPU6050姿态解算一阶互补滤波（原理到代码）](https://blog.csdn.net/tjcwt2011/article/details/138476215) — 互补滤波β系数与代码
- [MPU6050滤波、姿态融合（一阶互补、卡尔曼）- 博客园](https://www.cnblogs.com/qsyll0916/p/8030379.html) — 互补/卡尔曼对比
- [PID 参数不会调？试试 Ziegler-Nichols 实验法 - 知乎](https://zhuanlan.zhihu.com/p/716747582) — Z-N 临界比例度整定表
- [Ziegler-Nichols对PID的调参方法 - CSDN](https://blog.csdn.net/m0_46499664/article/details/136458581) — Ku/Tu 与 0.6/0.5/0.125 系数核对
- [PID控制器参数整定：试凑法实践指南](https://blog.csdn.net/fysf911/article/details/123240010) — 试凑法步骤先P后D再I


> [!nav] [[00-总览MOC|📖 总览]] · ⬅ [[05-感知传感器选型|05 感知传感器选型]] · [[07-K230视觉与主控通信|07 K230 视觉与主控通信]] ➡