#!/usr/bin/env python3
"""extract_pdfs.py — 批量提取 PDF 文本，供综述写作与文献核对使用。

用法:
    python extract_pdfs.py <pdf_dir> <out_dir> [--combined corpus.txt]

说明:
    - 逐个提取 PDF 文本，写入 <out_dir>/<pdf名>.txt；
    - 显式处理加密、损坏、无文本层等情况，不中断整体流程；
    - 输出每个文件的状态、页数、字符数；
    - --combined 额外将全部文本合并为一个文件。
"""
import argparse
import os
import sys

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    print("[错误] 需要 pypdf，请先安装: pip install pypdf", file=sys.stderr)
    sys.exit(2)


def extract_one(pdf_path):
    """返回 (status, pages, text)。status: ok / encrypted / no_text / error。"""
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                return "encrypted", 0, ""
        pages = len(reader.pages)
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                parts.append("")
        text = "\n".join(parts).strip()
        if not text:
            return "no_text", pages, ""
        return "ok", pages, text
    except Exception as exc:  # 损坏或无法解析
        return "error", 0, f"<<解析失败: {type(exc).__name__}: {exc}>>"


def main():
    parser = argparse.ArgumentParser(description="批量提取 PDF 文本")
    parser.add_argument("pdf_dir", help="PDF 所在目录")
    parser.add_argument("out_dir", help="文本输出目录")
    parser.add_argument("--combined", metavar="FILE", help="合并输出文件名（置于 out_dir）")
    args = parser.parse_args()

    pdf_dir = os.path.abspath(args.pdf_dir)
    out_dir = os.path.abspath(args.out_dir)
    if not os.path.isdir(pdf_dir):
        print(f"[错误] PDF 目录不存在: {pdf_dir}", file=sys.stderr)
        return 2
    os.makedirs(out_dir, exist_ok=True)

    pdfs = sorted(f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf"))
    if not pdfs:
        print(f"[提示] 目录中没有 PDF: {pdf_dir}")
        return 0

    print(f"共发现 {len(pdfs)} 个 PDF，开始提取...\n")
    stats = {"ok": 0, "encrypted": 0, "no_text": 0, "error": 0}
    combined_parts = []

    for name in pdfs:
        pdf_path = os.path.join(pdf_dir, name)
        status, pages, text = extract_one(pdf_path)
        stats[status] += 1
        base = os.path.splitext(name)[0]
        out_path = os.path.join(out_dir, base + ".txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text if text else f"<<{status}: {name}>>")
        print(f"  [{status:9s}] {name}  pages={pages} chars={len(text)}")
        if status == "ok":
            combined_parts.append(f"\n\n===== {name} =====\n{text}")

    if args.combined:
        combined_path = os.path.join(out_dir, args.combined)
        with open(combined_path, "w", encoding="utf-8") as f:
            f.write("\n".join(combined_parts))
        print(f"\n合并文本已写入: {combined_path}")

    print("\n汇总: " + ", ".join(f"{k}={v}" for k, v in stats.items()))
    if stats["ok"] == 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
