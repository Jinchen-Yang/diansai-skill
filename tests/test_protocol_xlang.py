#!/usr/bin/env python3
"""跨语言协议一致性测试（最关键的契约验证）：
Python 端(contracts/protocol.py) 与 C 端(contracts/protocol.h, 经 host_test emit)
对同样的帧逐字节比对；再用 Python Parser 解 C 产出的字节，验证解码正确。
两端同源于 contracts/protocol.yaml，本测试保证生成器没让两端漂移。

退出码: 0=PASS, 1=FAIL。
"""
import os, sys, subprocess, tempfile, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW = os.path.join(ROOT, 'examples', 'sending-medicine-2023', 'firmware')


def load_protocol_py():
    path = os.path.join(ROOT, 'contracts', 'protocol.py')
    spec = importlib.util.spec_from_file_location('protocol', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_c_emitter():
    """编译 host_test，返回可执行路径。"""
    out = os.path.join(tempfile.gettempdir(), 'host_test_xlang')
    cmd = ['cc', '-std=c11', '-O2',
           '-I', os.path.join(FW, 'middleware'), '-I', os.path.join(ROOT, 'contracts'),
           os.path.join(FW, 'tests', 'host_test.c'),
           os.path.join(FW, 'middleware', 'pid.c'),
           os.path.join(FW, 'middleware', 'scheduler.c'),
           '-o', out]
    subprocess.run(cmd, check=True)
    return out


def main():
    proto = load_protocol_py()

    # Python 端造帧（须与 host_test.c emit 的两帧一致）
    py_frames = [
        proto.line_error(-123).hex().upper(),
        proto.blob_xy(100, 200).hex().upper(),
    ]

    # C 端 emit
    try:
        exe = build_c_emitter()
    except subprocess.CalledProcessError as e:
        print(f"✗ 无法编译 C 端: {e}"); return 1
    c_out = subprocess.run([exe, 'emit'], capture_output=True, text=True, check=True)
    c_frames = [ln.strip() for ln in c_out.stdout.splitlines() if ln.strip()]

    print(f"签名: protocol.py SIG={proto.PROTOCOL_SIG}")
    ok = True
    names = ['line_error(-123)', 'blob_xy(100,200)']
    for i, name in enumerate(names):
        py, c = py_frames[i], c_frames[i]
        same = (py == c)
        ok &= same
        print(f"  {name}: PY={py}  C={c}  {'✓' if same else '✗ 不一致'}")

    # 反向：Python Parser 解 C 产出的字节
    parser = proto.Parser()
    decoded = None
    for b in bytes.fromhex(c_frames[0]):
        r = parser.feed(b)
        if r:
            decoded = r
    if decoded and decoded[0] == proto.FUNC_LINE_ERROR:
        import struct
        err = struct.unpack('<h', decoded[1])[0]
        print(f"  Python Parser 解 C 的 line_error 帧 -> error={err} {'✓' if err == -123 else '✗'}")
        ok &= (err == -123)
    else:
        print("  ✗ Python Parser 未能解出 C 的帧"); ok = False

    print("✓ 跨语言一致性 PASS" if ok else "✗ FAIL")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
