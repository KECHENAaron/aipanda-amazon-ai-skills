---
name: aipanda-search-term-audit
description: 用标准化 SP 日粒度搜索词 CSV 做离线复核，检查重复、缺失、归因成熟与 ACOS，生成带来源行号的 HTML 和 JSON 草稿；适用于搜索词报表分析，不连接广告后台。
---

# AIPANDA 搜索词复核

先读 [输入口径](references/schema.md)。本包自带合成输入和 Python 标准库脚本，可独立复制使用。

确认输入的账户、站点、币种、报告期间、广告类型和归因窗口。仅接受 SP 日粒度标准表；原始 Amazon/ERP 表头需先映射，保留原文件，不猜测近似字段的含义。已有汇总表不可伪造为每日数据。

从技能目录运行：

```bash
python3 scripts/audit.py --input assets/demo.csv --scope assets/demo-scope.json --output-dir /tmp/aipanda-search-term-demo
```

输出目录须尚不存在。业务输入使用新的 scope，标记 `data_kind=user_supplied`。`target_acos` 和 `no_order_spend` 是用户的分析假设；样例值不是通用投放标准，也不是 Amazon 官方建议。`maturity_days` 按实际报告口径与数据更新时间设置。

读回报告再解释：

- 缺失保持未知，不补零。重复或混合范围先返回具体错误，不能一边报错一边沿用旧报告。
- ACOS 的分母是广告归因销售额；不要改称 TACOS。CPC 是历史均价，不是当前 Bid。
- 候选是人工复核入口。控费前还需相关性、自然排名、利润目标及当前关键词/Target 状态。没有这些数据时不生成可执行的否词或竞价指令。
- 报告没有出现的日期或搜索词，不证明它们没有花费。说明覆盖范围和缺口。

交付时指出数据类型、期间、规则假设、待核验项和结果路径。本技能不发送、上传或更改账户数据。
