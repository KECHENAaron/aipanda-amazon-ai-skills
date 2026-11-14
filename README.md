<div align="center">
  <img src="assets/avatar.jpg" width="220" alt="AIPANDA 熊猫头像">
  <h1>🐼 AIPANDA · 跨境有AI</h1>
  <p><strong>AIPANDA Amazon AI Skills</strong></p>
  <p>把亚马逊运营经验，变成可复用的 AI 技能、工具与实战工作流。</p>
  <p><a href="https://kechenaaron.github.io/aipanda-amazon-ai-skills/">项目主页</a> · <a href="#十分钟开始">快速开始</a> · <a href="#技能目录">技能目录</a> · <a href="https://kechenaaron.github.io/aipanda-amazon-ai-skills/demo/report.html">报告样例</a> · <a href="docs/roadmap.md">后续计划</a></p>
</div>

面向亚马逊卖家与使用 AI 的运营人员。从一个具体问题出发，保留输入、来源、判断理由与可复现结果。

**当前版本：0.5.0。** 共 7 个技能入口：4 个 MIT 技能与 3 个保留 AGPL-3.0 的社区衍生包；5 个有离线脚本，2 个是指令型工作流。配套 [7 个完全合成案例主题](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/)，其中广告复盘包含周期比较、架构 / 搜索词诊断、竞价 / 预算 / 广告位情景三组，共 10 个独立练习。只分享通用技能，不展示实际商品、店铺或经营资料。

**许可分区：基础版 MIT；`community/ivyeaops/` 与 `docs/cases/data/` 保留 AGPL-3.0。** 来源、版本与修改逐包记录，品牌图片另见 [NOTICE](NOTICE)。

## 技能目录

| 技能 | 输入与交付 | 当前状态 |
|---|---|---|
| [搜索词复核](skills/aipanda-search-term-audit/SKILL.md) | 标准 SP 日粒度 CSV → 带来源行号的 HTML / JSON 草稿 | Python 工具，可离线运行 |
| [Listing 证据复核](skills/aipanda-listing-evidence/SKILL.md) | 产品事实＋文案 → 逐条证据状态与改写理由 | 指令型技能，含合成练习 |
| [竞品证据对标](skills/aipanda-competitor-evidence/SKILL.md) | 竞品资料 → 同口径矩阵、机会与缺口 | 指令型技能，含合成练习 |

工具当前只接受已经按仓库字段规范整理的 CSV，不直接兼容所有 Amazon、ERP 或广告导出格式。

## 独立维护的社区技能

以下是 [IvyeaOps 固定版本](https://github.com/Hector-xue/IvyeaOps/tree/d5e440d7f14ff0444bbde4a890ed39df05876388) 的独立优化公开副本，保留作者署名与完整 AGPL 许可。逐包带源码、测试、合成输入、依赖和改动记录，使用前见 [社区包说明](community/ivyeaops/README.md)。

| 技能 | 能做什么 | 可复现案例 |
|---|---|---|
| [搜索词进阶分析](community/ivyeaops/zach-search-term-report-analyzer-optimized/SKILL.md) | 显式字段映射、daily / aggregate、候选与来源实体 | [汇总粒度](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/aggregate-window.html) |
| [Listing 结构化证据审计](community/ivyeaops/amazon-asin-cosmo-rufus-audit-optimized/SKILL.md) | 部件 / SKU / 批次冲突、引用校验、评论去重与变体分母 | [参数冲突](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/listing-conflicts.html) / [文意反例](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/copy-reference.html) |
| [图片简报与技术筛查](community/ivyeaops/amazon-listing-creative-optimized/SKILL.md) | 卖点 / 配件证据、简报阻断、可选 Pillow / OCR | [简报到验收](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/image-brief.html) |

**工具检查有范围。** 引用 ID 有效不等于文案文意正确；白色像素不等于整图合规；启发式候选不等于可以执行的广告调整。三个包均不包含业务写入脚本。标准库基础版与社区包的输入协议、依赖和许可分别说明。

[公开分享规范](docs/curation.md) · [版本变化](CHANGELOG.md) · [完整案例目录](cases/README.md)

## 广告复盘：周期、搜索词与控制情景

[技能与契约](skills/aipanda-ads-period-review/SKILL.md) · [周期 3 个练习](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/ads-period-review.html) · [公开来源与许可](skills/aipanda-ads-period-review/references/sources.md)

Skill 1.2.0 保留 [架构、搜索词与优化候选的 3 个合成练习](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/ads-diagnostics.html)。Python 标准库实现，从相同匿名单元的 SP 日报比较两期：覆盖、归因成熟、总量与两种日均、加权比率、分单元变化及结构偏移。字段白名单拒绝商品 / 店铺 / 成本 / 备注等额外字段，不做利润核对，不输出竞价或否词操作。

```bash
python3 skills/aipanda-ads-period-review/scripts/review.py \
  --input skills/aipanda-ads-period-review/assets/unequal-days.json \
  --output-dir /tmp/aipanda-period-demo
```

结构与搜索词模式使用 `scripts/diagnose.py`，入口、独立契约、方法及演示命令见 SKILL.md。

新增 [竞价、预算、广告位与联合改动 4 个合成练习](https://kechenaaron.github.io/aipanda-amazon-ai-skills/cases/ad-controls.html)，使用 `scripts/control_scenarios.py` 检查调用者假设，不从历史 CPC 自动产生推荐 Bid。固定乘数模型与平均日预算均保留适用边界。

仅用常量合成的公开练习可供分享；匿名本地报告标记“不供公开”，不要提交到仓库或 Issue。

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

本版默认离线运行，不连接卖家账户，不修改广告或 Listing。社区搜索词包可选抓取公开商品页，需使用者明确选择；默认关闭。历史 CPC 不等于当前 Bid；ACOS 不等于 TACOS；离线草稿不代表后台已执行或收益已提升。

本仓库原创基础代码和文档采用 [MIT](LICENSE)；`community/ivyeaops/` 和 `docs/cases/data/` 按各目录保留的 AGPL-3.0 分发，完整对应源码随仓库提供。不可将整库代码统称为 MIT。品牌图片另见 [NOTICE](NOTICE)。

Independent project for Amazon sellers. Not affiliated with or endorsed by Amazon, Walmart, or TikTok. Third-party marks remain with their respective owners.
