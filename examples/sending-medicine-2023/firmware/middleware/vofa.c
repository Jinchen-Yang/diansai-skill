#include "vofa.h"

/* TODO: 接调试 UART(pinmap: log_tx)。此处声明占位，便于分层与单测。 */
static void log_uart_write(const unsigned char *buf, int len) {
    (void)buf; (void)len;
}

void vofa_send(const float *ch, int n) {
    static const unsigned char tail[4] = { 0x00, 0x00, 0x80, 0x7F };  /* JustFloat 帧尾 */
    log_uart_write((const unsigned char *)ch, n * 4);
    log_uart_write(tail, 4);
}
