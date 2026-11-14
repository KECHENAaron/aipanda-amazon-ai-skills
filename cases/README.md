# AIPANDA 实务问题重构案例

[在线案例库](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/) · [本批筛选记录](../docs/curation.md)

这些案例保留真实工作里遇到的问题结构，重新构造公开输入，不复制真实经营资料。商品、品牌、ASIN、SKU、评论、日期与数字均为合成设定。它们不展示真实账户业绩，也不证明收益改善。

| 案例 | 问题与可复现结果 | 输入 / 输出 |
|---|---|---|
| [汇总报表不能长出每日趋势](../docs/cases/aggregate-window.html) | 12 天无日期明细 → aggregate，只保留 period 指标 | [CSV](../docs/cases/data/demo-aggregate.csv) / [报告](../docs/cases/data/search/report.html) |
| [参数冲突先阻断](../docs/cases/listing-conflicts.html) | 材质与尺寸争议；评论去重与变体分母分别保留 | [输入](../docs/cases/data/demo-evidence.json) / [审计](../docs/cases/data/listing-audit.json) |
| [引用正确不等于文意正确](../docs/cases/copy-reference.html) | 同一个 QTY 引用可写出“一件”或“十件”；输出明确需人工审文意 | [反例](../docs/cases/data/demo-evidence.json) / [回归测试](../community/ivyeaops/amazon-asin-cosmo-rufus-audit-optimized/tests/test_evidence.py) |
| [简报检查与图片验收分开](../docs/cases/image-brief.html) | 4 槽位阻断 → 2 槽位设计草稿；生成和上传均为 0 | [原简报](../docs/cases/data/demo-brief-blocked.json) / [修订结果](../docs/cases/data/brief-revised-audit.json) |

## 如何复现

在 [社区包目录](../community/ivyeaops/README.md) 选择单个包，按其 SKILL.md 的“可复现的公开练习”运行。无需 API Key 或真实账户。搜索词包需要显式安装 requirements.txt；Listing 和简报校验使用 Python 标准库，像素检查另需 Pillow。

汇总口径、产品冲突与图片简报问题来自本机既有只读实务验证；其原始报表、原产品资料、图片及私有证据路径保持私有。第三个案例是本次源码审阅发现并修正的输出语义问题。每个页面说明程序验证了什么、没有验证什么。

案例文字为 AIPANDA 原创整理，适用根 MIT。`docs/cases/data/` 内含社区工具生成的结果，整体按该目录保留的 AGPL-3.0 分发，完整对应源码位于 `community/ivyeaops/`；请勿将整个仓库统称为 MIT。
