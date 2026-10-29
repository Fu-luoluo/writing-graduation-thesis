#!/usr/bin/env python3
"""check_citations.py — 核对综述论文的顺序编码引用与参考文献表。

用法:
    python check_citations.py <paper.docx>

检查项:
    1. 正文引用编号是否连续、首次出现顺序是否为 1,2,3...;
    2. 正文引用集合与文后条目集合是否一一对应;
    3. 文后条目是否有重复、跳号;
    4. 条目是否含 [J]/[D] 类型标识;
    5. 统计引用标记数量与覆盖情况。
存在问题时退出码为 1。
"""
import re
import sys

try:
    from docx import Document
    from docx.oxml.ns import qn
except ImportError:  # pragma: no cover
    print("[错误] 需要 python-docx，请先安装: pip install python-docx", file=sys.stderr)
    sys.exit(2)

# [n] / [n-m] / [n,m] / [n][m]
RANGE_RE = re.compile(r"\[(\d{1,3})\s*[-–—]\s*(\d{1,3})\]")
LIST_RE = re.compile(r"\[(\d{1,3}(?:\s*[,，]\s*\d{1,3})*)\]")
ENTRY_RE = re.compile(r"^\s*\[(\d{1,3})\]")


def ordered_blocks(doc):
    """按文档顺序返回文本块（段落与表格混排），并标注是否为标题。"""
    blocks = []
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            text = "".join(t.text or "" for t in child.iter(qn("w:t")))
            style = child.find(qn("w:pPr"))
            is_heading = False
            if style is not None and style.find(qn("w:pStyle")) is not None:
                val = style.find(qn("w:pStyle")).get(qn("w:val"), "")
                is_heading = "Heading" in val or val.startswith(("1", "2", "3")) and "heading" in val.lower()
            blocks.append((text, is_heading))
        elif child.tag == qn("w:tbl"):
            text = "".join(t.text or "" for t in child.iter(qn("w:t")))
            blocks.append((text, False))
    return blocks


def cited_in(text):
    """提取文本中引用的编号集合与标记数。"""
    nums = set()
    marks = 0
    for m in RANGE_RE.finditer(text):
        a, b = int(m.group(1)), int(m.group(2))
        if a <= b:
            nums.update(range(a, b + 1))
        marks += 1
    text2 = RANGE_RE.sub("", text)
    for m in LIST_RE.finditer(text2):
        group = [int(x) for x in re.split(r"[,，]", m.group(1))]
        nums.update(group)
        marks += 1
    return nums, marks


def main():
    if len(sys.argv) != 2:
        print("用法: python check_citations.py <paper.docx>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    doc = Document(path)
    blocks = ordered_blocks(doc)

    # 定位参考文献标题
    ref_idx = None
    for i, (text, is_heading) in enumerate(blocks):
        if text.strip().replace(" ", "").endswith("参考文献") or text.strip() == "参考文献":
            ref_idx = i
            break

    if ref_idx is None:
        print("[严重] 未找到“参考文献”标题。")
        return 1

    # 正文：标题之前的块；文后：之后
    body_blocks = blocks[:ref_idx]
    ref_blocks = blocks[ref_idx + 1:]

    # 首次出现顺序
    first_order = []
    seen = set()
    total_marks = 0
    for text, _ in body_blocks:
        nums, marks = cited_in(text)
        total_marks += marks
        for n in sorted(nums):
            if n not in seen:
                seen.add(n)
                first_order.append(n)

    # 文后条目
    entries = {}
    for text, _ in ref_blocks:
        m = ENTRY_RE.match(text)
        if m:
            n = int(m.group(1))
            entries.setdefault(n, text.strip())

    cited = set(first_order)
    listed = set(entries)

    print("=" * 64)
    print("引用核对结果")
    print("=" * 64)
    print(f"正文引用标记数: {total_marks}")
    print(f"正文引用不同编号数: {len(cited)}；文后条目数: {len(entries)}")
    print(f"首次出现顺序: {first_order}")

    problems = []

    expected = list(range(1, max(first_order) + 1)) if first_order else []
    if first_order != expected:
        missing_order = [x for x in expected if x not in first_order]
        problems.append(f"首次出现顺序非 1..N 连续；缺失/异常: {missing_order}")

    only_cited = sorted(cited - listed)
    if only_cited:
        problems.append(f"正文引用但文后缺条目: {only_cited}")

    only_listed = sorted(listed - cited)
    if only_listed:
        problems.append(f"文有条目但正文未引用: {only_listed}")

    dup = [n for n, _ in enumerate(entries, 1) if False]
    # 重复条目（同一编号出现多次）
    counts = {}
    for text, _ in ref_blocks:
        m = ENTRY_RE.match(text)
        if m:
            counts[int(m.group(1))] = counts.get(int(m.group(1)), 0) + 1
    duplicates = [n for n, c in counts.items() if c > 1]
    if duplicates:
        problems.append(f"文后重复编号: {duplicates}")

    if listed:
        gaps = [n for n in range(1, max(listed) + 1) if n not in listed]
        if gaps:
            problems.append(f"文后条目跳号: {gaps}")

    # 类型标识检查
    no_type = [n for n, t in entries.items() if ("[J]" not in t and "[D]" not in t)]
    if no_type:
        problems.append(f"条目缺 [J]/[D] 标识: {no_type}")

    if problems:
        print("\n[发现问题]")
        for p in problems:
            print("  - " + p)
        return 1

    print("\n[通过] 顺序编码连续，正文与文后一一对应，类型标识齐全。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
