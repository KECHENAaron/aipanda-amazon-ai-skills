# 图片简报输入

`product`包括asin、marketplace、sku、batch_id；不能确认的值留空。

`facts[]`包括id、field、value、status、asin、sku、batch_id、source_reference。status只在原件核实并正确绑定后填confirmed；它是需负责的证据声明，不是软件鉴真。

`slots[]`：slot（唯一正整数）、role、question、background、subject、text_overlays（字符串数组）、callouts（数组）、forbidden（数组）、style_reference（可选）。默认设计7张，可按需求调整；必须有且只有一个slot=1。

`claims[]`放在每个slot内，字段为text和fact_ids。每个产品参数、数量、效果或限制都应绑定事实。数字和敏感参数文案缺声明时会阻断；脚本不能识别全部语言事实，仍需人工完整核对。

主图background默认#FFFFFF，text_overlays/callouts必须为空；accessories_visible为true时需当前bom_reference。role=comparison需要comparison_evidence；role=real_use需要actual_photo_reference；role=included_items需要bom_reference。没有相应证据可保留阻断槽位，不强凑比较或配件数量。

validate_brief只表明简报是否可进入设计复核；不表示图像成品已生成或平台合规。audit_image只读格式、尺寸及边缘像素，--ocr可用macOS Vision。最终必须人工核对SKU外形、文字、随箱物与当前类目政策。
