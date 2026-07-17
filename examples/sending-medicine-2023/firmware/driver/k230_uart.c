#include "k230_uart.h"
#include <string.h>

static proto_frame_t s_fr;

void k230_uart_init(void) {
    memset(&s_fr, 0, sizeof(s_fr));
    /* TODO(SysConfig/DriverLib): 配 UART1 (pinmap: k230_tx/k230_rx) 115200 8N1, 开 RX 中断 */
}

/* 在 UART1 RX 中断服务里调：把字节喂给协议状态机（重同步在 protocol.h 内） */
void k230_on_rx_byte(uint8_t c) {
    proto_parse_byte(c, &s_fr);
}

/* 主循环/任务里轮询：取走一帧 */
int k230_get_frame(proto_frame_t *out) {
    if (s_fr.ready) { *out = s_fr; s_fr.ready = 0; return 1; }
    return 0;
}
