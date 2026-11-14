# 事实与文案输入

`product`：asin、marketplace、sku；涉及批次关键参数时提供batch_id。

`sources[]`：id、kind、reference、observed_at、asin、marketplace、sku、batch_id、verification。只有人工已经审阅原件时才填`verification: reviewed_original`。reference是源文件、原始页面或可回溯材料标识，不能填旧AI结论作为制造商原件。制造商明确覆盖当前全部批次时可填`applies_to_all_current_batches: true`；这仍是需人工负责的证据声明。

`claims[]`：id、field、value、unit、component、source_id、asin。field采用material、dimensions、total_load、individual_load、max_users、age_range、voltage、wattage、included_quantity、warranty、certification等；仅填本次涉及字段。不同部件的材质分别标component，不能把组成材料简单视为同一事实。不同单位未换算前保留待核实；没有明确总承重不能用单人限重乘人数推导。

`copy_claims[]`：id、location、text、fact_ids（对应claims.id）。可发布事实型表达要求对应事实无冲突、已核实且与当前范围绑定。没有引用的表达被标记待审阅。

`required_fields[]`：本次任务需要的字段；不把所有产品都要求有认证、保修等字段。

`reviews[]`：id、asin、date、rating、text、topics。asin只在评论明确绑定子ASIN时填写，尺寸或款式描述不足以确认材质批次；不明则保留未知。topics是可追溯的人工/模型主题标注，不等于缺陷率。

输出包含facts状态、缺证原因、文案阻断项和去重后的评论范围。confirmed表示输入证据声明满足约束，不表示脚本独立鉴真。需要审计来源本身时另外人工回读。
