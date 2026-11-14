---
name: amazon-asin-cosmo-rufus-audit-optimized
description: "按11板块审计Amazon Listing并生成有证据的改写草稿，核验产品事实冲突、SKU批次绑定和评论覆盖；不用于广告执行或把COSMO推演当官方评分。"
license: "AGPL-3.0 (see LICENSE)"
metadata:
  version: "1.1.0-public.1"
  upstream: "Hector-xue/IvyeaOps@d5e440d7f14ff0444bbde4a890ed39df05876388"
---

# Listing 证据审计 · 独立优化版 1.1.0

保留 IvyeaOps 原版11板块审计与改写模板，独立维护，不读取旧Listing Skill或本机知识库作为隐含规则。来源见 UPSTREAM.json。

公开整理版：AIPANDA curated 1.1.0-public.1，2026-11-14。保留上游署名与 AGPL-3.0 许可。使用自己的 Python 环境；本包不需要作者机器路径。详见 PUBLIC_CHANGES.md。

## 取证与事实表

明确单一ASIN、站点、SKU、材料/部件与当前批次。通过当前可用MCP或用户提供的原件获取标题、正文、属性、图片、评论及业务数据；以实际业务调用验证可用性，不固定要求Claude或Hermes。

每项事实记录字段、值、单位、部件、来源、查询时间和范围。材质、尺寸、承重、年龄、人数、电源、配件和保修等涉及改写的字段，需要已审阅原件与明确SKU/批次绑定；制造商明确适用于当前所有批次的原件可单独声明。未核实不填confirmed。

输入格式见 references/evidence_contract.md。执行：

```bash
python3 "$SKILL_DIR/scripts/audit_evidence.py" --input evidence.json --as-of 2026-10-30 --out /tmp/new-listing-run/evidence_audit.json
```

脚本只核查输入声明、冲突和绑定，不自动证明原件真伪。--strict可在有阻断时返回2，但仍保存审计结果。无需第三方依赖。

## 诊断与改写

先判断曝光、点击、转化或预期错配。按“纠错、补齐、强化、美化”排序。先运行事实检查，再写Title、5 Bullets、后台词、Q&A和图片建议；每个产品事实型表述对应事实ID。冲突或缺失项保留待核实，不择大值、不用旧AI报告替代原件。

评论按评论ID或内容/日期去重；目标变体、其他变体、未知变体分别统计。报告样本时间窗、数量及缺口；不能把样本问题占比叫售后缺陷率。

仍使用 templates/report-template.md 的11板块。7维检查卡是可解释性人工判断，不是Amazon官方算法分数。页面问答推演、实际Rufus测试分别标注；没有实际发问不能称Rufus测试通过。

标题、后台词字节、禁用表达及图文一致性应按当前站点类目规则复核；不要为了补足模板编造产品属性或承诺。无权威规范时写待验证。

## 数据边界

领星/Amazon账户数据可支撑实际花费、订单、当前状态。SIF/Sorftime市场观测、估计与流量不是账户账本。缺利润、当前Bid/预算或因果证据时仅提供条件式测试框架，不输出高置信绝对调整值。

输出用户可读HTML/PDF/工作簿和机器审计JSON；只写草稿，不提交Seller Central、广告或图片后台。所需证据不足不阻止审计，但阻止相应参数进入可发布文案。

## 可复现的公开练习

从本包目录运行，无第三方依赖。

```bash
SKILL_DIR="$PWD"
python3 "$SKILL_DIR/scripts/audit_evidence.py" \
  --input "$SKILL_DIR/examples/demo-evidence.json" --as-of 2026-09-20 \
  --out /tmp/aipanda-community-listing-demo.json
```

预期：材质与尺寸冲突；尺寸文案被阻断；5 条合成评论去重为 4 条，其中目标变体 2 条。`reviewed_original` 也是合成输入中的声明，不表示审阅了真实产品文件。

`references_validated_manual_text_review_required` 只表示引用的事实 ID 可用。程序不理解文案语义，`copy_text_semantics_verified=false`。练习中的“一件”和“十件”都引用 QTY，必须由人发现后者与数量 1 不符。不得把该状态描述为文案真实或可发布。
