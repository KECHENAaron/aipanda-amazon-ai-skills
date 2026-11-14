---
name: aipanda-ads-period-review
description: 对匿名 SP 日报做前后周期复盘，核验覆盖、归因成熟、投放天数和口径，输出加权指标、分单元变化及结构偏移提醒；不用于利润核对或广告执行。
license: MIT
metadata:
  version: "1.0.0"
---

# 匿名广告周期复盘

适用于“这次调整后真的变好了吗”“两个长度不同的周期怎样比”。先按 [输入契约](references/contract.md) 准备本地匿名数据；不直接接收 Amazon、ERP 原始导出。无需第三方依赖、账户、API 或私有知识库。

先按 [通用复盘方法卡](references/review-method.md)明确目标、诊断层级、事件窗口与待验证解释；再用脚本核对可比性。方法卡经授权由课程学习摘要和内部笔记重新组织，不需要访问原知识库。

## 复盘过程

1. 明确同一站点、币种、SP 点击归因、观察对象集合和快照日期。先在本地去除商品、品牌、店铺及真实 ID；使用 UNIT-A 等匿名单元。不同口径分开运行，不按金额或对象比例猜测拆分。
2. 每个日期 × 单元都显式提供一行。缺行、缺指标和异常关系保留为阻断；未出现不等于零。inactive 行要显式提供零或未知，不能编造。
3. 核对归因窗口和用户声明的报表回填等待期。未成熟仍可展示原始摘要，周期变化保持未知。窗口到期不证明来源数据已经最终定稿。
4. 从合计分子分母重算 CTR、CPC、订单 / 点击、ACOS、ROAS；不平均行级比率。总量、日历日均、实际投放日均分开；投放日是该范围内至少一个单元 active=true 的日期，另看分单元构成。
5. 检查分单元结果。汇总 ACOS 改善但全部单元恶化时标记结构偏移。促销、价格、库存、内容、预算或竞价事件仅作混杂背景；相关变化不等于因果效果。
6. 给出数据缺口、可比与不可比项、需要回查的单元和下一轮观察条件。缺当前 Bid、策略或其他必要证据时，不生成竞价、否词或恢复活动指令。该工具没有自动账户接入或写入能力。

## 运行合成练习

在本技能目录运行，输出目录必须尚不存在：

```bash
python3 scripts/review.py --input assets/unequal-days.json --output-dir /tmp/aipanda-period-01
python3 scripts/review.py --input assets/immature.json --output-dir /tmp/aipanda-period-02
python3 scripts/review.py --input assets/mix-shift.json --output-dir /tmp/aipanda-period-03
```

每次输出 report.html 与 report.json。三个输入由 scripts/make_demo.py 中的常量独立生成，无产品名称、商品 ID、搜索词或经营数据来源。所有金额为人工设定的演示数，与任何企业账本无关。

## 公开分享边界与来源

真实数据只留在使用者本地；`anonymized_local` 输出明确标记“不供公开”。声明 synthetic 本身不证明已脱敏，发布前还需重构并审核。不要将真实商品、品牌、店铺、截图、成本费用、账户配置或报表附到仓库或 Issue。

实现与练习为本仓库独立编写，MIT；未搬运原广告包实现、课程原文、知识卡原件或 AGPL 社区代码；通用方法经授权重新编写。公开定义与适用限制见 [来源说明](references/sources.md)。
