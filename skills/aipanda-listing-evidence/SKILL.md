---
name: aipanda-listing-evidence
description: 按匿名原子声明核对来源、变体批次条件、冲突与缺证，离线输出 HTML / JSON；不验证自然语言语义、不提交 Listing。
license: MIT
metadata:
  version: "1.0.0"
---

# Listing 证据复核 · 1.0.0

Python 3.9+ 标准库独立运行，先读 [输入契约与状态](references/contract.md)，再运行随包合成样例。无需 API、账户或私有知识库；不直接读取原始 Amazon / ERP 导出。

把原句在本地拆为可验证声明，绑定对象、变体、批次、部件、属性与条件。程序扫描全部已输入的匹配事实，保留未引用反证；支持值只表示结构化输入一致，人工仍须核对原文含义、测试范围和原件。关键词不能增加事实。

从本技能目录运行，输出目录须尚不存在：

```bash
python3 scripts/audit.py --input assets/supported.json --output-dir /tmp/aipanda-listing-evidence-1
python3 scripts/audit.py --input assets/conflicts.json --output-dir /tmp/aipanda-listing-evidence-2
python3 scripts/audit.py --input assets/boundaries.json --output-dir /tmp/aipanda-listing-evidence-3
```

每次生成 report.html 与 report.json，先读回状态、理由和完整匿名证据账本。没有英文文案自动生成、官方评分、完整政策合规或后台提交。

[来源与许可](references/sources.md)区分既有 MIT 方法、官方阅读背景和原创协议；不复制原课程、知识卡或社区 AGPL 实现。三个输入由 scripts/make_demo.py 的常量生成，不读取经营资料；只允许代码标签与有限类型值，不接收真实商品名、店铺、成本费用、外链或自由备注。真实对应表留在本地，anonymized_local 报告不供公开。synthetic 声明仍需生成器与人工复审。

本包含完整 MIT LICENSE 和独立脚本；复制单包即可。程序输出始终不可执行，来源真实性和业务判断需另行核实。利润核对不属于本技能。
