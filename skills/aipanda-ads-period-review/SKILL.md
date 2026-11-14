---
name: aipanda-ads-period-review
description: 匿名 SP 广告复盘，覆盖周期比较、架构搜索词及竞价 / 预算 / 广告位假设检查；保留来源、残差与阻断，不用于利润核对或后台执行。
license: MIT
metadata:
  version: "1.2.0"
---

# 匿名广告复盘 · 1.2.0

适用于周期变化、广告结构混乱、搜索词诊断或优化候选复核。先按 [通用复盘方法](references/review-method.md)明确目标，再选择工作流。Python 标准库即可运行，不需要 API、付费账户或私有知识库；不直接兼容原始导出。

| 任务 | 阅读与运行 |
|---|---|
| 两期真的改善了吗 | [周期契约](references/contract.md)，scripts/review.py；总量 / 两种日均 / 归因成熟 / 分单元变化 |
| 结构哪里不清楚 | [架构方法](references/architecture-method.md)；明确角色、控制范围、独占归属及 owner |
| 搜索词怎样分层 | [搜索词方法](references/search-term-method.md)；完整 TERM 与源 UNIT、成交保护、符号聚合 |
| 什么优化暂时不能做 | [优化方法](references/optimization-method.md)；候选、证据缺口、迁移承接与恢复观察 |
| 竞价、预算和广告位如何试验 | [竞价](references/bid-method.md)、[预算](references/budget-method.md)、[广告位](references/placement-method.md)；把历史表现、声明配置与提议分开 |
| 运行控制情景检查 | [控制协议](references/control-contract.md)，scripts/control_scenarios.py；只核对调用者提出的假设 |
| 运行结构与搜索词检查 | [诊断契约](references/diagnostic-contract.md)，scripts/diagnose.py；汇总窗口、残差、候选与阻断 |

## 从方法到可复核结果

先锁定同一范围、期间、币种和归因口径。真实对象与匿名标签的对应关系只保留在本地，公开包不接收实际商品、店铺、搜索词或成本费用信息。三种契约独立，不能把 SQP、SB / SD 或不同归因报告混作 SP。

周期模式显式覆盖每日 × 单元，不从缺失造零。诊断模式只接受一个汇总窗口，不推断逐日趋势；以独立源单元的控制摘要比较已披露词，差额单列，不造“其他词”。词根 / 双词视图不可相加当总额。

相关性、归属、余量、否定表完整与持续承接都是输入声明，程序未独立核实。保护已观察到的成交与显式保护词；其他来源转化未知也会阻断普通否定。迁移分别核对来源与承接，不能机械从自动 / 广泛转精确。

脚本只产生复核问题和条件候选，所有候选 executable=false。REVIEW_ONLY 不是批准或实时后台就绪；周期和搜索词协议不接收当前 Bid；新控制协议只接受声明配置与调用者假设，仍不由历史 CPC 自动生成推荐价。缺失、矛盾、归因未成熟、共享归属、已暂停或承接不明都保留相应阻断。

## 运行十个完全合成练习

在本技能目录运行；输出目录必须尚不存在。每次输出 report.html 与 report.json。

```bash
python3 scripts/review.py --input assets/unequal-days.json --output-dir /tmp/aipanda-period-01
python3 scripts/review.py --input assets/immature.json --output-dir /tmp/aipanda-period-02
python3 scripts/review.py --input assets/mix-shift.json --output-dir /tmp/aipanda-period-03
python3 scripts/diagnose.py --input assets/diagnostic-architecture.json --output-dir /tmp/aipanda-diagnostic-01
python3 scripts/diagnose.py --input assets/diagnostic-term-safety.json --output-dir /tmp/aipanda-diagnostic-02
python3 scripts/diagnose.py --input assets/diagnostic-optimization.json --output-dir /tmp/aipanda-diagnostic-03
python3 scripts/control_scenarios.py --input assets/control-bid.json --output-dir /tmp/aipanda-control-01
python3 scripts/control_scenarios.py --input assets/control-budget.json --output-dir /tmp/aipanda-control-02
python3 scripts/control_scenarios.py --input assets/control-placement.json --output-dir /tmp/aipanda-control-03
python3 scripts/control_scenarios.py --input assets/control-joint-change.json --output-dir /tmp/aipanda-control-04
```

输入由 make_demo.py、make_diagnostic_demo.py 与 make_control_demo.py 的常量生成，不读取经营资料。UNIT / TERM / TOKEN 是匿名符号；金额只是演示设定，不能映射企业表现。实际自然语言、词形与 phrase 否定的语义必须另行人工核验。

控制模式区分历史 CPC、基础竞价与固定乘数情景；需要同活动、互斥广告位、日级覆盖与范围对账。动态策略、混合基础竞价和其他加价不计算单一竞拍上限；平均日预算也不是保证的每日花费上限。多变量变更阻断本脚本的单变量试验候选，详见控制协议。

## 来源与公开边界

[来源说明](references/sources.md)区分官方定义、课程 / 知识卡学习背景和本项目工程设计。经授权重写通用方法，不附原课件、专属模板、知识卡原件或内部路径；原作不因本项目 MIT 获得再授权。新实现未搬运外部代码，也不导入社区 AGPL 包。

只分享完全合成练习。真实输入与匿名本地报告留在本地，anonymized_local 输出标记“不供公开”；synthetic 声明不等于已经完成脱敏。不得上传真实商品、店铺、截图、成本费用、客户、经营报表或内部配置到仓库 / Issue。利润核对和业务后台操作不属于本 Skill。
