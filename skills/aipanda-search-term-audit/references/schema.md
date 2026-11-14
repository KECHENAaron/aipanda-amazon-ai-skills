# 标准 CSV 与 scope

Python 3.9+，不需要第三方依赖。`demo.csv` 完全合成，不代表任何真实店铺的表现。

每行是一条日粒度 SP 搜索词记录。字段名固定为：

| 类型 | 字段 |
|---|---|
| 期间 | date，ISO 日期 |
| 范围 | profile_id、marketplace、currency、ad_type、attribution_window |
| 对象 | campaign_id、ad_group_id、target_id、match_type、search_term |
| 指标 | impressions、clicks、spend、orders、sales |

除指标外字段不可空。指标留空表示未知；展示、点击、订单是非负整数，金额是非负数字。不解析千分位和币种符号，清洗时需保留审计依据。

所有维度加日期共同构成唯一键。CSV 不能混入账户汇总行、总计行、不同站点或归因窗口。相同搜索词跨不同 Target 的合法明细可汇总，但不能把复制的同一行当新增数据。

scope 中五个范围字段必须与每行一致。起止日期包括边界。`as_of` 是本次数据快照/分析日期；`maturity_days` 是人为明确的归因成熟假设，不是实时官方规则。日期有一行未成熟，该词进入等待状态。

`target_acos` 是小数比例，如 0.25；`no_order_spend` 按 scope 币种计。脚本优先处理缺数和矛盾，再处理成熟度，最后给复核候选。没有订单但花费低于自设线时保持观察。

每个派生比率在分子缺失或分母为零/缺失时为 null。汇总有任一缺失时该指标总计为 null，已知的其他指标可以独立汇总。无订单花费不是已证实的“浪费金额”。

源行号是输入 CSV 的物理行号，包含第 1 行表头。输出保留范围、源行号和观测日期；HTML 将用户输入转义，不执行输入文本。
