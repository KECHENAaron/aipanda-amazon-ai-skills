# IvyeaOps 社区衍生技能 · AIPANDA 公开整理版

三个彼此独立、可整目录复制的本机优化包，来自 [Hector-xue/IvyeaOps 固定版本](https://github.com/Hector-xue/IvyeaOps/tree/d5e440d7f14ff0444bbde4a890ed39df05876388)，保留作者署名与各包完整的 **AGPL-3.0** 许可。这些包不适用仓库根目录的 MIT 授权。

| 包 | 交付能力 | 依赖 |
|---|---|---|
| [搜索词分析](zach-search-term-report-analyzer-optimized/SKILL.md) | 逐日/汇总 CSV，字段归一化、投放来源、条件式候选 | pandas、BeautifulSoup、openpyxl，见 requirements.txt |
| [Listing 证据审计](amazon-asin-cosmo-rufus-audit-optimized/SKILL.md) | 事实冲突、SKU/批次绑定、评论去重与变体分母 | Python 标准库 |
| [图片简报质检](amazon-listing-creative-optimized/SKILL.md) | 图像简报、声明与配件证据、像素检查 | 简报为标准库；像素检查需 Pillow；可选 OCR 需 macOS Swift/Vision |

从仓库根目录运行各自测试：

```bash
python3 -m unittest discover -s community/ivyeaops/zach-search-term-report-analyzer-optimized/tests -v
python3 -m unittest discover -s community/ivyeaops/amazon-asin-cosmo-rufus-audit-optimized/tests -v
python3 -m unittest discover -s community/ivyeaops/amazon-listing-creative-optimized/tests -v
```

依赖可在自己的虚拟环境中安装。例如进入搜索词包目录后：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

此后用 `.venv/bin/python` 代替该包示例中的 `python3`。Listing 与简报校验无需这一步；像素检查按图片包 requirements.txt 安装。所有命令均在使用者自己的环境运行。

与仓库基础版相同，均不会修改广告、商品或图片后台。新装技能时先检查是否已有同名文件夹，不自动覆盖已有版本。

## 与基础版如何选

`skills/aipanda-search-term-audit` 适合已经整理好的 SP 日粒度标准 CSV，零第三方依赖；本社区搜索词包支持更多表头和汇总口径，但阈值是待校准的启发式规则，不等于已验证利润线。币种、报表范围、归因成熟、当前 Bid 和经营目标仍须在输入前明确；不能把历史 CPC 变成当前出价指令。

Listing 审计只验证输入声明、来源绑定和冲突；**事实引用有效，不等于文案语义真实**。图片技术检查也不等于实际出图或平台审核通过。

公开版本移除了机器环境路径和旧的预生成文件，替换了本机案例标识，并提供新的合成练习；各包 `PUBLIC_CHANGES.md` 记录整理内容。学习案例见 [案例索引](../../cases/README.md)。
