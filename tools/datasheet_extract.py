#!/usr/bin/env python3
"""数据手册确定性抽取（select-parts 的兜底）：从 PDF 文本层抽引脚表/关键参数候选行。
多模态读手册是 lead/Claude 的活；本工具只做"文本层 + 关键词命中"的确定性预筛，
结果须人工/多模态复核（关键额定值绝不单凭本工具下结论）。

用法:
    python tools/datasheet_extract.py <datasheet.pdf> [--grep "Vgs|Iout|Abs Max"]
"""
import sys, re

DEFAULT_KEYS = r"(abs(olute)? max|recommended operating|V\s*(in|out|gs|cc|dd)|I\s*(out|max|q)|pin(out)?|package|RDS)"


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python tools/datasheet_extract.py <datasheet.pdf> [--grep PATTERN]")
        sys.exit(2)
    pattern = DEFAULT_KEYS
    if "--grep" in args:
        i = args.index("--grep")
        try:
            pattern = args[i + 1]; del args[i:i + 2]
        except IndexError:
            print("--grep 需要一个正则"); sys.exit(2)
    path = args[0]

    import os
    if not os.path.exists(path):
        print(f"✗ 文件不存在: {path}")
        sys.exit(2)

    rx = re.compile(pattern, re.IGNORECASE)
    hits, tables = 0, 0
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            print(f"页数: {len(pdf.pages)}  | 关键词: {pattern}  | 引擎: pdfplumber")
            for pno, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                for line in text.splitlines():
                    if rx.search(line):
                        print(f"  p{pno}: {line.strip()[:100]}")
                        hits += 1
                for t in (page.extract_tables() or []):
                    tables += 1
    except ImportError:
        # 兜底：pdfplumber 缺失/装不上时退化用 pypdf（只抽文本行，不抽表格）
        try:
            from pypdf import PdfReader
        except ImportError:
            print("✗ 缺 pdfplumber 且缺 pypdf：pip install pdfplumber pypdf（或跑 tools/bootstrap.sh）")
            sys.exit(2)
        reader = PdfReader(path)
        print(f"页数: {len(reader.pages)}  | 关键词: {pattern}  | 引擎: pypdf(无表格抽取)")
        for pno, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            for line in text.splitlines():
                if rx.search(line):
                    print(f"  p{pno}: {line.strip()[:100]}")
                    hits += 1
    print(f"\n命中 {hits} 行 / {tables} 张表。")
    print("⚠ 文本层预筛，可能漏扫描件/合并单元格；关键额定(Vmax/Imax/封装/引脚)须多模态(lead)复核。")
    sys.exit(0)


if __name__ == '__main__':
    main()
