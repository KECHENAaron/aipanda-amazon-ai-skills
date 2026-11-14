<div align="center">
  <img src="assets/avatar.jpg" width="220" alt="AIPANDA 熊猫头像">
  <h1>🐼 AIPANDA · 跨境有AI</h1>
  <p><strong>AIPANDA Amazon AI Skills</strong></p>
  <p>把亚马逊运营经验，变成可复用的 AI 技能、工具与实战工作流。</p>
  <p><a href="https://kechenaaron.github.io/aipanda-amazon-ai-skills/">项目主页</a> · <a href="#十分钟开始">快速开始</a> · <a href="#技能目录">技能目录</a> · <a href="https://kechenaaron.github.io/aipanda-amazon-ai-skills/demo/report.html">报告样例</a> · <a href="docs/roadmap.md">后续计划</a></p>
</div>

面向亚马逊卖家与使用 AI 的运营人员。从一个具体问题出发，保留输入、来源、判断理由与可复现结果。

**当前版本：0.1.0。** 包含 1 个可运行的离线分析工具，以及 2 个可供 AI 使用的证据工作流与合成练习。示例全部为合成数据，未展示真实店铺成绩。

## 技能目录

| 技能 | 输入与交付 | 当前状态 |
|---|---|---|
| [搜索词复核](skills/aipanda-search-term-audit/SKILL.md) | 标准 SP 日粒度 CSV → 带来源行号的 HTML / JSON 草稿 | Python 工具，可离线运行 |
| [Listing 证据复核](skills/aipanda-listing-evidence/SKILL.md) | 产品事实＋文案 → 逐条证据状态与改写理由 | 指令型技能，含合成练习 |
| [竞品证据对标](skills/aipanda-competitor-evidence/SKILL.md) | 竞品资料 → 同口径矩阵、机会与缺口 | 指令型技能，含合成练习 |

工具当前只接受已经按仓库字段规范整理的 CSV，不直接兼容所有 Amazon、ERP 或广告导出格式。

## 十分钟开始

需要 Python 3.9+，无需安装第三方依赖。

```bash
git clone https://github.com/KECHENAaron/aipanda-amazon-ai-skills.git
cd aipanda-amazon-ai-skills
python3 skills/aipanda-search-term-audit/scripts/audit.py \
  --input skills/aipanda-search-term-audit/assets/demo.csv \
  --scope skills/aipanda-search-term-audit/assets/demo-scope.json \
  --output-dir /tmp/aipanda-search-term-demo
```

打开输出目录的 `report.html`，或阅读 `report.json`。输出目录必须尚不存在；再次运行时请换一个新目录。

样例包含四种不同情况：成熟期内无订单且达到自设花费线、有效率的有订单词、证据不足的观察词，以及点击缺失的数据待核验词。缺失不会补为零。

`target_acos=0.25` 与 `no_order_spend=20` 仅为合成演示假设，不是建议所有账户采用的投放标准。详细输入与计算边界见 [schema](skills/aipanda-search-term-audit/references/schema.md)。

## 在 AI 工具中使用

将所需的单个技能文件夹提供给支持读取 `SKILL.md` 的 AI 工具，或直接让 AI 阅读对应文件。各技能自带必要的指令、示例或脚本。

Codex 用户可手动将选中的技能文件夹复制到自己的 `~/.codex/skills/`；已有同名文件夹时先比较内容，避免覆盖。其他客户端请按各自当前文档设置；本项目未逐一完成兼容性测试。

可尝试：

> 使用 aipanda-search-term-audit，先运行仓库合成样例，解释候选分类、数据缺口和归因口径，不执行广告调整。

## 为什么这样做

- **保留依据。** 结果能追到输入行与数据范围。
- **承认未知。** 缺数、矛盾、估算与真实零值分开表达。
- **让建议可复核。** 报告输出候选和理由，业务动作另行决定。
- **便于复现。** 从合成数据开始，运行分析无需 API Key 或付费账户。

关于开发、检查与贡献，见 [贡献指南](CONTRIBUTING.md)。想了解选题，见 [路线图](docs/roadmap.md)；有关第三方项目的学习导航，见 [公开参考](docs/references.md)。

## 范围与许可

本版本不连接卖家账户，不获取实时数据，不修改广告或 Listing。历史 CPC 不等于当前 Bid；ACOS 不等于 TACOS；离线草稿不代表后台已执行或收益已提升。

本仓库新编写的代码和文档采用 [MIT](LICENSE)。品牌图片另见 [NOTICE](NOTICE)。

Independent project for Amazon sellers. Not affiliated with or endorsed by Amazon, Walmart, or TikTok. Third-party marks remain with their respective owners.
