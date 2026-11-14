---
name: aipanda-competitor-evidence
description: 按匿名实体和观测核对量纲、窗口、方法、包装与可比性，离线输出证据矩阵 HTML / JSON；不作市场赢家或利润结论。
license: MIT
metadata:
  version: "1.0.0"
---

# 竞品证据对标 · 1.0.0

Python 3.9+ 标准库独立运行，先读 [输入契约与状态](references/contract.md)，再运行随包合成样例。无需 API、账户或私有知识库；不直接读取原始 Amazon / ERP 导出。

先说明比较池与比较组依据，再提供同维度观测。程序保留来源、时间、实测 / 估算、范围与缺口；同口径通过也不证明全产品等价或市场覆盖。按包装归一化只适用于明确可加的数值，未知不补零。人工仍须核对实际规格及方法。

从本技能目录运行，输出目录须尚不存在：

```bash
python3 scripts/compare.py --input assets/normalized.json --output-dir /tmp/aipanda-competitor-evidence-1
python3 scripts/compare.py --input assets/scope-mismatch.json --output-dir /tmp/aipanda-competitor-evidence-2
python3 scripts/compare.py --input assets/missing.json --output-dir /tmp/aipanda-competitor-evidence-3
```

每次生成 report.html 与 report.json，先读回状态、理由和完整匿名证据账本。没有英文文案自动生成、官方评分、完整政策合规或后台提交。

[来源与许可](references/sources.md)区分既有 MIT 方法、官方阅读背景和原创协议；不复制原课程、知识卡或社区 AGPL 实现。三个输入由 scripts/make_demo.py 的常量生成，不读取经营资料；只允许代码标签与有限类型值，不接收真实商品名、店铺、成本费用、外链或自由备注。真实对应表留在本地，anonymized_local 报告不供公开。synthetic 声明仍需生成器与人工复审。

本包含完整 MIT LICENSE 和独立脚本；复制单包即可。程序输出始终不可执行，来源真实性和业务判断需另行核实。利润核对不属于本技能。
