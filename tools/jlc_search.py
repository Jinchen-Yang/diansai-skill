#!/usr/bin/env python3
"""jlcsearch 查件助手（配件表缺口时按规格现查在库件）。
封装 tscircuit 的 jlcsearch JSON 服务。仅作 select-parts 的补充，非确定性门——
网络不可用时优雅降级（提示离线，不报致命错）。

用法:
    python tools/jlc_search.py "TB6612" [--limit 10]
    python tools/jlc_search.py "buck 5V 3A" --limit 5
"""
import sys, json

# 公共第三方镜像（tscircuit 社区的 JLC 搜索服务），非官方 API；不可达时本工具优雅降级。
BASE = "https://jlcsearch.tscircuit.com"
TIMEOUT = 12


def search(query, limit=10):
    import requests  # 延迟导入，缺包时给清晰提示
    url = f"{BASE}/components/list.json"
    r = requests.get(url, params={"search": query, "limit": limit}, timeout=TIMEOUT,
                     headers={"User-Agent": "elec-race/jlc_search"})
    r.raise_for_status()
    data = r.json()
    # 返回结构可能是 {components:[...]} 或 list；兼容处理
    if isinstance(data, dict):
        for k in ("components", "items", "results", "data"):
            if k in data and isinstance(data[k], list):
                return data[k]
        # 找不到已知键，返回首个 list 值
        for v in data.values():
            if isinstance(v, list):
                return v
        return []
    return data if isinstance(data, list) else []


def main():
    args = sys.argv[1:]
    if not args:
        print('用法: python tools/jlc_search.py "<查询>" [--limit N]')
        sys.exit(2)
    limit = 10
    if "--limit" in args:
        i = args.index("--limit")
        try:
            limit = int(args[i + 1]); del args[i:i + 2]
        except (IndexError, ValueError):
            print("--limit 需要一个整数"); sys.exit(2)
    query = " ".join(args)

    try:
        rows = search(query, limit)
    except ImportError:
        print("✗ 缺 requests：pip install requests（或跑 tools/bootstrap.sh）"); sys.exit(2)
    except Exception as e:
        print(f"⚠ 离线/查询失败（{type(e).__name__}: {e}）。")
        print("  jlc_search 是联网助手；离线时请从主办方配件表里选，或联网后重试。")
        sys.exit(0)  # 非致命

    if not rows:
        print(f"（无结果：{query}）"); sys.exit(0)
    print(f"jlcsearch '{query}' 前 {min(limit,len(rows))} 条：")
    for it in rows[:limit]:
        if isinstance(it, dict):
            lcsc = it.get("lcsc") or it.get("lcsc_id") or it.get("partNumber") or "?"
            desc = it.get("description") or it.get("mfr") or it.get("name") or ""
            pkg = it.get("package") or ""
            stock = it.get("stock") or it.get("quantity") or ""
            price = it.get("price") or ""
            # price 可能是阶梯报价 list 或其 JSON 字符串 [{qFrom,qTo,price}]；取最小起订价
            if isinstance(price, str) and price.strip().startswith("["):
                try:
                    price = json.loads(price)
                except ValueError:
                    pass
            if isinstance(price, list) and price:
                p0 = price[0]
                price = (f"¥{float(p0['price']):.3f}@{p0.get('qFrom', 1)}+"
                         if isinstance(p0, dict) and p0.get('price') is not None else "")
            print(f"  LCSC {lcsc} | {pkg} | 库存 {stock} | {price} | {str(desc)[:60]}")
        else:
            print(f"  {it}")


if __name__ == '__main__':
    main()
