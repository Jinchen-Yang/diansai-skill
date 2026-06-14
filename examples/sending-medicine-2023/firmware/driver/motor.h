/* 电机驱动（TB6612）：引脚见 contracts/pinmap.yaml 的 motorL_/motorR_/motor_stby 各信号 */
#ifndef MOTOR_H
#define MOTOR_H

void motor_init(void);
void motor_set(int ch, int duty);   /* ch:0=左 1=右；duty:-1000..1000，符号=方向 */

#endif
