# 字段映射与粒度

核心字段：search_term、clicks、spend。daily另外需要真实date；aggregate需要明确源窗口。orders、sales、impressions可缺失，但不能用零补齐；非法值停止处理。

支持原Amazon中英文常用表头。CSV和Excel以字符串读取标识符，保留未知与原有精度，数值去除货币符号/千位符后校验。Report Window Start/End用于核对汇总窗口。

ASIN先明确选择并过滤，日期范围明确后过滤。不同来源的币种、归因、商品范围需在取数环节核实。本工具不把接口筛选上下文冒充逐行售出ASIN，也不把累计报表推导成逐日回放。
