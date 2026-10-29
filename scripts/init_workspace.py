#!/usr/bin/env python3
"""init_workspace.py — 综述类毕业论文工作区初始化与资产自动探测。

用法:
    python init_workspace.py <target_dir>                 # 仅扫描并报告资产
    python init_workspace.py <target_dir> --create        # 扫描并创建标准目录骨架
    python init_workspace.py <target_dir> --create --force # 允许创建缺失目录(默认即创建,不覆盖已有文件)

说明:
    - 标准骨架: 01-文献库/ 02-模板库/ 03-初稿/ 04-终稿/ 05-质检文档/
    - 幂等: 已存在的目录与文件一律保留, 不覆盖用户文件。
    - 自动探测: 按关键词识别已有的文献/模板/草稿/输出文件夹。
"""
import argparse
import os
import sys

# 标准目录骨架 (目录名, 说明)
SCAFFOLD = [
    ("01-文献库", "参考文献 PDF；建议原地引用，附 manifest.md 路径清单"),
    ("02-模板库", "学校官方 Word 模板"),
    ("03-初稿", "内容完整、引用体系建立的初稿"),
    ("04-终稿", "套用模板、含图表、核对通过的终稿"),
    ("05-质检文档", "文献台账、格式检查报告"),
]

# 资产探测关键词 (小写匹配)
DETECT = {
    "文献库": ["参考文献", "文献库", "文献", "literature", "papers", "refs"],
    "模板库": ["格式模板", "模板库", "模板", "template", "templates"],
    "草稿": ["初稿综述", "草稿", "大纲", "draft", "outline"],
    "输出/工具": ["output", "输出", "tools", "工具"],
}

MANIFEST_TEMPLATE = """# 文献库路径清单（manifest）

> 本清单记录文献的实际存放位置。默认原地引用，避免复制大量 PDF。
> 无 PDF 的文献请在“PDF 可得性”中标注“无 PDF”，仅按主题层面引用。

| 序号 | 文献题名 | 实际路径 | PDF 可得性 |
|---|---|---|---|
| 1 |  |  |  |
"""


def scan(target):
    """扫描 target 下一级目录，返回 {资产类别: [目录名]}。"""
    found = {k: [] for k in DETECT}
    try:
        entries = sorted(os.listdir(target))
    except FileNotFoundError:
        return None, found
    for name in entries:
        full = os.path.join(target, name)
        if not os.path.isdir(full):
            continue
        low = name.lower()
        for category, keywords in DETECT.items():
            if any(kw in low or kw in name for kw in keywords):
                found[category].append(name)
                break
    return entries, found


def count_files(directory, ext):
    """统计 directory 下（含一级子目录）指定扩展名文件数。"""
    total = 0
    for root, _dirs, files in os.walk(directory):
        total += sum(1 for f in files if f.lower().endswith(ext))
    return total


def main():
    parser = argparse.ArgumentParser(description="毕业论文工作区初始化与资产探测")
    parser.add_argument("target", help="目标工作区目录")
    parser.add_argument("--create", action="store_true", help="创建标准目录骨架")
    args = parser.parse_args()

    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print(f"[错误] 目标目录不存在: {target}", file=sys.stderr)
        return 2

    print("=" * 64)
    print(f"工作区: {target}")
    print("=" * 64)

    entries, found = scan(target)
    print("\n[资产自动探测结果]")
    for category, names in found.items():
        if names:
            detail = []
            for n in names:
                full = os.path.join(target, n)
                pdfs = count_files(full, ".pdf")
                docx = count_files(full, ".docx")
                extra = []
                if pdfs:
                    extra.append(f"{pdfs} PDF")
                if docx:
                    extra.append(f"{docx} docx")
                detail.append(f"{n}" + (f"（{', '.join(extra)}）" if extra else ""))
            print(f"  {category}: {', '.join(detail)}")
        else:
            print(f"  {category}: 未发现")

    if not args.create:
        print("\n[提示] 仅扫描未创建骨架。加 --create 可创建标准目录。")
        return 0

    print("\n[创建标准目录骨架]")
    for dirname, note in SCAFFOLD:
        path = os.path.join(target, dirname)
        if os.path.isdir(path):
            print(f"  已存在，保留: {dirname}")
        else:
            os.makedirs(path, exist_ok=True)
            print(f"  已创建: {dirname}  # {note}")

    manifest = os.path.join(target, "01-文献库", "manifest.md")
    if os.path.exists(manifest):
        print("  manifest.md 已存在，保留")
    else:
        with open(manifest, "w", encoding="utf-8") as f:
            f.write(MANIFEST_TEMPLATE)
        print("  已写入: 01-文献库/manifest.md")

    print("\n[完成] 未覆盖任何已有文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
