/* 自动生成 — 勿手改。源: contracts/protocol.yaml  生成器: tools/gen_protocol.py */
/* K230 <-> 主控 UART 帧协议 (C / 主控端) */
#ifndef PROTOCOL_H
#define PROTOCOL_H
#include <stdint.h>

#define PROTOCOL_SIG "bd8385352fff6e42"   /* 两端一致性签名，须与 protocol.py 相同 */
#define PROTO_HEADER0 0xaa
#define PROTO_HEADER1 0x55
#define PROTO_TAIL    0x0d
#define PROTO_MAX_DATA 32
/* 链路: 115200 8N1, 3.3V TTL */

/* 功能码 */
typedef enum {
    FUNC_BLOB_XY = 0x01,  /* 色块/光点中心坐标 */
    FUNC_LINE_ERROR = 0x02,  /* 巡线中线偏差（喂给 PID） */
    FUNC_TARGET_CLASS = 0x03,  /* 目标类别 + 置信度 */
    FUNC_HANDSHAKE = 0x04,  /* 上电握手 / ACK */
} proto_func_t;

/* 各帧负载结构 (packed, 小端) */
typedef struct __attribute__((packed)) {
    int16_t cx;
    int16_t cy;
} frame_blob_xy_t;
typedef struct __attribute__((packed)) {
    int16_t error;
} frame_line_error_t;
typedef struct __attribute__((packed)) {
    uint8_t class_id;
    uint8_t confidence;
} frame_target_class_t;
typedef struct __attribute__((packed)) {
    uint8_t token;
} frame_handshake_t;

/* 接收帧 */
typedef struct {
    uint8_t func;
    uint8_t len;
    uint8_t data[PROTO_MAX_DATA];
    uint8_t ready;   /* 1=收到完整有效帧 */
} proto_frame_t;

/* sum8 校验 */
static inline uint8_t proto_checksum(uint8_t len, uint8_t func, const uint8_t *data) {
    uint8_t s = (uint8_t)(len + func);
    for (uint8_t i = 0; i < len - 1; i++) s = (uint8_t)(s + data[i]);
    return s;
}

/* 组帧: out 须 >= len+5; 返回总字节数。data 不含 func; len = 1(func)+payload */
static inline uint8_t proto_build(uint8_t func, const uint8_t *payload, uint8_t plen, uint8_t *out) {
    uint8_t len = (uint8_t)(plen + 1);
    uint8_t s = (uint8_t)(len + func), i = 0;
    out[0]=PROTO_HEADER0; out[1]=PROTO_HEADER1; out[2]=len; out[3]=func;
    for (i = 0; i < plen; i++) { out[4+i] = payload[i]; s = (uint8_t)(s + payload[i]); }
    out[4+plen] = s; out[5+plen] = PROTO_TAIL;
    return (uint8_t)(plen + 6);
}

/* 逐字节喂入的解析状态机 (复用 KB 07 重同步状态机)。收到完整帧时 fr->ready=1。*/
static inline void proto_parse_byte(uint8_t c, proto_frame_t *fr) {
    static enum { S_H1, S_H2, S_LEN, S_BODY, S_CHK, S_TAIL } st = S_H1;
    static uint8_t len=0, idx=0, sum=0, buf[PROTO_MAX_DATA];
    switch (st) {
    case S_H1: st = (c==PROTO_HEADER0)? S_H2 : S_H1; break;
    case S_H2: st = (c==PROTO_HEADER1)? S_LEN : ((c==PROTO_HEADER0)? S_H2 : S_H1); break;
    case S_LEN:
        len = c; sum = c; idx = 0;
        st = (len>0 && len<=PROTO_MAX_DATA)? S_BODY : S_H1;
        break;
    case S_BODY:
        buf[idx++] = c; sum = (uint8_t)(sum + c);
        if (idx >= len) st = S_CHK;
        break;
    case S_CHK: st = (c==sum)? S_TAIL : S_H1; break;
    case S_TAIL:
        if (c==PROTO_TAIL) { fr->func=buf[0]; fr->len=len; 
            for (uint8_t i=0;i<len;i++) fr->data[i]=buf[i]; fr->ready=1; }
        st = S_H1;
        break;
    }
}

#endif /* PROTOCOL_H */
