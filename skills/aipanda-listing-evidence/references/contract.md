# Listing 结构化声明契约 1

## 输入

根字段只允许 schema_version=1、data_kind（synthetic / anonymized_local）、snapshot_date、max_age_days（0–3650 整数）、sources、facts、claims。每组至多 200 个事实 / 声明、64 个来源。来源和事实可空，以保留缺证；声明至少 1 条。未知字段、重复 ID / JSON 键、未来来源、非法值会拒绝，不回显输入值。

来源为 id（SRC-001）、observed_date、access（provided / unavailable）。provided 表示调用者提供了材料，不代表程序访问或验证过原件。max_age_days 为使用者的复核假设，不是通用有效期。

事实字段：id（EV-001）、source_id、unit（UNIT-A）、variant（VAR-A）、batch（BATCH-A）、component（PART-ALL）、attribute（ATTR-001）、condition（COND-A）、value、measure_unit。声明用 id（CLAIM-001）与相同六个绑定字段、value、measure_unit、evidence_ids；没有 source_id。编号只允许约定前缀及 1–12 个大写字母或数字；不接收自由备注、商品名、店铺、链接、自然语言文案或费用字段。

measure_unit 只允许 cm、mm、g、kg、L、mL、count、bool、token。数值非负、最多 6 位有效小数且不大于 10^12；count 必须整数，bool 必须 JSON 布尔值，token 值为 TOKEN-A 形式。事实 value=null 保持未知，声明 value 不可空。不同量纲不自动换算，比较为精确相等，不做近似容差或区间推断。数值输出保留为十进制字符串，避免展示舍入。

## 状态与来源范围

以对象、变体、批次、部件、属性、条件六元绑定查找**输入中所有匹配事实**，不只看被引用的支持材料。未提交给程序的外部反证仍不可见。

- CONFLICT：可用的匹配来源值彼此不一致，即使未被引用也保留冲突。
- CONTRADICTED：可用来源一致，但声明值与其不同。
- MISSING_EVIDENCE：没有匹配事实；MISSING_CITATION：有匹配事实但没有明确引用。
- NOT_APPLICABLE：引用绑定错位，不能转给另一变体 / 批次 / 条件。
- REVIEW_REQUIRED：来源不可用、过旧、值未知、量纲不同或没有可用的引用。
- SUPPORTED_BY_INPUT：引用和输入事实在本契约内一致，不代表自然语言句子真实、原件真实或可以直接上架。

多条问题可能并存，状态先保留已知冲突 / 反证，细节另列引用、匹配事实与理由。只在 SUPPORTED_BY_INPUT 返回 draft_value；这是结构化值，不是自动生成的英文文案。copy_semantics_verified、source_authenticity_verified 和 executable 始终 false。

## 人工与运行边界

先在本地把原句拆成原子声明，并核验每个代码与实际对象、条件的对应；映射不随公共包分发。脚本不会理解“一件 / 十件”、认证措辞、兼容性或隐含范围；人工还须回看原句及政策。它不生成官方评分、完整合规结论、图片、Listing 提交或执行 payload。

CLI：scripts/audit.py --input <JSON> --output-dir <新目录>。结果为 report.html / report.json，包含完整匿名来源与事实账本。已有目录拒绝覆盖；读取或校验失败不输出成功报告。anonymized_local 报告标记“不供公开”。只有生成器重建、来源及脱敏审核均通过的合成输入和输出才能发布。
