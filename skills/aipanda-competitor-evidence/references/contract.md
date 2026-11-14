# 竞品可比性契约 1

## 输入

根字段：schema_version=1、data_kind（synthetic / anonymized_local）、snapshot_date、max_age_days、sources、baseline、entities、observations。来源同 id / observed_date / access，最多 64 个；提供不代表验证原件。max_age_days 为调用者假设，不是统一有效期。

实体至少 2 个、最多 20 个：id（ITEM-A）、variant（VAR-A）、comparison_group（GROUP-A）、pack_count（1–10000 整数或 null）。baseline 必须在实体池中；比较组和绑定仅为输入声明，不证明物理规格相同或覆盖整个市场。

观测至少 1 条、最多 200 条：id（OBS-001）、source_id、entity_id、variant、attribute（ATTR-001）、value、measure_unit、kind（observed / estimated）、method（METHOD-A）、coverage（COVER-A）、window_start、window_end、basis（per_item / per_pack）、aggregation（additive / non_additive）。变体必须与实体绑定一致；窗口起点 ≤ 终点 ≤ 来源观测日期 ≤ 快照日期。

量纲只支持 cm、mm、g、kg、L、mL、count、bool、token；不接收价格、币种、成本或费用字段。值规则与 Listing 包相同：非负有限数、最多 6 位有效小数、count 整数；bool 为布尔，token 为 TOKEN-A；null 不补零。数值最大 10^12。所有编号仅约定代码，不接收商品名、店铺、外链或自由备注。

## 可比门槛

对每个其他实体与基准按属性建立矩阵；任一方缺失或同一实体 / 属性有多条观测时，不自动选一条或聚合。所有观测及来源 ID 保留在报告中。

必须核对比较组、量纲、observed / estimated、method、coverage、起止日期、aggregation，以及来源可用性与使用者声明的新鲜度。任一不一致或未知时返回 NOT_COMPARABLE 并列出理由；不把估算当实际销量，也不由一个维度判断全产品优劣。

统一到 per_item（算术平均每件，不证明每个单件相同；混合包装需人工拆分）：per_pack 数值只有在明确 additive 且包装数已知时才除以包装数。长度、比率、评分等若声明 non_additive 则不除。布尔 / token 只比较 per_item；不自动换算 mm / cm 等量纲。per_item 本身不需要包装数，但仍不证明其他属性可比。

通过时为 COMPARABLE_BY_INPUT，数值采用精确分数，例如 20/3，delta_exact 为对方减基准，relative_change_exact 为差值除基准。基准为 0 时保留差值，相对变化未知并说明 zero_baseline；不是无限增幅。数值原值为十进制字符串，归一及派生值为整数或分数字符串，不使用舍入值决定相等。

## 边界

来源、比较组、包装和方法都是输入声明，未独立验证。相同 kind / method 不证明模型准确；estimated 在报告中仍标记估算。COMPARABLE_BY_INPUT 只覆盖所列单维度，不输出赢家、选品结论、全市场覆盖、销量因果、利润或后台动作。

CLI：scripts/compare.py --input <JSON> --output-dir <新目录>，生成 report.html 与 report.json；已有目录拒绝覆盖。真实输入与匿名报告留在本地；synthetic 标记不替代生成器、来源与脱敏审核。
