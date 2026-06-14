/* 可移植 PID（与芯片无关，可主机编译/单测）—— firmware-scaffold 中间件层 */
#ifndef PID_H
#define PID_H

typedef struct {
    float kp, ki, kd;
    float integ, prev_err;
    float out_min, out_max, integ_max;   /* 抗积分饱和：积分限幅 + 输出限幅 */
} pid_t;

void  pid_init(pid_t *p, float kp, float ki, float kd,
               float out_min, float out_max, float integ_max);
void  pid_reset(pid_t *p);
float pid_update(pid_t *p, float target, float meas);   /* 位置式，返回限幅后输出 */

#endif /* PID_H */
