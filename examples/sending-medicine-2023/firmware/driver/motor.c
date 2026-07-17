#include "motor.h"

void motor_init(void) {
    /* TODO(SysConfig/DriverLib):
       TIMA0 出 motorL_pwm/motorR_pwm(PA0/PA1) PWM；
       GPIO 方向 AIN1/2 BIN1/2(PA4..PA7)；STBY(PB13) 拉高使能。 */
}

void motor_set(int ch, int duty) {
    int dir = duty >= 0;
    int mag = duty >= 0 ? duty : -duty;
    if (mag > 1000) mag = 1000;
    (void)ch; (void)dir; (void)mag;
    /* TODO: 据 ch 设对应 INx 方向（dir），据 mag 设对应通道 PWM 占空 */
}
