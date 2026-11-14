# AIPANDA 完全合成案例

[在线案例库](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/) · [公开分享规范](../docs/curation.md)

这些练习独立构造通用数据与验证边界，不映射任何实际商品或经营资料。商品、品牌、ASIN、SKU、评论、日期与数字均为合成设定。它们不展示真实账户业绩，也不证明收益改善。

| 案例 | 问题与可复现结果 | 输入 / 输出 |
|---|---|---|
| [汇总报表不能长出每日趋势](../docs/cases/aggregate-window.html) | 12 天无日期明细 → aggregate，只保留 period 指标 | [CSV](../docs/cases/data/demo-aggregate.csv) / [报告](../docs/cases/data/search/report.html) |
| [参数冲突先阻断](../docs/cases/listing-conflicts.html) | 材质与尺寸争议；评论去重与变体分母分别保留 | [输入](../docs/cases/data/demo-evidence.json) / [审计](../docs/cases/data/listing-audit.json) |
| [引用正确不等于文意正确](../docs/cases/copy-reference.html) | 同一个 QTY 引用可写出“一件”或“十件”；输出明确需人工审文意 | [反例](../docs/cases/data/demo-evidence.json) / [回归测试](../community/ivyeaops/amazon-asin-cosmo-rufus-audit-optimized/tests/test_evidence.py) |
| [简报检查与图片验收分开](../docs/cases/image-brief.html) | 4 槽位阻断 → 2 槽位设计草稿；生成和上传均为 0 | [原简报](../docs/cases/data/demo-brief-blocked.json) / [修订结果](../docs/cases/data/brief-revised-audit.json) |
| [匿名广告周期复盘](../docs/cases/ads-period-review.html) | 3 个完全合成练习：总量与日均、未成熟阻断、聚合结构偏移 | [技能](../skills/aipanda-ads-period-review/SKILL.md) / [合成生成器](../skills/aipanda-ads-period-review/scripts/make_demo.py) |
| [广告架构与搜索词诊断](../docs/cases/ads-diagnostics.html) | 3 组合成练习：架构缺口、成交保护 / 符号聚合、有条件迁移 | [诊断契约](../skills/aipanda-ads-period-review/references/diagnostic-contract.md) / [常量生成器](../skills/aipanda-ads-period-review/scripts/make_diagnostic_demo.py) |
| [竞价预算广告位情景](../docs/cases/ad-controls.html) | 4 组合成练习：Bid、预算、位置与多变量反例 | [控制协议](../skills/aipanda-ads-period-review/references/control-contract.md) / [常量生成器](../skills/aipanda-ads-period-review/scripts/make_control_demo.py) |
| [Listing 声明证据核对](../docs/cases/listing-evidence.html) | 支持、未引用冲突、绑定 / 量纲 / 来源反例 | [独立 Skill](../skills/aipanda-listing-evidence/SKILL.md) |
| [竞品可比性核对](../docs/cases/competitor-evidence.html) | 精确包装归一、窗口 / 方法差异、未知与多来源 | [独立 Skill](../skills/aipanda-competitor-evidence/SKILL.md) |

## 如何复现

匿名周期与架构 / 搜索词练习见 [独立 MIT 技能](../skills/aipanda-ads-period-review/SKILL.md)。其他结构化练习在 [社区包目录](../community/ivyeaops/README.md) 选择单个包，按其 SKILL.md 的“可复现的公开练习”运行。无需 API Key 或真实账户。搜索词包需要显式安装 requirements.txt；Listing 和简报校验使用 Python 标准库，像素检查另需 Pillow。

所有公开输入均为合成练习；不包含经营对象映射、原始资料或私有证据路径。引用反例用于演示程序验证范围。每个页面说明程序验证了什么、没有验证什么。

案例文字为 AIPANDA 原创整理，适用根 MIT。`docs/cases/data/` 内含社区工具生成的结果，整体按该目录保留的 AGPL-3.0 分发，完整对应源码位于 `community/ivyeaops/`；请勿将整个仓库统称为 MIT。

广告复盘的 `docs/cases/ads-period-review/` 、`docs/cases/ads-diagnostics/` 和 `docs/cases/ad-controls/` 目录为独立 MIT 内容，不属于社区 AGPL 数据目录。

新 Listing 与竞品的 `docs/cases/listing-evidence/`、`docs/cases/competitor-evidence/` 为独立原创 MIT 内容，不属于 AGPL data 目录。
