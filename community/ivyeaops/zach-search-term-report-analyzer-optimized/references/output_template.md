# 输出契约

report.html 为只读候选报告；details.csv 包含全部词、依据和source_entities；candidates.csv仅筛选候选；summary.json含ASIN、站点、输入模式、明确窗口、记录数、缺失字段、排除行、源文件SHA和阈值。

aggregate输出period_*指标和not_available_aggregate；不输出7d/14d/30d伪窗口。daily输出真实窗口并报告observed_daily_dates，后者不证明报表完整。

status=DONE_WITH_CONCERNS表示产物已生成但仍需人工判断，不代表广告已经操作。business_writes固定0。
