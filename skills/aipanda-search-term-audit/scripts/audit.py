#!/usr/bin/env python3
"""Offline SP search-term review of explicitly normalized daily CSV. Python 3.9+."""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from html import escape
import json
from pathlib import Path

METRICS = ('impressions', 'clicks', 'spend', 'orders', 'sales')
DIMENSIONS = ('profile_id', 'marketplace', 'currency', 'ad_type', 'attribution_window')
IDENTITY = ('date',) + DIMENSIONS + ('campaign_id', 'ad_group_id', 'target_id', 'match_type', 'search_term')


def number(value, integer=False):
    if value is None or not str(value).strip():
        return None
    try:
        result = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ValueError('指标必须是非负数字或留空') from exc
    if not result.is_finite() or result < 0 or (integer and result != result.to_integral_value()):
        raise ValueError('指标包含非法值、负数或非整数计数')
    return result


def ratio(a, b):
    return a / b if a is not None and b is not None and b > 0 else None


def serial(value):
    if isinstance(value, Decimal):
        return float(round(value, 6))
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serial(item) for item in value]
    return value


def analyze(input_path, scope):
    required = set(DIMENSIONS) | {'start_date', 'end_date', 'as_of', 'maturity_days', 'target_acos', 'no_order_spend', 'data_kind'}
    if required - scope.keys():
        raise ValueError('scope 缺少字段: ' + ', '.join(sorted(required - scope.keys())))
    start, end, as_of = (date.fromisoformat(scope[key]) for key in ('start_date', 'end_date', 'as_of'))
    if start > end or end > as_of:
        raise ValueError('日期范围必须满足 start_date <= end_date <= as_of')
    if scope['ad_type'] != 'SP' or scope['data_kind'] not in ('synthetic', 'user_supplied'):
        raise ValueError('仅接受 SP 日粒度标准表，data_kind 必须明确标记')
    lag = scope['maturity_days']
    if isinstance(lag, bool) or not isinstance(lag, int) or lag < 0:
        raise ValueError('maturity_days 必须是非负整数，由报告口径确定')
    target, stop = (number(scope[key]) for key in ('target_acos', 'no_order_spend'))
    if target is None or stop is None or target <= 0 or stop <= 0:
        raise ValueError('target_acos 与 no_order_spend 必须大于零')
    for key in DIMENSIONS:
        if not isinstance(scope[key], str) or not scope[key].strip():
            raise ValueError('scope 维度不能为空: ' + key)
    seen, groups, observed_dates, count = set(), {}, set(), 0
    with Path(input_path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        needed = set(IDENTITY + METRICS)
        if not reader.fieldnames or needed - set(reader.fieldnames):
            raise ValueError('CSV 缺少标准字段: ' + ', '.join(sorted(needed - set(reader.fieldnames or []))))
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('CSV 表头重复')
        for line, row in enumerate(reader, 2):
            if None in row:
                raise ValueError(f'第 {line} 行列数超过表头')
            row = {key: value.strip() if value is not None else '' for key, value in row.items()}
            if any(not row[key] for key in IDENTITY):
                raise ValueError(f'第 {line} 行维度字段为空')
            day = date.fromisoformat(row['date'])
            if not start <= day <= end:
                raise ValueError(f'第 {line} 行超出期间范围')
            if any(row[key] != scope[key] for key in DIMENSIONS):
                raise ValueError(f'第 {line} 行与账户/站点/币种/广告类型/归因窗口不一致')
            key = tuple(row[field] for field in IDENTITY)
            if key in seen:
                raise ValueError(f'第 {line} 行维度重复；请核对报表重叠或重复导入')
            seen.add(key)
            values = {field: number(row[field], field in ('impressions', 'clicks', 'orders')) for field in METRICS}
            item = dict(values, date=day.isoformat(), source_line=line, mature=(as_of - day).days >= lag)
            groups.setdefault(row['search_term'], []).append(item)
            observed_dates.add(day.isoformat())
            count += 1
    if not count:
        raise ValueError('CSV 无数据行')
    results = []
    for term, rows in groups.items():
        totals = {field: sum((r[field] for r in rows), Decimal(0)) if all(r[field] is not None for r in rows) else None for field in METRICS}
        gaps = [field for field, value in totals.items() if value is None]
        issues = []
        for r in rows:
            if r['clicks'] is not None and r['impressions'] is not None and r['clicks'] > r['impressions']:
                issues.append('点击高于展示')
            if r['clicks'] == 0 and r['spend'] is not None and r['spend'] > 0:
                issues.append('零点击却有花费')
            if r['orders'] == 0 and r['sales'] is not None and r['sales'] > 0:
                issues.append('零订单却有归因销售额')
        derived = {
            'ctr': ratio(totals['clicks'], totals['impressions']),
            'cpc': ratio(totals['spend'], totals['clicks']),
            'cvr': ratio(totals['orders'], totals['clicks']),
            'acos': ratio(totals['spend'], totals['sales']),
            'roas': ratio(totals['sales'], totals['spend']),
        }
        if gaps or issues:
            state, reason = '数据待核验', '缺失指标或指标矛盾，先回查来源'
        elif not all(row['mature'] for row in rows):
            state, reason = '等待归因成熟', '部分日期尚未达到 scope 设定的成熟期'
        elif totals['orders'] == 0 and totals['spend'] >= stop:
            state, reason = '控费复核候选', '成熟期内无订单且达到自设花费线；先核相关性与目标，再决定动作'
        elif totals['orders'] > 0 and derived['acos'] is not None and derived['acos'] <= target:
            state, reason = '效率复核候选', 'ACOS 在自设目标内；仍需核利润、预算、当前竞价和自然排名'
        elif totals['orders'] > 0:
            state, reason = '经济性复核候选', '有订单；结合毛利、目标及流量结构复核成本'
        else:
            state, reason = '继续观察', '当前证据不足以支持控费判断'
        results.append(dict(search_term=term, metrics=totals, derived=derived, state=state, reason=reason,
                            missing_metrics=gaps, issues=sorted(set(issues)), source_lines=[r['source_line'] for r in rows],
                            dates=[r['date'] for r in rows]))
    totals = {field: sum((item['metrics'][field] for item in results), Decimal(0)) if all(item['metrics'][field] is not None for item in results) else None for field in METRICS}
    return serial({'scope': scope, 'row_count': count, 'observed_dates': sorted(observed_dates),
                   'coverage_note': '仅覆盖所提供数据行；未出现的日期/搜索词不是零表现或完整覆盖的证明。',
                   'totals': totals, 'items': results,
                   'boundary': '离线分析草稿；候选不是执行指令。未获取当前 Bid、利润、自然排名或后台状态；不会连接账户或修改广告。'})


def render(report):
    def value(v):
        return '未知' if v is None else f'{v:,.2f}'
    cards = ''.join(f'<div><small>{escape(k)}</small><strong>{value(v)}</strong></div>' for k, v in report['totals'].items())
    rows = []
    for item in report['items']:
        metrics = item['metrics']
        acos = item['derived']['acos']
        evidence = ', '.join(map(str, item['source_lines']))
        rows.append('<tr>' + ''.join(f'<td>{escape(str(v))}</td>' for v in [item['search_term'], item['state'], value(metrics['spend']), value(metrics['orders']), value(metrics['sales']), '未知' if acos is None else f'{acos:.1%}', item['reason'], evidence]) + '</tr>')
    scope = escape(json.dumps(report['scope'], ensure_ascii=False, indent=2))
    data_label = '合成数据演示' if report['scope']['data_kind'] == 'synthetic' else '用户提供数据 · 本地分析'
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AIPANDA 搜索词复核</title><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#f5f7fb;color:#142338;font:15px/1.65 system-ui,sans-serif}}main{{max-width:1200px;margin:auto;padding:36px 24px}}h1{{font-size:30px}}.label{{color:#7356be;font-weight:700}}.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}}.cards div{{background:white;border:1px solid #dae1ed;border-radius:12px;padding:16px;min-width:140px}}strong,small{{display:block}}strong{{font-size:24px}}.table{{overflow-x:auto;background:white;border:1px solid #dae1ed;border-radius:12px}}table{{border-collapse:collapse;width:100%;min-width:900px}}td,th{{padding:14px;text-align:left;border-bottom:1px solid #e5eaf2}}th{{background:#edf1fa}}pre{{white-space:pre-wrap;background:#eaf0f8;border-radius:10px;padding:20px}}.note{{color:#52627a}}a{{color:#6052ad}}</style>
    <main><div class="label">AIPANDA · {data_label}</div><h1>先看证据，再决定下一步。</h1><p>{escape(report['boundary'])}</p><div class="cards">{cards}</div><div class="table"><table><thead><tr><th>搜索词</th><th>状态</th><th>花费</th><th>订单</th><th>归因销售额</th><th>ACOS</th><th>复核理由</th><th>CSV 行号</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div><p class="note">{escape(report['coverage_note'])} 汇总中任一输入缺失，该指标总计显示“未知”。ACOS 按广告归因销售额计算，与 TACOS 不同。</p><details><summary>数据范围与分析假设</summary><pre>{scope}</pre></details><p class="note">v0.1.0 · 本地生成 · 无网络调用</p></main></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--scope', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error('output-dir 已存在；请选择新目录，避免覆盖')
    try:
        report = analyze(args.input, json.loads(args.scope.read_text(encoding='utf-8')))
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    args.output_dir.mkdir(parents=True)
    (args.output_dir / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    (args.output_dir / 'report.html').write_text(render(report), encoding='utf-8')
    print('已生成本地复核草稿: ' + str(args.output_dir))


if __name__ == '__main__':
    main()
