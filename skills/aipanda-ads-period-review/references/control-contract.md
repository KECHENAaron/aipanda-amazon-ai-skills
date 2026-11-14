# 竞价、预算、广告位情景协议 v1

使用 scripts/control_scenarios.py。它核对调用者提供的配置假设，不从报告计算推荐 Bid，不接受原始导出。原周期和搜索词协议保持独立。所有对象字段白名单，不接收商品、店铺、真实对象 ID、成本、费用、自然语言备注或 URL。

根字段：schema_version=1、data_kind（synthetic / anonymized_local）、unit（UNIT-A 等）、scope、window、context、current、proposal、guardrails、daily、placements。

- scope 沿用 SP / click、匿名 SCOPE-001、站点 / 币种、明确归因天数与回填等待期。
- window：start_date、end_date、snapshot_date；最多 31 天，start ≤ end ≤ snapshot。
- context：configuration_as_of；state（enabled / paused）；ownership（exclusive / shared / unknown）；relevance（supported / unknown）；capacity（adequate / limited / unknown）；observation_status（stable / recent_change / unknown）；strategy（fixed / dynamic_down_only / dynamic_up_down / rule_based / unknown）；other_bid_adjustments 与 budget_rules（none_declared / present / unknown）；bid_basis（single_or_uniform_declared / mixed / unknown）；performance_scope（campaign_declared / partial_or_unknown）；placement_partition（exclusive_three_declared / unknown）。全部为输入声明，未独立核实；stable 应表示观察窗口与当前配置背景没有未披露的变更。
- current / proposal：base_bid、average_daily_budget、placement_pct（top / rest / product，数值 25 表示 25%）。前两项为正；百分比为 0–900，仅为本模型技术范围，不是账户权限或平台限制验证。proposal 是使用者提出的假设，不是脚本建议。
- guardrails：target_acos、min_clicks、min_orders、max_base_bid、max_average_daily_budget、max_placement_adjusted_bid。全部显式为正，计数为整数。边界约束整个提议配置，不只约束变化项；都不是自动操作授权、利润线或保证的花费上限。
- daily：窗口内每个日历日一行，date、budget_exhausted（布尔 / null）和五指标 impressions / clicks / spend / orders / sales。日期重复拒绝；缺日不补零。未知和矛盾保留问题。
- placements：top / rest / product 各一行，placement 与五指标；必须声明为互斥、同活动、同窗口，合计与 daily 相符。额外 / 重复位置拒绝；缺失、差额或未知阻断候选。

数据指标与数字范围沿用原协议；本情景模型的数值输入最多 6 位小数，超出会拒绝，避免被输出舍入成零。派生结果保留最多 8 位小数，不作为账本精度或平台金额规则。成熟检查仍由声明的归因与等待天数决定，不能证明源报告最终定稿。

输出分别呈现历史 CPC、目标成本 CPC 参考、声明基础竞价、各位历史表现、固定情景算术、平均日预算与预算约束日期。CPC 参考=目标 ACOS × 广告销售额 / 订单 × 订单 / 点击；分母无效时未知，不作为盈亏点或建议 Bid。

单一 / 统一基础竞价、fixed 且无其他加价声明时，计算各位置 base × (1 + pct/100)。混合 Bid、动态或其他调整时不计算单一出价情景；预算候选仍可能依据观测复核，但不得据此声称动态 Bid 上限已验证。

逐个变化变量输出 BLOCKED / REVIEW_ONLY。多个原子变量（基础竞价、预算或各个广告位）同时变化会阻断本脚本的单变量试验候选。所有候选 executable=false、live_state_independently_verified=false；不存在执行 payload。平均日预算的 daily_budget_is_hard_cap 和 spend_cap_guaranteed 始终为 false。
