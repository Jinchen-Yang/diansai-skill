/* K230 串口驱动：收帧用 contracts/protocol.h（勿改协议，改 protocol.yaml 重生成）*/
#ifndef K230_UART_H
#define K230_UART_H
#include "protocol.h"

void k230_uart_init(void);                 /* SysConfig: UART1 115200 8N1 + RX 中断 */
void k230_on_rx_byte(uint8_t c);           /* 在 UART RX 中断里逐字节调 */
int  k230_get_frame(proto_frame_t *out);   /* 主循环轮询；有新帧返回 1 */

#endif
