/* 裸机时间片调度（复用 KB08 模板，可主机编译/单测）—— firmware-scaffold 中间件层 */
#ifndef SCHEDULER_H
#define SCHEDULER_H
#include <stdint.h>

typedef struct {
    void    (*task)(void);
    uint16_t period_ms;
    uint16_t timer;
    uint8_t  run;
} task_t;

void sched_tick(task_t *tasks, uint8_t n);   /* 放 1ms 定时器中断：到点置 run */
void sched_run (task_t *tasks, uint8_t n);   /* 放 main while(1)：跑就绪任务 */

#endif /* SCHEDULER_H */
