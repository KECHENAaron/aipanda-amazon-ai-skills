---
name: zach-search-term-report-analyzer-optimized
description: "分析Amazon搜索词报表，区分逐日与汇总粒度，输出可追溯的分类、观察、控成本及放量候选；用于搜索词报告诊断，不执行广告写入。"
license: "AGPL-3.0 (see LICENSE)"
metadata:
  version: "1.1.0-public.1"
  upstream: "Hector-xue/IvyeaOps@d5e440d7f14ff0444bbde4a890ed39df05876388"
---

# 搜索词分析 · 独立优化版 1.1.0

这是 IvyeaOps 搜索词 Skill 的独立衍生版本，来源见 UPSTREAM.json。原版与旧版保持独立，不加载它们的规则或知识库。

公开整理版：AIPANDA curated 1.1.0-public.1，2026-11-14。保留上游署名与 AGPL-3.0 许可。使用自己的 Python 环境；本包不需要作者机器路径。详见 PUBLIC_CHANGES.md。

## 输入与运行

先核实 ASIN、站点、报告类型、日期范围、币种与归因口径。缺少订单/销售额时保留未知，不当成零订单。pandas、BeautifulSoup、openpyxl 依赖见 requirements.txt；使用已有可用Python或独立虚拟环境，不修改全局解释器。

将 SKILL_DIR 设为本 Skill 实际目录，使用新的运行输出目录：

```bash
python3 "$SKILL_DIR/scripts/run_analysis.py" input.csv --asin B0XXXXXXXX --brand ExampleBrand --mode aggregate --start-date 2026-10-01 --end-date 2026-10-10 --output-dir /tmp/new-search-run
```

- `--mode auto|daily|aggregate`：真实 date 列进入 daily；无日期列用明确窗口进入 aggregate。汇总模式不生成7/14/30天伪趋势。
- `--listing-context-file`：传已获得的页面文字；默认不联网。只有需要公开页面抓取时用 `--live-listing`，失败不替代产品证据。
- `--config config.json`：可配置 thresholds、protected_keywords、competitor_brands、goal。无配置时为 diagnostic；goal记录目标上下文，具体判定由thresholds和target-acos控制，不从阶段名称自动推导财务容忍值。默认阈值仅是待校准的启发式参考。
- `--target-acos`：可用明确目标；不提供时使用报表成本参考线，不当成盈亏点。
- 同一ASIN的不同投放来源在来源字段保留；时间窗用稳定搜索词对齐，匹配方式不作可变连接键。
- 普通高频词不会自动认定竞品品牌。仅把明确 competitor_brands 用于竞品识别；多词品牌仍需人工核对。

## 输出与判断

输出 report.html、details.csv、candidates.csv、summary.json。CSV保留 source_entities；候选需要核对具体投放来源后人工决策。汇总模式只输出 period 指标，不假称30天。

任何控价、否定或放量候选均不是执行指令。缺当前状态、明确目标、完整转化字段或利润证据时，说明影响范围与缺证项。不得把相关性评分、参考ACOS或默认点击门槛当成盈利结论。

作者“不投SBV/不走Vine”等偏好不自动成为用户偏好；本工具也不主动推荐广告执行或评论动作。用户选择的策略只作用于当次配置。

读取 references/decision_rules.md 了解候选边界，references/output_template.md 了解输出字段。源报表字段映射见 references/field_mapping.md。

## 只读数据接入

通过当前实际暴露的 MCP schema 获取数据；领星账户业绩与 SIF/Sorftime 市场观测分开。完成分页并与源汇总对账后才输入。无需读取浏览器凭据、本机密钥或替换配置。缓存快照需标明查询时间、范围与哈希。

## 可复现的公开练习

从本包目录运行。商品、日期和数字全部为合成数据，币种在此练习中约定为 USD；目标 ACOS 25% 仅为演示假设。

```bash
SKILL_DIR="$PWD"
python3 "$SKILL_DIR/scripts/run_analysis.py" "$SKILL_DIR/examples/demo-aggregate.csv" \
  --asin B0DEMO0001 --brand DemoBrand --site US --report-type SP --mode aggregate \
  --start-date 2026-09-01 --end-date 2026-09-12 --target-acos 0.25 \
  --config "$SKILL_DIR/examples/demo-config.json" \
  --listing-context-file "$SKILL_DIR/examples/demo-listing-context.md" \
  --output-dir /tmp/aipanda-community-search-demo
```

预期：4 个输入行；`input_mode=aggregate`；`observed_daily_dates=null`；`candidate_only=true`；`business_writes=0`。不存在每日趋势。`scale_up`、`reduce_bid` 是启发式候选标签，不代表已具备调整条件。使用者还需核实币种、归因成熟度、订单归属、当前 Bid 和利润。
