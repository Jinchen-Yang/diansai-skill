/* VOFA+ JustFloat 上位机回传（KB08）：小端 float 数组 + 4 字节帧尾 */
#ifndef VOFA_H
#define VOFA_H

void vofa_send(const float *ch, int n);   /* n 个通道；如 {target,actual,pwm} 整定 PID */

#endif
