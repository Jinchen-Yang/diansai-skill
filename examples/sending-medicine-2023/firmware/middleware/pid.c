#include "pid.h"

static float clampf(float v, float lo, float hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}

void pid_init(pid_t *p, float kp, float ki, float kd,
              float out_min, float out_max, float integ_max) {
    p->kp = kp; p->ki = ki; p->kd = kd;
    p->out_min = out_min; p->out_max = out_max; p->integ_max = integ_max;
    p->integ = 0.0f; p->prev_err = 0.0f;
}

void pid_reset(pid_t *p) { p->integ = 0.0f; p->prev_err = 0.0f; }

float pid_update(pid_t *p, float target, float meas) {
    float err = target - meas;
    p->integ = clampf(p->integ + err, -p->integ_max, p->integ_max);  /* 积分限幅 */
    float d = err - p->prev_err;
    float out = p->kp * err + p->ki * p->integ + p->kd * d;
    p->prev_err = err;
    return clampf(out, p->out_min, p->out_max);                      /* 输出限幅 */
}
