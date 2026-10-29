#!/usr/bin/env python3
"""apply_template.py — 以"样式值覆盖"方式把模板的页面设置与样式应用到目标文档。

用法:
    python apply_template.py <template.docx> <target.docx> [--dry-run] [--out OUT.docx]

说明:
    - 不整体替换文档: 仅复制页面设置、缺失样式, 保留目标正文与原编号;
    - 预检模板编号依赖 (numStyleLink/styleLink), 存在依赖时不搬 numbering.xml;
    - 复制样式时剥离其中的 numPr, 避免引用模板编号导致失效;
    - 默认输出 <target>.templated.docx, 不覆盖目标文件; --dry-run 仅报告。
"""
import argparse
import copy
import os
import re
import sys
import zipfile

try:
    from docx import Document
    from docx.oxml.ns import qn
except ImportError:  # pragma: no cover
    print("[错误] 需要 python-docx，请先安装: pip install python-docx", file=sys.stderr)
    sys.exit(2)


def cm(emu):
    return round(emu / 360000, 2) if emu is not None else None


def section_info(sec):
    return {
        "宽x高(cm)": f"{cm(sec.page_width)}x{cm(sec.page_height)}",
        "边距 上/下/左/右(cm)": (
            f"{cm(sec.top_margin)}/{cm(sec.bottom_margin)}/"
            f"{cm(sec.left_margin)}/{cm(sec.right_margin)}"
        ),
    }


def check_numbering(path):
    """检查 numbering.xml 是否依赖 numStyleLink/styleLink。"""
    result = {"has_numbering": False, "numStyleLink": [], "styleLink": []}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if "word/numbering.xml" not in names:
            return result
        result["has_numbering"] = True
        xml = z.read("word/numbering.xml").decode("utf-8", "ignore")
        result["numStyleLink"] = re.findall(r'<w:numStyleLink[^>]*w:val="([^"]+)"', xml)
        result["styleLink"] = re.findall(r'<w:styleLink[^>]*w:val="([^"]+)"', xml)
    return result


def style_signature(style_el):
    """提取样式基本信息 (类型, 名称)。"""
    stype = style_el.get(qn("w:type"), "")
    name_el = style_el.find(qn("w:name"))
    name = name_el.get(qn("w:val")) if name_el is not None else ""
    return stype, name


def copy_missing_styles(tpl_doc, tgt_doc):
    """把模板中目标缺失的样式复制过去，返回 (copied, stripped_numPr, skipped)。"""
    tpl_root = tpl_doc.styles.element
    tgt_root = tgt_doc.styles.element
    tgt_ids = {s.get(qn("w:styleId")) for s in tgt_root.findall(qn("w:style"))}

    copied, stripped, skipped = [], [], []
    for st in tpl_root.findall(qn("w:style")):
        sid = st.get(qn("w:styleId"))
        stype, name = style_signature(st)
        if sid in tgt_ids:
            skipped.append(f"{name or sid}")
            continue
        new = copy.deepcopy(st)
        has_num = False
        for pPr in new.iter(qn("w:pPr")):
            if pPr.find(qn("w:numPr")) is not None:
                has_num = True
                for numPr in pPr.findall(qn("w:numPr")):
                    pPr.remove(numPr)
        tgt_root.append(new)
        tgt_ids.add(sid)
        copied.append(f"{name or sid} [{stype}]")
        if has_num:
            stripped.append(f"{name or sid}")
    return copied, stripped, skipped


def copy_doc_defaults(tpl_doc, tgt_doc):
    """目标缺 docDefaults 时复制模板的默认字体定义。"""
    tpl_root = tpl_doc.styles.element
    tgt_root = tgt_doc.styles.element
    if tgt_root.find(qn("w:docDefaults")) is not None:
        return False
    defaults = tpl_root.find(qn("w:docDefaults"))
    if defaults is None:
        return False
    tgt_root.insert(0, copy.deepcopy(defaults))
    return True


def apply_page_setup(tpl_doc, tgt_doc):
    """把模板第一节的页面设置复制到目标每一节。"""
    src = tpl_doc.sections[0]
    changes = []
    for i, dst in enumerate(tgt_doc.sections):
        before = section_info(dst)
        dst.page_width = src.page_width
        dst.page_height = src.page_height
        dst.orientation = src.orientation
        dst.top_margin = src.top_margin
        dst.bottom_margin = src.bottom_margin
        dst.left_margin = src.left_margin
        dst.right_margin = src.right_margin
        changes.append((i, before["边距 上/下/左/右(cm)"],
                        section_info(dst)["边距 上/下/左/右(cm)"]))
    return changes


def main():
    parser = argparse.ArgumentParser(description="样式值覆盖方式套用模板")
    parser.add_argument("template", help="模板 docx")
    parser.add_argument("target", help="目标文档 docx")
    parser.add_argument("--dry-run", action="store_true", help="仅报告，不写出")
    parser.add_argument("--verbose", action="store_true", help="列出全部复制的样式")
    parser.add_argument("--out", help="输出路径（默认 <target>.templated.docx）")
    args = parser.parse_args()

    for p in (args.template, args.target):
        if not os.path.isfile(p):
            print(f"[错误] 文件不存在: {p}", file=sys.stderr)
            return 2

    tpl = Document(args.template)
    tgt = Document(args.target)

    print("=" * 64)
    print("模板预检")
    print("=" * 64)
    num = check_numbering(args.template)
    print(f"numbering.xml: {'有' if num['has_numbering'] else '无'}")
    if num["numStyleLink"] or num["styleLink"]:
        print("  ⚠ 发现外部样式链接依赖:")
        for x in num["numStyleLink"]:
            print(f"    numStyleLink = {x}")
        for x in num["styleLink"]:
            print(f"    styleLink = {x}")
        print("  → 不搬用模板 numbering.xml，保留目标现有编号，仅覆盖样式外观。")
    else:
        print("  无外部样式链接依赖。")

    print("\n模板页面设置（第一节）:")
    for k, v in section_info(tpl.sections[0]).items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 64)
    print("应用结果")
    print("=" * 64)
    changes = apply_page_setup(tpl, tgt)
    for idx, before, after in changes:
        print(f"  节{idx} 边距: {before} → {after}")

    copied, stripped, skipped = copy_missing_styles(tpl, tgt)
    print(f"\n复制缺失样式 {len(copied)} 个:")
    shown = copied if args.verbose else copied[:10]
    for c in shown:
        print(f"  + {c}")
    if not args.verbose and len(copied) > 10:
        print(f"  …等 {len(copied) - 10} 个（加 --verbose 查看全部）")
    if stripped:
        print(f"剥离编号引用（避免失效）: {', '.join(stripped)}")
    print(f"已存在而跳过 {len(skipped)} 个。")

    if copy_doc_defaults(tpl, tgt):
        print("已复制模板 docDefaults（默认字体）。")

    if args.dry_run:
        print("\n[dry-run] 未写出文件。")
        return 0

    out = args.out or os.path.splitext(args.target)[0] + ".templated.docx"
    tgt.save(out)
    print(f"\n[完成] 已写出: {out}")
    print("提示: 打开后 Ctrl+A → F9 更新域；原文件未被覆盖。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
