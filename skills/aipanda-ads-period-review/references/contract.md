# 匿名输入契约 v1

仅支持 Python 3.9+、SP、click 归因、显式日粒度与两个不重叠的 before / after 窗口。根对象与嵌套对象均使用字段白名单，未知字段直接拒绝。它是本项目自定义的交换格式，不代表 Amazon 报表或 API schema。

- 根字段：schema_version=1、data_kind（synthetic 或 anonymized_local）、scope、snapshot_date、units、periods、rows、events。
- scope：scope_token 使用 SCOPE-001 形式；marketplace / currency 为受支持代码；ad_type=SP；attribution_basis=click；attribution_days 为 1–90 整数；reporting_lag_days 为 0–30 整数。后两项必须按自己的实际报告声明，没有统一平台默认值。
- units：唯一的 UNIT-A 等匿名标签；两期使用同一集合。标签对应关系只保留在本地，不附产品信息。
- periods：恰好两个对象，各含 period、start_date、end_date。before 结束早于 after 开始，每窗最长 366 天，结束日期不晚于快照。
- rows：period、date、unit、active（布尔）以及 impressions、clicks、spend、orders、sales。每期每个日历日期 × 单元都须一行；全部缺失或指标留 null 会阻断比较，绝不补零。重复键拒绝。
- 指标：0 至 10^18 范围内的有限数（本工具的技术输入界限，不是平台限制）；impressions / clicks / orders 为整数；null 表示未知。比率采用合计分子 / 合计分母，分母 0 为 null。点击高于展示、零点击有花费、零订单有销售额、inactive 却有非零指标都需要回查，阻断比较。
- events：每项只有 period、date、kind。kind 为 promotion、price_change、availability_change、content_change、bid_change、budget_change 之一，不接收备注、名称、URL 或自由文本。

输出包含两期总计、比率、日历日均、实际投放日均、分单元结果、源行号、数据问题、阻断原因与变化。成熟条件为快照距窗口末日不小于 attribution_days + reporting_lag_days；这是输入约定下的检查，仍须回查源报表状态。订单 / 点击是本工具采用的描述性比值，不宣称与所有平台报表 CVR 定义相同。

COMPARABLE_DESCRIPTIVE 只表示通过本契约的可比性检查。BLOCKED_COMPARISON 下原始数据可见，变化值为 null。相对变化的旧值为 0 或未知时也为 null。

不接收 ASIN、SKU、品牌、商品标题、账户 / 店铺名、搜索词、采购成本、服务费用、利润、自然单或总店铺销售等字段。不支持跨币种、不同归因、SB / SD、逐订单归属、利润核对、TACOS 或因果推断。未来扩展应另建契约和测试。
