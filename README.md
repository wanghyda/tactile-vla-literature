# Tactile + VLA Literature

触觉（tactile）与视觉-语言-动作模型（VLA）机器人研究的持续更新文献库。

本仓库优先收录：

- 2024 年以来的触觉-VLA、视觉-触觉-语言-动作（VTLA）和接触感知策略；
- 有公开 arXiv / 会议页面 / DOI 的真实论文；
- 有官方代码、数据集或项目页的可复现工作；
- 触觉表征学习、触觉世界模型、灵巧操作和高影响 VLA 基线。

## 目录

- [按主题浏览](#按主题浏览)
- [精选论文](papers/README.md)
- [完整索引](papers/index.csv)
- [BibTeX](sources/references.bib)
- [本地已收集文献](sources/local-collection.md)
- [待核验候选](sources/candidates.md)
- [更新机制](#更新机制)

## 按主题浏览

| 主题 | 入口 |
|---|---|
| 直接触觉-VLA / VTLA | [papers/tactile-vla.md](papers/tactile-vla.md) |
| 触觉表征、基础模型与传感器 | [papers/tactile-representation.md](papers/tactile-representation.md) |
| 触觉策略、灵巧操作与接触控制 | [papers/tactile-manipulation.md](papers/tactile-manipulation.md) |
| VLA 基线与开放模型 | [papers/vla-foundations.md](papers/vla-foundations.md) |
| 综述、数据集与基准 | [papers/surveys-datasets.md](papers/surveys-datasets.md) |

## 评价口径

`status` 区分同行评审版本与 arXiv 预印本；`verification` 记录是否通过 arXiv 元数据或官方页面核验；`quality` 是面向阅读优先级的主观标签，不等同于官方评分或引用数。对 2026 年论文默认标为 `preprint`，除非有独立的会议/期刊页面。

仓库只保存元数据、链接、分类和简短阅读笔记，不上传受版权保护的 PDF。`sources/local-collection.md` 记录本机已有 PDF 的位置，便于本地阅读和去重。

## 更新机制

- GitHub Actions 每周运行一次 `tools/update_arxiv.py`，查询 arXiv 最新触觉-VLA候选并更新 `sources/arxiv-candidates.json`。
- 自动更新只追加候选，不自动提升论文的质量或验证状态；人工核验后再加入正式索引。
- 手动更新：`python tools/update_arxiv.py --output sources/arxiv-candidates.json`

## 贡献

欢迎提交遗漏论文、修正作者/venue/代码链接或补充阅读笔记。请优先引用论文的 arXiv、DOI、会议官网和作者官方代码仓库。

