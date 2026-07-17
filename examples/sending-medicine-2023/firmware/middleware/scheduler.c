#include "scheduler.h"

void sched_tick(task_t *t, uint8_t n) {
    for (uint8_t i = 0; i < n; i++) {
        if (t[i].timer == 0) { t[i].run = 1; t[i].timer = t[i].period_ms; }
        else                 { t[i].timer--; }
    }
}

void sched_run(task_t *t, uint8_t n) {
    for (uint8_t i = 0; i < n; i++) {
        if (t[i].run) { t[i].run = 0; if (t[i].task) t[i].task(); }
    }
}
