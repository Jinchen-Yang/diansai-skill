#!/usr/bin/env python3
"""门-状态耦合共享库（确定性，无 LLM）。

把"确定性门的结果"和"人工签字"落成可提交的状态文件，供 board.py / gate_check.py /
单人编排子代理统一读写，杜绝逻辑漂移。

状态落盘位置（可被 ELEC_DESIGN_DIR 覆盖，便于自测不污染真实 design/）：
    <design>/gates/<gate>.yaml   每个确定性门一份机读报告（result: PASS|FAIL）
    <design>/signoffs.yaml       人工签字列表（status: pending|approved|rejected）
"""
import os
import datetime
import hashlib
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.environ.get('ELEC_DESIGN_DIR', os.path.join(ROOT, 'design'))
GATES_DIR = os.path.join(DESIGN, 'gates')
SIGNOFFS = os.path.join(DESIGN, 'signoffs.yaml')


def _now():
    return datetime.datetime.now().isoformat(timespec='seconds')


def file_sha(target):
    """target 内容哈希（相对 ROOT 的文件路径）；非文件/不存在返回 None。
    用于把门报告绑定到被检物——被检物改了，报告即视为过期。"""
    p = target if os.path.isabs(target) else os.path.join(ROOT, target)
    if not os.path.isfile(p):
        return None
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()[:16]


# ---------- 确定性门报告 ----------

def gate_path(gate):
    return os.path.join(GATES_DIR, f'{gate}.yaml')


def write_report(gate, target, result, details=None, by=None):
    """写一份机读门报告。result ∈ {PASS, FAIL}。返回报告路径。"""
    assert result in ('PASS', 'FAIL'), result
    os.makedirs(GATES_DIR, exist_ok=True)
    rep = dict(gate=gate, target=target, target_sha=file_sha(target), result=result,
               checked_at=_now(), by=by or '', details=list(details or []))
    with open(gate_path(gate), 'w', encoding='utf-8') as f:
        yaml.safe_dump(rep, f, allow_unicode=True, sort_keys=False)
    return gate_path(gate)


def read_report(gate):
    p = gate_path(gate)
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return yaml.safe_load(f)


# ---------- 人工签字 ----------

def load_signoffs():
    if not os.path.exists(SIGNOFFS):
        return []
    with open(SIGNOFFS, encoding='utf-8') as f:
        return yaml.safe_load(f) or []


def signoff_status(gate):
    for s in load_signoffs():
        if s.get('gate') == gate:
            return s.get('status')
    return None


def set_signoff(gate, status, note=None, by=None):
    """新增/更新一条签字。status ∈ {pending, approved, rejected}。"""
    assert status in ('pending', 'approved', 'rejected'), status
    items = load_signoffs()
    rec = next((s for s in items if s.get('gate') == gate), None)
    if rec is None:
        rec = dict(gate=gate)
        items.append(rec)
    rec.update(status=status, note=note or rec.get('note', ''), by=by or rec.get('by', ''), at=_now())
    os.makedirs(DESIGN, exist_ok=True)
    with open(SIGNOFFS, 'w', encoding='utf-8') as f:
        yaml.safe_dump(items, f, allow_unicode=True, sort_keys=False)
    return rec


# ---------- 任务级校验（门 + 签字）----------

def check_spec(spec):
    """给一个任务 spec（含可选 gate / signoff 键），返回 (ok, problems[])。
    不依赖 board，避免循环 import：调用方把 spec 传进来。"""
    problems = []
    gate = spec.get('gate')
    signoff = spec.get('signoff')
    if gate:
        rep = read_report(gate)
        if rep is None:
            problems.append(f"确定性门 [{gate}] 无报告：先跑对应工具并加 --report（见 skill）")
        elif rep.get('result') != 'PASS':
            problems.append(f"确定性门 [{gate}] = {rep.get('result')}（须 PASS）")
        else:
            # 报告须绑定被检物：target 改动后旧 PASS 视为过期，须重跑门
            tgt, old = rep.get('target'), rep.get('target_sha')
            if tgt and old:
                cur = file_sha(tgt)
                if cur and cur != old:
                    problems.append(f"确定性门 [{gate}] 报告已过期：{tgt} 自上次检查后被改动，请重跑门 --report")
    if signoff:
        st = signoff_status(signoff)
        if st != 'approved':
            problems.append(f"人工签字 [{signoff}] = {st or '未签'}（须 approved；用 tools/signoff.py approve {signoff}）")
    return (len(problems) == 0, problems)
