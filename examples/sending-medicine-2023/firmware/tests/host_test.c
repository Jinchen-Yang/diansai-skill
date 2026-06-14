/* 主机自测：验中间件(PID/调度器) + 协议 C 端往返。
 * 编译: cc -I<middleware> -I<contracts> host_test.c pid.c scheduler.c -o host_test
 * 运行: ./host_test        (跑断言)
 *       ./host_test emit    (只打印两帧 hex, 供跨语言比对)
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include "pid.h"
#include "scheduler.h"
#include "protocol.h"

static int g_count = 0;
static void counter_task(void) { g_count++; }

static int decode_i16(const uint8_t *d) { return (int16_t)(d[0] | (d[1] << 8)); }

static void print_hex(const uint8_t *b, int n) {
    for (int i = 0; i < n; i++) printf("%02X", b[i]);
    printf("\n");
}

int main(int argc, char **argv) {
    int emit = (argc > 1 && strcmp(argv[1], "emit") == 0);

    /* 组帧: line_error(-123) */
    int16_t e = -123;
    uint8_t pl[2] = { (uint8_t)(e & 0xFF), (uint8_t)((e >> 8) & 0xFF) };
    uint8_t out[32];
    uint8_t n = proto_build(FUNC_LINE_ERROR, pl, 2, out);

    /* 组帧: blob_xy(100,200) */
    int16_t cx = 100, cy = 200;
    uint8_t pl2[4] = { (uint8_t)(cx & 0xFF), (uint8_t)((cx >> 8) & 0xFF),
                       (uint8_t)(cy & 0xFF), (uint8_t)((cy >> 8) & 0xFF) };
    uint8_t out2[32];
    uint8_t n2 = proto_build(FUNC_BLOB_XY, pl2, 4, out2);

    if (emit) { print_hex(out, n); print_hex(out2, n2); return 0; }

    /* 协议往返: line_error */
    proto_frame_t fr; memset(&fr, 0, sizeof(fr));
    for (uint8_t i = 0; i < n; i++) proto_parse_byte(out[i], &fr);
    assert(fr.ready == 1 && fr.func == FUNC_LINE_ERROR);
    assert(decode_i16(&fr.data[1]) == -123);
    printf("protocol line_error roundtrip OK (error=%d)\n", decode_i16(&fr.data[1]));

    /* 协议往返: blob_xy */
    proto_frame_t fr2; memset(&fr2, 0, sizeof(fr2));
    for (uint8_t i = 0; i < n2; i++) proto_parse_byte(out2[i], &fr2);
    assert(fr2.ready && fr2.func == FUNC_BLOB_XY);
    assert(decode_i16(&fr2.data[1]) == 100 && decode_i16(&fr2.data[3]) == 200);
    printf("protocol blob_xy roundtrip OK (cx=%d cy=%d)\n",
           decode_i16(&fr2.data[1]), decode_i16(&fr2.data[3]));

    /* 校验和错误应被拒（重同步） */
    uint8_t bad[32]; memcpy(bad, out, n); bad[n - 2] ^= 0xFF;   /* 破坏 CHK */
    proto_frame_t fr3; memset(&fr3, 0, sizeof(fr3));
    for (uint8_t i = 0; i < n; i++) proto_parse_byte(bad[i], &fr3);
    assert(fr3.ready == 0);
    printf("protocol bad-checksum rejected OK\n");

    /* PID 健全性 */
    pid_t pid; pid_init(&pid, 1.0f, 0.1f, 0.05f, -100, 100, 100);
    float u1 = pid_update(&pid, 10.0f, 0.0f);   /* 大正误差 -> 正输出 */
    assert(u1 > 0);
    float u2 = pid_update(&pid, 10.0f, 10.0f);  /* 到目标 -> 输出回落 */
    assert(u2 <= u1);
    printf("pid sanity OK (u1=%.2f u2=%.2f)\n", u1, u2);

    /* 调度器: period=5, 20 ticks -> 跑 4 次 */
    task_t tasks[1] = { { counter_task, 5, 0, 0 } };
    for (int t = 0; t < 20; t++) { sched_tick(tasks, 1); sched_run(tasks, 1); }
    printf("scheduler runs=%d (expect 4)\n", g_count);
    assert(g_count == 4);

    printf("ALL HOST TESTS PASSED\n");
    return 0;
}
