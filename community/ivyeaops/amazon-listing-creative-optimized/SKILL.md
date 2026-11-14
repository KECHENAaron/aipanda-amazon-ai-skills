---
name: amazon-listing-creative-optimized
description: "为Amazon主图与辅图制作按品类选择的设计简报，核验卖点证据、SKU配件和图像技术质量；不承担广告调价或把简报当已生成图片。"
license: "AGPL-3.0 (see LICENSE)"
metadata:
  version: "1.1.0-public.1"
  upstream: "Hector-xue/IvyeaOps@d5e440d7f14ff0444bbde4a890ed39df05876388"
---

# Listing 图片创意 · 独立优化版 1.1.0

基于IvyeaOps原版7槽位简报独立优化，不调用旧素材采集Skill，不包含广告调价或评论策略。来源见 UPSTREAM.json。

公开整理版：AIPANDA curated 1.1.0-public.1，2026-11-14。保留上游署名与 AGPL-3.0 许可。使用自己的 Python 环境；本包不需要作者机器路径。详见 PUBLIC_CHANGES.md。

## 先绑定产品事实

明确ASIN、站点、SKU、批次、实际外观和随箱物。只使用有权限的实拍/页面证据。材质、尺寸、承重、年龄、人数、电气参数、配件数量、认证和保修需要明确事实引用；旧照片或文件夹名称不能自动证明当前批次。

## 按购买疑问选择槽位

默认保留7张规划，但不硬套摄像头App或效果样张。每张回答一个不同购买疑问，例如：主图识别、布局/功能、真实尺寸与场地、实际使用、安装与电源、细节/限制、随箱清单。根据品类调整顺序与数量。没有竞品证据不制作优劣比较；没有App不创造App功能。

每张简报保留：Slot、Background、Subject、Text overlays、Callouts、Forbidden、Style reference，另记录question、role、claims/fact_ids。比较、真实效果及配件分别需要comparison_evidence、actual_photo_reference、bom_reference。

主图按当前站点/类目官方规范核验；默认白底、不叠加文字徽章、不展示未包含物。删除“小NEW例外”。正面、侧面和45°作为候选构图，通过实际表现选择，不保证某角度总赢。副图短文案以移动端可读为准。

输入格式见 references/brief_contract.md。

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" --input brief.json --out /tmp/new-image-run/brief_check.json
python3 "$SKILL_DIR/scripts/audit_image.py" actual.jpg --main --out /tmp/new-image-run/image_check.json
```

图像检查需要Pillow。可选 --ocr 使用macOS自带Swift/Vision提取文字，无额外服务。OCR失败或不可用须保留状态；OCR不能证明数字或卖点真实。

## 设计和验收

只要求策划时交付简报，不自动生成图片。需要实际出图时使用当前已授权图像工具，并逐张核对实物身份、文字/数字、配件、人体与场景、移动端可读性，最后检查整套风格一致性。

边缘白像素、格式、分辨率只能技术筛查，不能自动宣称背景、产品占比、Amazon合规或实物一致已通过。最后保留人工复核。仅在用户授权的范围内生成或上传；本Skill不包含上传脚本。

输出HTML/PDF或实际图片及验收JSON；分别报告简报、生成、OCR、人工复核和上传状态。照片效果/示范必须来自实际产品，不伪造使用结果。

## 可复现的公开练习

从本包目录运行。简报检查仅需 Python 标准库；实际像素检查另需 `requirements.txt` 中的 Pillow。

```bash
SKILL_DIR="$PWD"
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --input "$SKILL_DIR/examples/demo-brief-blocked.json" \
  --out /tmp/aipanda-brief-blocked.json
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --input "$SKILL_DIR/examples/demo-brief-revised.json" \
  --out /tmp/aipanda-brief-revised.json
```

前者 4 个槽位均被阻断；后者为 2 个槽位的 `BRIEF_CHECKED_DRAFT`，仍需设计与人工验收。两者均为 `generated_images=0`、`uploaded_images=0`，不表示已经出图。
