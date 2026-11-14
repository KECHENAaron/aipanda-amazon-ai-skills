#!/usr/bin/env python3
"""Build the static, progressively enhanced beginner page from catalog.json. MIT."""
import argparse
from html import escape
import json

from project_catalog import ROOT, load_catalog

GH = 'https://github.com/KECHENAaron/aipanda-amazon-ai-skills/blob/main/'
CATEGORIES = {'ads': '广告', 'listing': 'Listing', 'research': '竞品研究', 'images': '图片'}
RUNTIMES = {'stdlib': '标准库脚本', 'third_party': '需第三方依赖', 'optional': '可选图像依赖', 'instructions': 'AI 指令工作流'}


def render(data):
    runnable = sum(s['kind'] == 'script' for s in data['skills'])
    runtime_options = ''.join('<option value="' + k + '">' + label + '</option>'
                              for k, label in RUNTIMES.items()
                              if any(s['runtime'] == k for s in data['skills']))
    cards = []
    for s in data['skills']:
        demos = [d for d in data['demos'] if d['skill_id'] == s['id']]
        links = '<a href="' + GH + escape(s['path']) + '/SKILL.md">阅读使用说明 ↗</a>'
        if s['case_page']:
            links += '<a href="' + escape(s['case_page']) + '">看合成案例 →</a>'
        if demos:
            links += '<a href="#demo" data-demo="' + demos[0]['id'] + '">运行合成练习 →</a>'
        cards.append(f'''<article class="skill-card" data-skill="{s['id']}" data-category="{s['category']}" data-runtime="{s['runtime']}">
<div class="tags"><span>{CATEGORIES[s['category']]}</span><span>{RUNTIMES[s['runtime']]}</span><a href="{GH}{escape(s['license_path'])}">{s['license']}</a></div>
<h3>{escape(s['title'])}</h3><p>{escape(s['summary'])}</p><p class="small">{escape(s['dependencies'])}</p><div class="card-links">{links}</div></article>''')
    options = ''.join('<option value="' + d['id'] + '">' + escape(d['title']) + '</option>' for d in data['demos'])
    demos_json = json.dumps([{'id': d['id'], 'preview': d['preview'][5:]} for d in data['demos']], ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="按广告、Listing、竞品与图片任务选择 AIPANDA 技能，区分依赖与许可，用 DEMO_COUNT 个合成练习开始。"><title>开始使用 · AIPANDA</title><link rel="icon" href="assets/avatar.jpg">
<style>*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fbfbfd;color:#17233b;font:16px/1.75 system-ui,-apple-system,"PingFang SC",sans-serif}a{color:#6950c7;text-decoration:none}a:hover{text-decoration:underline}header,main,footer{max-width:1100px;margin:auto;padding:0 26px}header{padding-top:26px;display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap}.brand{font-weight:800;color:#17233b}nav{display:flex;gap:20px;font-size:14px}.hero{padding:60px 0 42px;max-width:760px}h1{font-size:clamp(34px,5vw,52px);line-height:1.25;letter-spacing:-.035em;margin:18px 0}h1 span{color:#6950c7}.eyebrow{font-size:12px;letter-spacing:.1em;color:#6950c7;font-weight:700}.lead,.small{color:#61708a}.lead{font-size:18px}.small{font-size:14px}.steps{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}.steps a{padding:9px 15px;background:#efedf8;border-radius:8px;font-size:14px}section{padding:32px 0;border-top:1px solid #e0e5ee}h2{font-size:28px;margin:0 0 12px}h3{font-size:20px;line-height:1.4;margin:16px 0 10px}.filters{display:flex;gap:16px;flex-wrap:wrap;align-items:end;margin:24px 0 12px}label{display:grid;gap:6px;font-size:14px}select,button{font:inherit;border:1px solid #bcc5d5;background:white;color:#17233b;border-radius:8px;padding:10px 14px;max-width:100%}button{cursor:pointer}select:disabled{color:#61708a}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.skill-card{padding:24px;border:1px solid #dfe4ee;border-radius:14px;background:white}.skill-card[hidden]{display:none}.skill-card p{margin:0 0 14px}.tags{display:flex;gap:7px;flex-wrap:wrap;font-size:11px}.tags span,.tags a{padding:3px 8px;background:#f0edf8;border-radius:20px;color:#6653a4}.card-links{display:flex;gap:12px;flex-wrap:wrap;font-size:14px}.note{padding:18px 22px;background:#f0edf8;border-left:4px solid #a695df;border-radius:0 10px 10px 0;overflow-wrap:anywhere}pre{background:#17233b;color:#e5eafa;border-radius:12px;padding:22px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.9 ui-monospace,SFMono-Regular,monospace}code{overflow-wrap:anywhere}.demo-grid{display:grid;grid-template-columns:1fr 1fr;gap:26px;align-items:start}details{margin:20px 0}summary{cursor:pointer;font-weight:650}footer{padding-top:24px;padding-bottom:36px;font-size:12px;color:#61708a}a:focus-visible,button:focus-visible,select:focus-visible{outline:3px solid #53c7ec;outline-offset:4px}[hidden]{display:none!important}@media(max-width:700px){header,main,footer{padding-left:22px;padding-right:22px}.hero{padding-top:38px}.grid,.demo-grid{grid-template-columns:1fr}.filters label{flex:1 1 145px}.filters select{width:100%}.skill-card{padding:20px}nav{gap:14px}#demo-select{width:100%}}
</style></head><body><header><a class="brand" href="index.html">🐼 AIPANDA · 跨境有AI</a><nav aria-label="页面导航"><a href="cases/index.html">合成案例</a><a href="privacy-review.html">公开复审</a><a href="https://github.com/KECHENAaron/aipanda-amazon-ai-skills">GitHub ↗</a></nav></header><main>
<div class="hero"><div class="eyebrow">START HERE / vVERSION</div><h1>选一个任务，<br><span>先跑通合成练习。</span></h1><p class="lead">7 个技能，各有适用范围。先看任务、运行方式和许可，再用公开样例核对输入与结果。</p><div class="steps"><a href="#choose">① 选择技能</a><a href="#demo">② 跑一个练习</a><a href="#read">③ 读懂结果</a></div></div>
<section id="choose"><div class="eyebrow">01 / CHOOSE</div><h2>你现在要解决什么问题？</h2><p class="small">SCRIPT_SUMMARY社区包各自保留 AGPL-3.0，不按整库 MIT 授权。</p><div class="filters"><label for="task-filter">任务方向<select id="task-filter" disabled><option value="all">全部任务</option><option value="ads">广告</option><option value="listing">Listing</option><option value="research">竞品研究</option><option value="images">图片</option></select></label><label for="runtime-filter">运行方式<select id="runtime-filter" disabled><option value="all">全部方式</option>RUNTIME_OPTIONS</select></label><button id="reset-filters" type="button" hidden>重置筛选</button></div><p id="result-count" class="small" role="status" aria-live="polite">显示 7 / 7 个技能</p><p id="empty-state" class="note" hidden>没有符合这组条件的技能。请切换运行方式，或重置筛选。</p><div class="grid" id="skill-grid">CARDS</div><noscript><p class="small">JavaScript 未启用：全部技能与命令仍可阅读，筛选和示例切换不可用。</p></noscript></section>
<section id="demo"><div class="eyebrow">02 / RUN A SYNTHETIC DEMO</div><h2>一条入口，DEMO_COUNT 个练习。</h2><div class="demo-grid"><div><p>在完整仓库根目录运行，需要 Python 3.9+。统一入口只运行四个原创 MIT 工具的公开常量样例，不接收自有报表、API 或账户信息；3 个社区包仍使用包内命令。</p><label for="demo-select">选择合成练习<select id="demo-select" disabled>OPTIONS</select></label><p class="small"><a id="preview-link" href="demo/report.html">先看对应报告 →</a></p><p class="small">下列命令的默认结果保存在唯一的系统临时目录，运行结束会打印 report.html 路径。每次运行使用新目录，无需覆盖旧结果。</p></div><div><pre><code>git clone https://github.com/KECHENAaron/aipanda-amazon-ai-skills.git
cd aipanda-amazon-ai-skills</code></pre><pre><code id="demo-command">python3 tools/run_demo.py --demo search-terms</code></pre><details><summary>查看全部练习与固定输出目录</summary><pre><code>python3 tools/run_demo.py --list
python3 tools/run_demo.py --demo ads-budget --output-dir outputs/budget-01</code></pre><p class="small">显式输出目录须尚不存在，已有目录会拒绝覆盖。outputs/ 已加入 Git 忽略；临时目录可能被系统清理，需保留时自行另存。若系统使用 python 命令，请用相应的 Python 3 解释器替换 python3。</p></details></div></div></section>
<section id="read"><div class="eyebrow">03 / READ BEFORE ACTING</div><h2>看结果，也看它没有证明什么。</h2><div class="grid"><article class="skill-card"><h3>先核对输入口径</h3><p>检查数据类型、期间、归因成熟度、覆盖和缺失。日粒度、汇总窗口与控制假设是独立协议，不能直接互换；原始 ERP / Amazon 导出不能直接当标准输入。</p><a href="cases/ads-period-review.html">看周期与成熟度反例 →</a></article><article class="skill-card"><h3>候选仍需复核</h3><p>REVIEW_ONLY 是人工复核入口，BLOCKED 保留阻断原因；它们不代表已经批准或执行调整。CPC 不等于当前 Bid，固定乘数不验证动态竞拍，预算不作为每日硬上限。</p><a href="cases/ad-controls.html">看控制情景反例 →</a></article></div><details><summary>怎样提供给 AI 工具？</summary><p>先让 AI 阅读选中技能的 SKILL.md 与相关契约，再运行它自带的合成样例。Listing 和竞品工具只核对结构化输入，人工仍须核对原文含义及实际可比性。需要安装时只复制所选技能完整文件夹，先比较已有同名目录；本页不会修改本机技能或客户端设置。各客户端兼容性需自行核验。</p></details><details><summary>什么时候可以处理自己的资料？</summary><p>先按对应契约在本地整理并验证。真实商品、店铺、成本费用、客户、报表和截图均留在本地；不要提交到 GitHub、Issue 或公共报告。统一演示入口只接受 --list、--demo 与 --output-dir，不提供私有数据上传接口。利润核对不属于公开项目范围。</p></details><p class="note">本项目分享通用技能与完全合成练习，不连接或修改卖家后台。方法、脚本通过离线测试，不代表业务效果已验证。<a href="privacy-review.html">查看公开复审边界 →</a></p></section>
</main><footer>vVERSION · AIPANDA Amazon AI Skills · <a href="catalog.json">机器可读目录</a> · <a href="https://github.com/KECHENAaron/aipanda-amazon-ai-skills/blob/main/NOTICE">许可分区</a> · 独立项目，无平台官方背书。</footer>
<script type="application/json" id="demo-data">DEMOS_JSON</script><script>
const task = document.getElementById('task-filter');
const runtime = document.getElementById('runtime-filter');
const reset = document.getElementById('reset-filters');
const cards = Array.from(document.querySelectorAll('[data-skill]'));
function filterSkills() {
  let count = 0;
  cards.forEach(card => {
    const visible = (task.value === 'all' || card.dataset.category === task.value) && (runtime.value === 'all' || card.dataset.runtime === runtime.value);
    card.hidden = !visible;
    if (visible) count++;
  });
  document.getElementById('result-count').textContent = '显示 ' + count + ' / ' + cards.length + ' 个技能';
  document.getElementById('empty-state').hidden = count !== 0;
}
task.disabled = false; runtime.disabled = false; reset.hidden = false;
task.addEventListener('change', filterSkills); runtime.addEventListener('change', filterSkills);
reset.addEventListener('click', () => {task.value='all'; runtime.value='all'; filterSkills();});
const demos = JSON.parse(document.getElementById('demo-data').textContent);
const select = document.getElementById('demo-select');
function chooseDemo() {
  const demo = demos.find(d => d.id === select.value);
  document.getElementById('demo-command').textContent = 'python3 tools/run_demo.py --demo ' + demo.id;
  document.getElementById('preview-link').href = demo.preview;
}
select.disabled = false; select.addEventListener('change', chooseDemo);
document.querySelectorAll('[data-demo]').forEach(a => a.addEventListener('click', () => {select.value=a.dataset.demo; chooseDemo();}));
</script></body></html>
'''.replace('VERSION', escape(data['project_version'])).replace('CARDS', '\n'.join(cards)).replace('RUNTIME_OPTIONS', runtime_options).replace('OPTIONS', options).replace('DEMOS_JSON', demos_json).replace('DEMO_COUNT', str(len(data['demos']))).replace('SCRIPT_SUMMARY', str(runnable) + ' 个技能均有离线脚本。' if runnable == len(data['skills']) else str(runnable) + ' 个技能有离线脚本。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if the committed page differs from the catalog renderer')
    args = parser.parse_args()
    expected = render(load_catalog())
    target = ROOT / 'docs/start.html'
    if args.check:
        if not target.is_file() or target.read_text(encoding='utf-8') != expected:
            parser.exit(1, 'Beginner page is stale; run python3 tools/build_start_page.py\n')
        print('Beginner page matches catalog.')
    else:
        target.write_text(expected, encoding='utf-8')
        print('Updated docs/start.html')


if __name__ == '__main__':
    main()
