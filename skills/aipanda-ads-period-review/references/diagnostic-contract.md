# 架构与搜索词诊断输入 v1

这是本项目自定义的匿名汇总协议，非 Amazon 导出格式。使用 diagnose.py；原 review.py 的两期日报协议保持不变。所有对象均字段白名单，未知字段拒绝；不接收商品、店铺、真实搜索词、实际投放 ID、成本、费用、备注或 URL。

根字段：schema_version=1、data_kind（synthetic / anonymized_local）、scope、window、thresholds、units、terms、rows、controls、existing_negatives。

- scope 与原周期契约相同：匿名 SCOPE-001，支持的站点 / 币种，SP、click 归因、显式归因天数和回填等待期。
- window：start_date、end_date、snapshot_date；窗口最多 366 天，start ≤ end ≤ snapshot。这里只接受一个汇总窗口，不能产生逐日趋势。归因成熟按声明天数核对，并非确认源报表已经最终定稿。
- thresholds：target_acos、min_clicks、min_orders、review_spend，全部显式为正；min_clicks 与 min_orders 为整数。它们是演示或本地分析配置，不是自动操作线。
- units：unit（UNIT-A 等）、role（discovery / harvest / defense / product / unknown）、match（auto / broad / phrase / exact / product）、state（enabled / paused）、ownership（exclusive / shared / unknown）、budget_headroom（yes / no / unknown）、negative_list_complete（布尔）。这些字段是输入声明，不是实时状态验证。
- terms：term（TERM-A 等）、kind（query / product_target）、tokens（TOKEN-A 等匿名符号序列）、relevance（relevant / irrelevant / unknown）、protected（布尔）、owner（某个 UNIT 或 null）、owner_continuity_declared（布尔）。query 必须有符号；product_target 必须无符号。不接受自然语言。
- rows：row_id（ROW-001 等）、unit、term 与 impressions / clicks / spend / orders / sales。同一窗口同一 UNIT × TERM 唯一；本地需先映射成唯一匹配来源。整数计数、非负有限指标与未知 null 的约束沿用原协议。
- controls：每个 UNIT 恰好一条同范围控制摘要：unit 和五个指标。残差=控制摘要减已披露行合计；未知、负残差、正残差与矛盾关系分别列出，均阻断有关候选。不编造缺失搜索词，不混加原控制表和搜索词表。
- existing_negatives：unit、term、kind（exact / phrase / product）。重复项拒绝；商品与关键词类型须适配。phrase 项只触发人工语义复核，本包不模拟平台 close variant 或真实 phrase 命中。

输出包含匿名架构、角色份额、控制残差、完整 TERM 及来源、逐行诊断、候选、阻断原因、单符号与相邻双符号视图。候选的 REVIEW_ONLY 仅表示声明条件未产生阻断；所有候选 executable=false、live_state_independently_verified=false。词根视图 non_additive=true，不能加成控制总量。

数据缺失不会补零。任一来源转化未知或矛盾，会阻断普通否定；已有成交与显式保护优先。迁移另核承接和来源样本，来源有成交时仍阻断；不存在机械的自动 / 广泛 → 精确迁移。
