#!/usr/bin/env python3
"""git 背书的任务板 + 流水线 DAG 自动派活（确定性引擎，任何模型/纯命令均可用）。

每个任务一文件 board/<id>.yaml（避免 git 冲突）。完成一个任务时，按内置 DAG
自动给下游 lane 派生任务（写新文件）；任务只有依赖全 done 才在 list 里"就绪"。
跨机器靠 git pull/push 同步；近实时靠 /loop 或 tools/watch.sh 轮询。

命令:
    python tools/board.py init                 初始化根任务(read-problem)
    python tools/board.py list [--lane LANE]    列出就绪任务(依赖已全 done)
    python tools/board.py status                全局看板
    python tools/board.py done <id> [--by LANE] 标完成(校验门/签字)+ 自动派生下游任务
    python tools/board.py show <id>             看单个任务
LANE ∈ lead | 硬件 | 控制 | 算法

done 会先校验该任务声明的确定性门(design/gates/<gate>.yaml=PASS)与人工签字
(design/signoffs.yaml=approved)，未满足则拒绝(exit 3)；确需越过加 --force(留痕)。
"""
import sys, os, glob
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib  # 门-状态耦合：done 前校验确定性门 + 人工签字（与 gate_check.py 共用判据）

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 默认 board/；ELEC_BOARD_DIR 可覆盖（测试用，不污染真实任务板）
BOARD = os.environ.get('ELEC_BOARD_DIR', os.path.join(ROOT, 'board'))

# 流水线规范任务图（id -> 角色/类型/依赖/标题/提示 + 可选 gate/signoff）。
# gate    = 完成前必过的确定性门名（对应 design/gates/<gate>.yaml，result 须 PASS）。
# signoff = 完成前必有的人工签字名（对应 design/signoffs.yaml，status 须 approved）。
# 任务在某个依赖完成时才被"派生"创建。
TASKS = {
    "read-problem":     dict(owner="lead", kind="skill",  deps=[],                          title="读题/审题",                hint="/read-problem"),
    "plan-solution":    dict(owner="lead", kind="skill",  deps=["read-problem"],            title="方案+需求(签字表)",        hint="/plan-solution",   signoff="solution-signoff"),
    "setup-env":        dict(owner="lead", kind="skill",  deps=["plan-solution"],           title="环境全包(三lane清单)",     hint="/setup-env"),
    "select-parts":     dict(owner="lead", kind="skill",  deps=["plan-solution"],           title="选材(配件表→BOM)",         hint="/select-parts",    signoff="bom-approval"),
    "power-design":     dict(owner="lead", kind="skill",  deps=["select-parts"],            title="供电(按堵转算)",           hint="/power-design",    gate="power",  signoff="power-approval"),
    "interconnect":     dict(owner="lead", kind="skill",  deps=["power-design"],            title="接线图(pinmap→wiring)",    hint="/interconnect",    gate="pinmux", signoff="wiring-net-review"),
    "vision-scaffold":  dict(owner="算法", kind="skill",  deps=["plan-solution"],           title="K230 视觉骨架",            hint="/vision-scaffold"),
    "vision-tune":      dict(owner="算法", kind="manual", deps=["vision-scaffold"],         title="K230 现场阈值/识别整定",   hint="design/test_plan.md B/D"),
    "firmware-scaffold":dict(owner="控制", kind="skill",  deps=["interconnect"],            title="固件骨架(SysConfig/工程)", hint="/firmware-scaffold", gate="compile", signoff="peripheral-init-review"),
    "hw-wiring":        dict(owner="硬件", kind="manual", deps=["interconnect"],            title="照接线图连线/焊接/供电",   hint="design/wiring.svg + harness.md"),
    "test-checklist":   dict(owner="lead", kind="skill",  deps=["interconnect"],            title="测试标定清单",             hint="/test-checklist"),
    "ctrl-bringup":     dict(owner="控制", kind="manual", deps=["firmware-scaffold", "hw-wiring"], title="实车 bring-up + 内环PID", hint="design/test_plan.md A/C"),
    "integration":      dict(owner="all",  kind="manual", deps=["ctrl-bringup", "vision-tune", "test-checklist"], title="整车联调:外环PID+全场跑", hint="design/test_plan.md D/E"),
}
LANES = {"lead", "硬件", "控制", "算法", "all"}


def tpath(tid):
    return os.path.join(BOARD, f"{tid}.yaml")


def load(tid):
    p = tpath(tid)
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return yaml.safe_load(f)


def exists(tid):
    return os.path.exists(tpath(tid))


def create(tid, created_by="dag"):
    spec = TASKS[tid]
    t = dict(id=tid, title=spec["title"], owner=spec["owner"], kind=spec["kind"],
             deps=list(spec["deps"]), status="todo", hint=spec["hint"], created_by=created_by)
    os.makedirs(BOARD, exist_ok=True)
    with open(tpath(tid), 'w', encoding='utf-8') as f:
        yaml.safe_dump(t, f, allow_unicode=True, sort_keys=False)
    return t


def save(t):
    with open(tpath(t["id"]), 'w', encoding='utf-8') as f:
        yaml.safe_dump(t, f, allow_unicode=True, sort_keys=False)


def deps_done(t):
    return all((load(d) or {}).get("status") == "done" for d in t.get("deps", []))


def ready(t):
    return t.get("status") == "todo" and deps_done(t)


def cmd_init():
    n = 0
    for tid, spec in TASKS.items():
        if not spec["deps"] and not exists(tid):
            create(tid, "init"); n += 1
    print(f"✓ 任务板初始化：建根任务 {n} 个 -> {os.path.relpath(BOARD, ROOT)}/")
    cmd_list(None)


def cmd_list(lane):
    if lane and lane not in LANES:
        print(f"未知 lane: {lane}（{', '.join(sorted(LANES))}）"); sys.exit(2)
    rows = []
    for p in sorted(glob.glob(os.path.join(BOARD, "*.yaml"))):
        t = yaml.safe_load(open(p, encoding='utf-8'))
        if not ready(t):
            continue
        if lane and t["owner"] != lane and t["owner"] != "all":
            continue
        rows.append(t)
    tag = f"（lane={lane}）" if lane else "（全部 lane）"
    if not rows:
        print(f"就绪任务{tag}：无。`status` 看全局，或等上游 done。")
        return
    print(f"就绪任务{tag}：")
    for t in rows:
        k = "▶skill" if t["kind"] == "skill" else "✋人工"
        spec = TASKS[t["id"]]
        req = []
        if spec.get("gate"):
            req.append(f"门:{spec['gate']}")
        if spec.get("signoff"):
            req.append(f"签:{spec['signoff']}")
        gate_tag = ("  [完成需 " + " ".join(req) + "]") if req else ""
        print(f"  [{t['id']}] {t['title']}  ·{t['owner']}· {k}  → {t['hint']}{gate_tag}")


def cmd_status():
    created = {os.path.splitext(os.path.basename(p))[0]: yaml.safe_load(open(p, encoding='utf-8'))
               for p in glob.glob(os.path.join(BOARD, "*.yaml"))}
    done = [k for k, t in created.items() if t["status"] == "done"]
    todo_ready = [k for k, t in created.items() if ready(t)]
    todo_block = [k for k, t in created.items() if t["status"] == "todo" and not deps_done(t)]
    locked = [k for k in TASKS if k not in created]
    print(f"看板：完成 {len(done)} · 就绪 {len(todo_ready)} · 阻塞 {len(todo_block)} · 未解锁 {len(locked)} / 共 {len(TASKS)}")
    if done:       print("  ✓ 完成:   " + ", ".join(done))
    if todo_ready: print("  ▶ 就绪:   " + ", ".join(f"{k}({created[k]['owner']})" for k in todo_ready))
    if todo_block: print("  ⏳ 阻塞:   " + ", ".join(f"{k}<-{created[k]['deps']}" for k in todo_block))
    if locked:     print("  🔒 未解锁: " + ", ".join(locked))


def cmd_done(tid, by=None, force=False):
    if tid not in TASKS:
        print(f"未知任务: {tid}"); sys.exit(2)
    spec = TASKS[tid]
    t = load(tid)
    if t is None:
        print(f"任务 {tid} 还没被派生（未解锁）。先完成其上游。"); sys.exit(2)
    # —— 门-状态耦合：未过确定性门 / 未签字 不得标完成（--force 可越过，留痕）——
    ok, problems = gatelib.check_spec(spec)
    if not ok and not force:
        print(f"✗ [{tid}] 不能标完成——门/签字未满足：")
        for p in problems:
            print(f"   - {p}")
        print("  （修好后重试；确需越过用 --force，会在任务里留 forced 痕迹）")
        sys.exit(3)
    t["status"] = "done"
    if not ok and force:
        t["forced"] = True
        print(f"⚠ [{tid}] 越过未满足的门/签字（--force）：" + "；".join(problems))
    if by:
        t["done_by"] = by
    save(t)
    # 按 DAG 派生下游：所有把 tid 列为依赖、且尚未创建的任务
    spawned = []
    for cid, spec in TASKS.items():
        if tid in spec["deps"] and not exists(cid):
            create(cid, created_by=tid)
            spawned.append(cid)
    print(f"✓ [{tid}] 标记完成" + (f"（by {by}）" if by else ""))
    if spawned:
        print("  → 自动派生下游任务：")
        for cid in spawned:
            c = TASKS[cid]
            rdy = "就绪" if deps_done(load(cid)) else f"待依赖 {c['deps']}"
            print(f"     [{cid}] {c['title']}  ·{c['owner']}·  ({rdy})  {c['hint']}")
    else:
        print("  （无新下游任务派生）")
    # 提示哪些因此变就绪
    newly = [cid for cid in TASKS if exists(cid) and ready(load(cid))]
    if newly:
        print("  当前就绪：" + ", ".join(f"{k}({TASKS[k]['owner']})" for k in newly))


def cmd_show(tid):
    t = load(tid)
    if t is None:
        print(f"任务 {tid} 未派生/不存在"); sys.exit(2)
    print(yaml.safe_dump(t, allow_unicode=True, sort_keys=False))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    cmd = args[0]
    if cmd == "init":
        cmd_init()
    elif cmd == "list":
        lane = None
        if "--lane" in args:
            lane = args[args.index("--lane") + 1]
        cmd_list(lane)
    elif cmd == "status":
        cmd_status()
    elif cmd == "done":
        if len(args) < 2:
            print("用法: board.py done <id> [--by LANE] [--force]"); sys.exit(2)
        by = args[args.index("--by") + 1] if "--by" in args else None
        cmd_done(args[1], by, force=("--force" in args))
    elif cmd == "show":
        cmd_show(args[1])
    else:
        print(__doc__); sys.exit(2)


if __name__ == '__main__':
    main()
