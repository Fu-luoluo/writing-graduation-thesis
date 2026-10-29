---
name: writing-graduation-thesis
description: "Guides the end-to-end writing and formatting of review-type undergraduate graduation theses (综述类毕业论文) in Word. Use when the user wants to write, revise, or format a literature review / graduation thesis: building a literature ledger and citation mapping, converting outline-style drafts into connected academic prose, applying a school Word template via style-value override (page setup, sections, multilevel numbering, auto TOC, roman/arabic page numbers), adding vector figures and three-line tables with SEQ/REF cross-references, and verifying sequential GB/T 7714-2015 citations. Triggers on mentions of 毕业论文, 综述, 文献综述, 论文排版, 参考文献, 开题/定稿, or when a thesis draft plus a literature folder is provided. Does not produce PPT."
---

# 综述类毕业论文写作与排版

## Overview

本技能把"综述类毕业论文"从草稿到终稿的过程固化为一条可复用流水线：以用户指定文献库为唯一事实来源，以草稿为写作基线，以官方模板为格式基线，交付可直接提交的 Word 终稿，并附格式检查报告与文献台账。

## 硬约束（必须遵守）

1. 只使用用户提供的文献，不引入外部文献，不编造文献、数据、结论；无文献支撑的表述标注 [待确认]；
2. 本技能**不制作 PPT**；
3. 项目中的 `AGENTS.md` / `PRD.md` 规则优先于本技能默认值；
4. 不覆盖用户原始文件，改动前先备份；
5. 排版一律用 Word 样式、域、自动编号，禁止用空格/回车模拟缩进、居中、页码、目录。

## 流程总览（S0–S7）

| 阶段 | 内容 | 闸门 |
|---|---|---|
| S0 | 读取项目规则（AGENTS.md / PRD.md） | — |
| S1 | 资产自动探测 + 一次确认 | — |
| S2 | 文献台账 + 草稿诊断 + 大纲建议 | 🚦 闸门1 |
| S3 | 编号映射（草稿号→新号） | 🚦 闸门2 |
| S4 | 模板预检与套用（先于正文） | — |
| S5 | 按模板生成内容初稿，用户通读 | — |
| S6 | 图表与交叉引用 | — |
| S7 | 终稿核对、域更新、交付 | 🚦 闸门3 |

---

## S0 读取项目规则

1. 检查工作区是否有 `AGENTS.md`、`PRD.md`，有则读取并声明"以项目规则为准"；
2. 无则继续，使用本技能内置规范（见 `references/`）。

## S1 资产自动探测 + 一次确认

先探测、后提问，避免逐条盘问：

1. 运行扫描（不创建骨架）：
   ```
   python scripts/init_workspace.py <工作区目录>
   ```
   自动识别已有的文献、模板、草稿、输出文件夹（含 PDF/docx 数量）；
2. 向用户展示"资产盘点表"；
3. 仅对**缺失项**用一次 `interaction.ask` 集中提问（最多 4 问），通常覆盖：
   - 研究方向/大纲/草稿（草稿可直接用，如"初稿综述"文件夹）；
   - 文献库路径（默认原地读取，不复制）；
   - 格式模板（见 S4 决策梯）；
   - 作者信息（姓名、学号、学院专业、指导教师）；
4. 用户确认目录方案后，再运行 `python scripts/init_workspace.py <工作区> --create` 建立标准骨架（已存在目录保留）：
   `01-文献库 / 02-模板库 / 03-初稿 / 04-终稿 / 05-质检文档`。

> 分支：无方向 → 必须先问清研究方向与大纲；无文献 → 请用户放置或指定路径，不得凭空写作。

## S2 🚦 闸门1：台账 + 诊断 + 大纲

**先诊断、后动笔**，材料齐并经用户确认才进入下一步：

1. 需要时提取 PDF 文本：
   ```
   python scripts/extract_pdfs.py <文献目录> <输出目录> --combined corpus.txt
   ```
2. 复制 `assets/ledger-template.xlsx` 到质检目录，按文献逐条建立台账（题录、类型、年卷期、DOI、主题标签、PDF 可得性、出现小节）；
3. 按 `references/outline-rules.md` 输出：
   - 草稿诊断（参考文献表为空、编号错乱、提纲式写法、摘要/关键词超标、章节交叉等）；
   - 大纲调整建议，使用"原问题—调整方案—调整理由"对照表；
4. 提交用户确认；用户不认可的条目不改。

## S3 🚦 闸门2：编号映射

1. 建立"草稿原编号 — 文献台账 — 新编号"映射，新编号按正文首次引用顺序生成；
2. 草稿旧编号一律弃用，不直接沿用；
3. 向用户展示关键映射并等待确认。

## S4 模板预检与套用（先于正文）

模板决策梯（按优先级）：

1. **用户提供模板**（最高优先）；
2. **学校教务处/学院官网**：用浏览器进入官方下载页；需登录则调用 `interaction.request_action` 交回用户；来源链接需用户确认；不使用第三方"论文网站"模板；
3. **通用兜底**：复制 `assets/fallback-template.docx`，并在报告中注明未套用官方模板。

套用（样式值覆盖，不整体替换文档）：

```
python scripts/apply_template.py <模板.docx> <目标.docx>
```

- 自动预检 numbering.xml 的 `numStyleLink/styleLink` 依赖；存在依赖时不搬 numbering，保留目标现有编号；
- 复制页面设置、缺失样式（自动剥离样式中的 numPr）；
- 按模板建立分节：前置部分大写罗马页码、正文阿拉伯数字从 1 起；
- 格式参数见 `references/format-spec.md`。

## S5 按模板生成内容初稿

1. 按确认后的大纲，在已套模板的文档中写作：
   - 提纲标签全部改写为连贯学术段落，段落间有过渡与评述；
   - 术语统一、学术语气，无口语化/宣传化；
   - 按新编号插入顺序编码引用（右上标），著录规则见 `references/gbt7714.md`；
2. 摘要 250–300 字、关键词 3–5 个；
3. 初稿放入 `03-初稿`，请用户通读并收集内容修改意见（此阶段只改内容，不重复套模板）。

## S6 图表与交叉引用

1. 图题在图下、表题在表上，题注样式居中、无首行缩进；
2. 编号用 SEQ 域，正文先引用后出现；"图 N/表 N"用 REF 交叉引用；
3. 表格用三线表（顶线粗、表头下细线、底线粗，无竖线/内部横线）；
4. 架构图/流程图用矢量工具（如 draw.io）绘制，保证清晰可编辑；图表不跨页。

## S7 🚦 闸门3：核对、域更新、交付

1. 引用核对（退出码 1 表示有问题）：
   ```
   python scripts/check_citations.py <论文.docx>
   ```
2. 按 `references/qc-checklist.md` 逐项核对：结构、引用一一对应、著录要素、样式、数据真实性；
3. 抽检关键数据点命中文献原文，确认无编造；
4. 提示用户打开 Word 后 `Ctrl+A` → `F9` 更新域（目录、页码、SEQ/REF）；
5. 交付：
   - `04-终稿/`：论文 docx；
   - `05-质检文档/`：格式检查报告（用 `assets/report-template.md`）、文献台账；
   - 原文件已备份。

---

## 资源地图

### scripts/（确定性操作，直接执行）

| 脚本 | 作用 |
|---|---|
| `init_workspace.py` | 资产探测与标准目录骨架创建（幂等） |
| `extract_pdfs.py` | 批量提取 PDF 文本，支持合并 |
| `apply_template.py` | 模板预检与样式值覆盖（`--dry-run`/`--verbose`） |
| `check_citations.py` | 引用连续性、一一对应、类型标识核对 |

### references/（按需阅读）

| 文档 | 内容 |
|---|---|
| `format-spec.md` | 页面/分节/样式规范、兜底参数、模板典型参数 |
| `gbt7714.md` | 顺序编码制与 GB/T 7714—2015 著录规则 |
| `outline-rules.md` | 综述结构、章节分工、大纲调整规则 |
| `qc-checklist.md` | 终稿质检清单 |

### assets/（用于产出，不读入上下文）

| 文件 | 用途 |
|---|---|
| `fallback-template.docx` | 无官方模板时的通用格式骨架 |
| `ledger-template.xlsx` | 文献台账空白模板 |
| `report-template.md` | 格式检查报告模板 |

## 执行环境

- Python 需具备 `python-docx`、`openpyxl`、`pypdf`；运行前先探测可用解释器，不硬编码路径；
- 技能内文件路径一律使用正斜杠；
- 遵循"先探测 → 约束 → 证据 → 执行 → 验证 → 交付"，三个闸门必须等用户确认。
