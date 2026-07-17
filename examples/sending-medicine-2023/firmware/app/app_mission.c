/* 送药流程状态机（复用 KB08 FSM 模板）：事件来自视觉/灰度/里程，动作调 driver。
 * 视觉与 FSM 解耦：K230 只产生结果，FSM 决定何时采信。 */
#include <stdint.h>
#include "protocol.h"
#include "k230_uart.h"
#include "motor.h"

typedef enum {
    ST_IDLE, ST_START, ST_TRACK, ST_DETECT, ST_ACTION, ST_RETURN, ST_STOP
} mission_state_e;

static mission_state_e g_state = ST_IDLE;
static int16_t g_line_err = 0;     /* 最新巡线偏差（来自 K230 或本地灰度） */

static void poll_vision(void) {
    proto_frame_t fr;
    if (k230_get_frame(&fr)) {
        if (fr.func == FUNC_LINE_ERROR) {
            g_line_err = (int16_t)(fr.data[1] | (fr.data[2] << 8));
        }
        /* else if (fr.func == FUNC_TARGET_CLASS) { 门牌识别事件 ... } */
    }
}

void app_mission(void) {           /* 放 task，5~10ms 调一次 */
    poll_vision();
    switch (g_state) {
    case ST_IDLE:   /* if (key_start()) g_state = ST_START; */            break;
    case ST_START:  motor_set(0, 300); motor_set(1, 300); g_state = ST_TRACK; break;
    case ST_TRACK:  /* 外环 PID(g_line_err)->差速；到指定房 -> ST_DETECT */ break;
    case ST_DETECT: /* K230 连续 N 帧确认门牌 -> ST_ACTION */              break;
    case ST_ACTION: /* 送达动作（停车/提示） */ g_state = ST_TRACK;        break;
    case ST_RETURN: /* 返航巡线；到药房 -> ST_STOP */                      break;
    case ST_STOP:   motor_set(0, 0); motor_set(1, 0);                     break;
    }
}
