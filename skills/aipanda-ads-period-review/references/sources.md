# 来源与许可说明

本技能的说明、代码、测试与合成输入是 AIPANDA 为匿名周期比较独立编写的内容，适用仓库根 MIT。标准算术与描述性比较直接实现；未复制原广告 Skill 的实现、模板、课程原文、知识卡原件或经营案例，也未链接社区包代码。

2026-11-14 核验的公开定义：

| 官方来源 | 用于什么 | 核验边界 |
|---|---|---|
| [Amazon Ads ACOS guide](https://advertising.amazon.com/library/guides/acos-advertising-cost-of-sales) | 广告花费 / 广告归因销售额；ROAS 为相反分子分母；没有适用所有对象的固定良好 ACOS | 已读取公开正文；只转述定义，未复制指南或示例 |
| [Amazon Ads FAQ](https://advertising.amazon.com/resources/faq) | CTR 的点击 / 展示定义及归因概念 | 已读取公开正文；不据此推断具体账户实际窗口 |
| [Amazon Ads attribution help](https://advertising.amazon.com/help/GX7KDKHMWQYMJ385) | 报告日期的归因指标在回溯窗口结束前可能不完整 | 本次可见官方搜索索引摘要；帮助页正文受动态页面限制，实际窗口由使用者核对 |

官方网页作为阅读来源，不随包复制，不据此声称官方背书。日均、汇总分母、匿名输入门槛、结构偏移提醒和非因果边界是本项目的分析设计，非平台规定或投放策略。既有社区 AGPL 包继续保留原许可，不能因新增 MIT 技能而重新授权。

## 经授权重构的方法来源

2026-11-14，用户明确允许将课程与内部知识卡清洗重构后公开。本批的通用方法卡参考了 Apollo 广告课程学习摘要与内部复盘笔记中“先明确目标和广告角色、分层诊断、区分活动与恢复阶段、检验替代解释”的思路，重新组织为独立问题与边界说明。

它们属于学习方法参考，不是 Amazon 官方规定。此处不分发课程原文、讲义图片、专属模板、原知识卡、内部卡片路径或经营案例；也不对这些原作授予本仓库 MIT 许可。公开实现、原创说明与合成生成器独立编写，MIT 仅覆盖本仓库有权授权的表达和实现。不以替换词句代替原实现、素材和模板的许可核查。

## 1.1.0 架构、搜索词与优化方法的来源复核

| 来源背景 | 重新表达后的采用范围 | 没有采用 / 再分发的内容 |
|---|---|---|
| Apollo 广告架构与诊断课程学习摘要 | 先明确流量任务，分层看已披露词与来源贡献；把样本和成熟度分开 | 原图、课件、原知识卡、经营案例、固定预算份额与通用调价天数 |
| Louis 广告结构学习摘要 | 先区分结构问题与竞价问题，用角色说明入口与承接 | 原视频、原讲义、专属表格、具体账户命名或统一出价阈值 |
| 用户授权的内部复盘方法 | 缺失、来源残差、成交保护、承接声明、停止与恢复条件 | 真实产品 / 店铺 / 词 / 数值、原报告、内部卡片路径及配置 |
| [特征词分析公开文章，固定提交](https://github.com/yangyayun2016/tianjikuajing/blob/140e2170958a45379fbbf9c2e997354fd684ae34/blog/general/2026-10-27-amazon-feature-word-analysis-system.md) | 行内去重、相邻符号组、回查完整词与非可加聚合的通用思路 | 原文章文字、实现、表格、示例词、统一归因天数、默认点击门槛或计算出的 Bid |

上述学习资料并非平台规则，也未核为完整课程逐课覆盖。天机公开文章与其仓库根目录在该固定提交未见明确再分发许可，因此仅链接作学习出处，不移植内容或代码；算法按本项目匿名契约重新实现。用户授权允许整理内部学习材料，不表示向读者转授课程原作权利。

2026-11-14 另核对的官方能力来源：

- [Sponsored Products targeting guide](https://advertising.amazon.com/library/guides/targeting-with-sponsored-products)：自动 / 手动、关键词 / 商品投放及否定选项；已读公开正文。
- [Sponsored Products best practices](https://advertising.amazon.com/library/guides/sponsored-products-best-practices)：区分搜索词与投放等报告用途；已读公开正文。

官方网页只作阅读链接，不随包复制。候选门槛、匿名合同、跨源保护、残差阻断、迁移门控及 non_additive 标记是本项目可测试的设计，不是 Amazon 官方策略。符号聚合不验证语言语义；所有业务状态均来自声明，脚本不能证明现场真实或完成后台执行。

## 1.2.0 竞价、预算与广告位来源复核

课程 / 内部学习摘要只提供“先区分结构与价格、按约束分配、保留观察与恢复”的思路。另核对 Apollo 诊断、结构学习摘要与 Louis 策略摘要，重新编写三张方法卡；不复制原文、图表、预算档位、固定份额、建议竞价倍数或“某种策略保证 ACOS”等表述。原资料不随包分发，原作不因本仓库 MIT 再授权。

| 官方阅读来源 | 本次使用范围 | 核验与不采用项 |
|---|---|---|
| [日预算政策与选项公告](https://advertising.amazon.com/resources/whats-new/sponsored-ads-daily-budgeting-policy-and-options) | 平均日预算不是每日硬上限，账户有设置选项 | 2026-11-14 已读公开正文；不同资料中的上浮示例不能硬编成实际账户固定封顶，本脚本不计算保证的日 / 月花费上限 |
| [预算与竞价规则指南](https://advertising.amazon.com/library/guides/budget-rules/) | 规则可能按日程或表现改变配置 | 已读公开正文；不读取、创建、启停规则，不采用文中演示比例 |
| [动态竞价指南](https://advertising.amazon.com/library/guides/dynamic-bidding-sponsored-products) | 动态策略会改变实际竞价 | 已读公开正文；不把动态变化率套入简化固定模型，不默认推荐或关闭某种策略 |
| [rest of search 调整公告](https://advertising.amazon.com/en-gb/resources/whats-new/improve-campaign-performance) | top / rest / product 是可区分的投放位置，调整适用范围需核对 | 已读公开正文；输入 0–900 只是模型覆盖范围，不宣称验证了账户上限或功能可用性 |
| [广告位调整帮助](https://advertising.amazon.com/help/GYYZVM7LGSRYGWV5) | 固定基础竞价与位置加价的例子，其他类型加价可能叠加 | 本次可见官方索引摘要；正文受动态页面限制，实际规则与账户配置仍需现场核对 |

固定乘数、目标成本 CPC 参考、声明预算约束、单变量门控与用户边界检查均为本项目重新实现的演示设计，非平台推荐值。CPC 参考不是利润或盈亏模型。当前 / 提议值来自输入，不是脚本生成的推荐价；全部候选不可执行，真实状态未独立核实。
