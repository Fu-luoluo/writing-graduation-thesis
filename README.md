# 综述类毕业论文写作与排版 Skill (writing-graduation-thesis)

> 一个端到端（End-to-End）的 AI 技能（Skill），用于辅助完成综述类毕业论文（Literature Review Thesis）的撰写、排版、引用核对与质检交付。

本 Skill 旨在将杂乱的草稿、零散的文献和复杂的 Word 排版规范，固化为一条可复用的流水线。通过**「三大闸门」**控制质量，借助 **Python 自动化脚本** 处理繁琐的格式与引用检查，最终交付符合 `GB/T 7714—2015` 标准的 Word 终稿。

---

## 核心特性

- **严守学术底线**：只使用用户提供的文献，不编造文献、数据、结论；无支撑的表述强制标记 `[待确认]`。
- **样式值覆盖套用**：不整体替换用户的 Word 文档，而是解析官方模板并逐项覆盖样式，保留正文内容与原有编号。
- **自动化引用核对**：通过脚本一键检查正文引用是否连续、是否与文后条目一一对应、是否有跳号或漏引。
- **标准流水线作业**：S0-S7 阶段化执行，包含 3 个强制的用户确认闸门，避免 AI 跑偏。
- **绝不制造垃圾**：内置严格的 `.gitignore`，自动隔离用户产生的真实文献、草稿、终稿，防止隐私泄露。

---

## 目录结构

```text
writing-graduation-thesis/
├── SKILL.md                 # AI 核心指令：定义硬约束、流程总览(S0-S7)与执行准则
├── scripts/                 # 核心自动化脚本 (需安装 Python 依赖)
│   ├── init_workspace.py    # 工作区初始化与资产自动探测
│   ├── extract_pdfs.py      # 批量提取 PDF 文本，合并语料库
│   ├── apply_template.py    # 模板预检与样式值覆盖
│   └── check_citations.py   # 引用连续性、一一对应核对
├── references/              # 规则知识库 (Markdown)
│   ├── format-spec.md       # 页面/分节/样式规范、兜底参数
│   ├── gbt7714.md           # 顺序编码制与著录规则
│   ├── outline-rules.md     # 综述结构、章节分工、大纲调整
│   └── qc-checklist.md      # 终稿质检清单 (闸门3)
└── assets/                  # 产出资产与模板
    ├── fallback-template.docx # 无官方模板时的兜底 Word 骨架
    ├── ledger-template.xlsx   # 文献台账与引用映射表
    └── report-template.md     # 格式检查报告生成模板