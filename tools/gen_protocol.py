#!/usr/bin/env python3
"""contracts/protocol.yaml -> protocol.h (C, 给主控/控制 lane) + protocol.py (MicroPython, 给 K230/算法 lane)

单一来源生成两端，杜绝控制 / 算法漂移。内置两端一致性自检：
两个生成文件都嵌入同一个 PROTOCOL_SIG（帧定义的规范化哈希），生成后回读比对，三者一致才算通过。

用法:
    python tools/gen_protocol.py [contracts/protocol.yaml]
"""
import sys, os, json, hashlib, re
import yaml

C_TYPE     = {'int8':'int8_t','uint8':'uint8_t','int16':'int16_t','uint16':'uint16_t','int32':'int32_t','uint32':'uint32_t'}
TYPE_SIZE  = {'int8':1,'uint8':1,'int16':2,'uint16':2,'int32':4,'uint32':4}
PY_STRUCT  = {'int8':'b','uint8':'B','int16':'h','uint16':'H','int32':'i','uint32':'I'}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def signature(spec):
    """帧定义的规范化签名——两端一致性的唯一判据。"""
    fr = spec['framing']
    canon = {
        'header': fr['header'], 'tail': fr['tail'],
        'checksum': fr['checksum'], 'max_data': fr['max_data'],
        'frames': [{'func': f['func'], 'name': f['name'],
                    'fields': [(x['name'], x['type']) for x in f.get('fields', [])]}
                   for f in spec['frames']],
    }
    blob = json.dumps(canon, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()[:16]


def validate(spec):
    errs = []
    fr = spec['framing']
    if len(fr['header']) != 2:
        errs.append("framing.header 必须是 2 字节双帧头")
    if fr['checksum'] != 'sum8':
        errs.append(f"暂只支持 checksum: sum8（收到 {fr['checksum']}）")
    seen_func, seen_name = set(), set()
    for f in spec['frames']:
        if f['func'] in seen_func:
            errs.append(f"重复 func: {f['func']:#04x}")
        if f['name'] in seen_name:
            errs.append(f"重复 name: {f['name']}")
        seen_func.add(f['func']); seen_name.add(f['name'])
        sz = sum(TYPE_SIZE[x['type']] for x in f.get('fields', []))
        if sz > fr['max_data']:
            errs.append(f"帧 {f['name']} 负载 {sz}B 超过 max_data={fr['max_data']}")
        for x in f.get('fields', []):
            if x['type'] not in TYPE_SIZE:
                errs.append(f"帧 {f['name']} 字段 {x['name']} 未知类型 {x['type']}")
    return errs


def gen_h(spec, sig):
    fr = spec['framing']; h0, h1 = fr['header']
    L = ['/* 自动生成 — 勿手改。源: contracts/protocol.yaml  生成器: tools/gen_protocol.py */',
         '/* K230 <-> 主控 UART 帧协议 (C / 主控端) */',
         '#ifndef PROTOCOL_H', '#define PROTOCOL_H', '#include <stdint.h>', '',
         f'#define PROTOCOL_SIG "{sig}"   /* 两端一致性签名，须与 protocol.py 相同 */',
         f'#define PROTO_HEADER0 {h0:#04x}',
         f'#define PROTO_HEADER1 {h1:#04x}',
         f'#define PROTO_TAIL    {fr["tail"]:#04x}',
         f'#define PROTO_MAX_DATA {fr["max_data"]}',
         f'/* 链路: {spec["link"]["baud"]} {spec["link"]["data_bits"]}'
         f'{spec["link"]["parity"][0].upper()}{spec["link"]["stop_bits"]}, {spec["link"]["level"]} */', '',
         '/* 功能码 */', 'typedef enum {']
    for f in spec['frames']:
        L.append(f'    FUNC_{f["name"].upper()} = {f["func"]:#04x},  /* {f.get("desc","")} */')
    L += ['} proto_func_t;', '', '/* 各帧负载结构 (packed, 小端) */']
    for f in spec['frames']:
        fields = f.get('fields', [])
        if not fields:
            continue
        L.append('typedef struct __attribute__((packed)) {')
        for x in fields:
            L.append(f'    {C_TYPE[x["type"]]} {x["name"]};')
        L.append(f'}} frame_{f["name"]}_t;')
    L += ['',
          '/* 接收帧 */',
          'typedef struct {',
          '    uint8_t func;',
          '    uint8_t len;',
          '    uint8_t data[PROTO_MAX_DATA];',
          '    uint8_t ready;   /* 1=收到完整有效帧 */',
          '} proto_frame_t;', '',
          '/* sum8 校验 */',
          'static inline uint8_t proto_checksum(uint8_t len, uint8_t func, const uint8_t *data) {',
          '    uint8_t s = (uint8_t)(len + func);',
          '    for (uint8_t i = 0; i < len - 1; i++) s = (uint8_t)(s + data[i]);',
          '    return s;',
          '}', '',
          '/* 组帧: out 须 >= len+5; 返回总字节数。data 不含 func; len = 1(func)+payload */',
          'static inline uint8_t proto_build(uint8_t func, const uint8_t *payload, uint8_t plen, uint8_t *out) {',
          '    uint8_t len = (uint8_t)(plen + 1);',
          '    uint8_t s = (uint8_t)(len + func), i = 0;',
          '    out[0]=PROTO_HEADER0; out[1]=PROTO_HEADER1; out[2]=len; out[3]=func;',
          '    for (i = 0; i < plen; i++) { out[4+i] = payload[i]; s = (uint8_t)(s + payload[i]); }',
          '    out[4+plen] = s; out[5+plen] = PROTO_TAIL;',
          '    return (uint8_t)(plen + 6);',
          '}', '',
          '/* 逐字节喂入的解析状态机 (复用 KB 07 重同步状态机)。收到完整帧时 fr->ready=1。*/',
          'static inline void proto_parse_byte(uint8_t c, proto_frame_t *fr) {',
          '    static enum { S_H1, S_H2, S_LEN, S_BODY, S_CHK, S_TAIL } st = S_H1;',
          '    static uint8_t len=0, idx=0, sum=0, buf[PROTO_MAX_DATA];',
          '    switch (st) {',
          '    case S_H1: st = (c==PROTO_HEADER0)? S_H2 : S_H1; break;',
          '    case S_H2: st = (c==PROTO_HEADER1)? S_LEN : ((c==PROTO_HEADER0)? S_H2 : S_H1); break;',
          '    case S_LEN:',
          '        len = c; sum = c; idx = 0;',
          '        st = (len>0 && len<=PROTO_MAX_DATA)? S_BODY : S_H1;',
          '        break;',
          '    case S_BODY:',
          '        buf[idx++] = c; sum = (uint8_t)(sum + c);',
          '        if (idx >= len) st = S_CHK;',
          '        break;',
          '    case S_CHK: st = (c==sum)? S_TAIL : S_H1; break;',
          '    case S_TAIL:',
          '        if (c==PROTO_TAIL) { fr->func=buf[0]; fr->len=len; ',
          '            for (uint8_t i=0;i<len;i++) fr->data[i]=buf[i]; fr->ready=1; }',
          '        st = S_H1;',
          '        break;',
          '    }',
          '}', '', '#endif /* PROTOCOL_H */', '']
    return '\n'.join(L)


def gen_py(spec, sig):
    fr = spec['framing']; h0, h1 = fr['header']
    L = ['# 自动生成 — 勿手改。源: contracts/protocol.yaml  生成器: tools/gen_protocol.py',
         '# K230 <-> 主控 UART 帧协议 (MicroPython / K230 端)',
         'import struct', '',
         f'PROTOCOL_SIG = "{sig}"   # 两端一致性签名，须与 protocol.h 相同',
         f'HEADER = bytes(({h0:#04x}, {h1:#04x}))',
         f'TAIL = {fr["tail"]:#04x}',
         f'MAX_DATA = {fr["max_data"]}',
         f'# 链路: {spec["link"]["baud"]} {spec["link"]["data_bits"]}'
         f'{spec["link"]["parity"][0].upper()}{spec["link"]["stop_bits"]}, {spec["link"]["level"]}', '',
         '# 功能码']
    for f in spec['frames']:
        L.append(f'FUNC_{f["name"].upper()} = {f["func"]:#04x}  # {f.get("desc","")}')
    L += ['', '',
          'def _checksum(length, func, payload):',
          '    s = (length + func) & 0xFF',
          '    for b in payload:',
          '        s = (s + b) & 0xFF',
          '    return s', '', '',
          'def build(func, payload=b""):',
          '    """组一帧完整字节串。"""',
          '    length = len(payload) + 1  # +1 = func',
          '    s = _checksum(length, func, payload)',
          '    return HEADER + bytes((length, func)) + payload + bytes((s, TAIL))', '']
    # 每帧发送助手
    for f in spec['frames']:
        fields = f.get('fields', [])
        args = ', '.join(x['name'] for x in fields)
        fmt = '<' + ''.join(PY_STRUCT[x['type']] for x in fields)
        L.append(f'def {f["name"]}({args}):')
        L.append(f'    """{f.get("desc","")}"""')
        if fields:
            L.append(f'    return build(FUNC_{f["name"].upper()}, struct.pack("{fmt}", {args}))')
        else:
            L.append(f'    return build(FUNC_{f["name"].upper()})')
        L.append('')
    # 简易接收解析器
    L += ['',
          'class Parser:',
          '    """逐字节喂入；feed() 返回 (func, data_bytes) 或 None。重同步状态机。"""',
          '    def __init__(self):',
          '        self.st = 0; self.len = 0; self.idx = 0; self.sum = 0; self.buf = bytearray(MAX_DATA)',
          '    def feed(self, c):',
          '        if self.st == 0:   self.st = 1 if c == HEADER[0] else 0',
          '        elif self.st == 1: self.st = 2 if c == HEADER[1] else (1 if c == HEADER[0] else 0)',
          '        elif self.st == 2:',
          '            self.len = c; self.sum = c; self.idx = 0',
          '            self.st = 3 if 0 < c <= MAX_DATA else 0',
          '        elif self.st == 3:',
          '            self.buf[self.idx] = c; self.idx += 1; self.sum = (self.sum + c) & 0xFF',
          '            if self.idx >= self.len: self.st = 4',
          '        elif self.st == 4: self.st = 5 if c == self.sum else 0',
          '        elif self.st == 5:',
          '            self.st = 0',
          '            if c == TAIL:',
          '                return self.buf[0], bytes(self.buf[1:self.len])',
          '        return None', '']
    return '\n'.join(L)


def extract_sig_h(text):
    m = re.search(r'#define PROTOCOL_SIG "([0-9a-f]+)"', text)
    return m.group(1) if m else None


def extract_sig_py(text):
    m = re.search(r'PROTOCOL_SIG = "([0-9a-f]+)"', text)
    return m.group(1) if m else None


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'contracts', 'protocol.yaml')
    spec = load(src)

    errs = validate(spec)
    if errs:
        print("✗ protocol.yaml 校验失败:")
        for e in errs:
            print("   -", e)
        sys.exit(1)

    sig = signature(spec)
    h_path = os.path.join(ROOT, 'contracts', 'protocol.h')
    py_path = os.path.join(ROOT, 'contracts', 'protocol.py')
    with open(h_path, 'w', encoding='utf-8') as f:
        f.write(gen_h(spec, sig))
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(gen_py(spec, sig))

    # 两端一致性自检：回读两个文件的 PROTOCOL_SIG，与 yaml 签名三者比对
    sig_h = extract_sig_h(open(h_path, encoding='utf-8').read())
    sig_py = extract_sig_py(open(py_path, encoding='utf-8').read())
    print(f"协议签名 yaml={sig}  protocol.h={sig_h}  protocol.py={sig_py}")
    if sig == sig_h == sig_py:
        print(f"✓ 生成成功，两端一致。共 {len(spec['frames'])} 帧。")
        print(f"  -> {os.path.relpath(h_path, ROOT)}")
        print(f"  -> {os.path.relpath(py_path, ROOT)}")
        sys.exit(0)
    else:
        print("✗ 两端签名不一致——生成有问题，请检查 gen_protocol.py")
        sys.exit(2)


if __name__ == '__main__':
    main()
