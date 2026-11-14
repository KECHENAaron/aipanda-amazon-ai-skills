#!/usr/bin/env python3
"""Anonymous, offline SP period review. Original AIPANDA implementation; MIT."""
import argparse
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from html import escape
import json
import math
from pathlib import Path
import re

METRICS = ('impressions', 'clicks', 'spend', 'orders', 'sales')
RATIOS = {'ctr': ('clicks', 'impressions'), 'cpc': ('spend', 'clicks'),
          'order_per_click': ('orders', 'clicks'), 'acos': ('spend', 'sales'), 'roas': ('sales', 'spend')}
EVENTS = {'promotion', 'price_change', 'availability_change', 'content_change', 'bid_change', 'budget_change'}


def exact(obj, keys):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError('invalid_or_unexpected_fields')


def day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('invalid_date')
    return date.fromisoformat(value)


def integer(value, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError('invalid_integer_setting')
    return value


def number(value, count=False):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError('invalid_metric')
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('invalid_metric') from exc
    if not n.is_finite() or n < 0 or n > Decimal("1e18") or (count and n != n.to_integral_value()):
        raise ValueError('invalid_metric')
    return n


def ratio(a, b):
    return a / b if a is not None and b is not None and b > 0 else None


def summarize(rows, complete):
    totals = {k: sum((r[k] for r in rows), Decimal(0))
              if complete and all(r[k] is not None for r in rows) else None for k in METRICS}
    return dict(totals=totals, ratios={k: ratio(totals[a], totals[b]) for k, (a, b) in RATIOS.items()})


def serial(x):
    if isinstance(x, Decimal):
        v = float(x)
        if not math.isfinite(v):
            raise ValueError("metric_out_of_output_range")
        return round(v, 8)
    if isinstance(x, dict):
        return {k: serial(v) for k, v in x.items()}
    if isinstance(x, list):
        return [serial(v) for v in x]
    return x


def review(data):
    exact(data, ('schema_version', 'data_kind', 'scope', 'snapshot_date', 'units', 'periods', 'rows', 'events'))
    if type(data['schema_version']) is not int or data['schema_version'] != 1 or data['data_kind'] not in ('synthetic', 'anonymized_local'):
        raise ValueError('unsupported_schema_or_data_kind')
    s = data['scope']
    exact(s, ('scope_token', 'marketplace', 'currency', 'ad_type', 'attribution_basis', 'attribution_days', 'reporting_lag_days'))
    if not isinstance(s['scope_token'], str) or not re.fullmatch(r'SCOPE-\d{3}', s['scope_token']):
        raise ValueError('anonymous_scope_required')
    if s['marketplace'] not in {'US', 'CA', 'MX', 'UK', 'DE', 'FR', 'IT', 'ES', 'JP', 'AU', 'IN'} or s['currency'] not in {'USD','CAD','MXN','GBP','EUR','JPY','AUD','INR'}:
        raise ValueError('unsupported_scope')
    if s['ad_type'] != 'SP' or s['attribution_basis'] != 'click':
        raise ValueError('only_click_based_SP_supported')
    lag = integer(s['attribution_days'], 1, 90) + integer(s['reporting_lag_days'], 0, 30)
    snapshot = day(data['snapshot_date'])
    units = data['units']
    if not isinstance(units, list) or not units or len(units) != len(set(units)) or any(not isinstance(u, str) or not re.fullmatch(r'UNIT-[A-Z]{1,3}', u) for u in units):
        raise ValueError('anonymous_unique_units_required')
    periods = data['periods']
    if not isinstance(periods, list) or len(periods) != 2:
        raise ValueError('two_periods_required')
    windows = {}
    for p in periods:
        exact(p, ('period', 'start_date', 'end_date'))
        name = p['period']
        if name not in ('before', 'after') or name in windows:
            raise ValueError('unique_before_after_required')
        start, end = day(p['start_date']), day(p['end_date'])
        if start > end or end > snapshot or (end - start).days > 365:
            raise ValueError('invalid_window')
        windows[name] = (start, end)
    if windows['before'][1] >= windows['after'][0]:
        raise ValueError('overlapping_or_reversed_windows')
    if not isinstance(data['events'], list) or not isinstance(data['rows'], list):
        raise ValueError('lists_required')
    for e in data['events']:
        exact(e, ('period', 'date', 'kind'))
        if e['period'] not in windows or e['kind'] not in EVENTS:
            raise ValueError('invalid_event')
        a, b = windows[e['period']]
        if not a <= day(e['date']) <= b:
            raise ValueError('event_outside_window')
    seen, normalized, issues = set(), [], []
    for source_row, row in enumerate(data['rows'], 1):
        exact(row, ('period', 'date', 'unit', 'active') + METRICS)
        if row['period'] not in windows or row['unit'] not in units or type(row['active']) is not bool:
            raise ValueError('row_scope_or_active_invalid')
        d = day(row['date']); a, b = windows[row['period']]
        if not a <= d <= b:
            raise ValueError('row_outside_window')
        key = (row['period'], row['date'], row['unit'])
        if key in seen:
            raise ValueError('duplicate_daily_unit')
        seen.add(key)
        n = {k: number(row[k], k in ('impressions', 'clicks', 'orders')) for k in METRICS}
        if any(v is None for v in n.values()):
            issues.append({'source_row': source_row, 'code': 'missing_metric'})
        if n['clicks'] is not None and n['impressions'] is not None and n['clicks'] > n['impressions']:
            issues.append({'source_row': source_row, 'code': 'clicks_above_impressions'})
        if (n['clicks'] == 0 and n['spend'] is not None and n['spend'] > 0) or (n['orders'] == 0 and n['sales'] is not None and n['sales'] > 0):
            issues.append({'source_row': source_row, 'code': 'inconsistent_metrics'})
        if not row['active'] and any(v is not None and v > 0 for v in n.values()):
            issues.append({'source_row': source_row, 'code': 'inactive_with_metrics'})
        normalized.append(dict(n, period=row['period'], date=row['date'], unit=row['unit'], active=row['active'], source_row=source_row))
    results, blockers = {}, []
    for name, (start, end) in windows.items():
        days = (end - start).days + 1
        rows = [r for r in normalized if r['period'] == name]
        complete = len(rows) == days * len(units)
        if not complete: blockers.append(name + ':daily_unit_coverage_incomplete')
        mature = (snapshot - end).days >= lag
        if not mature: blockers.append(name + ':attribution_or_reporting_window_incomplete')
        m = summarize(rows, complete)
        active_days = len({r['date'] for r in rows if r['active']}) if complete else None
        m.update(calendar_days=days, active_days=active_days, rows=len(rows), expected_rows=days * len(units), coverage_complete=complete,
                 mature_under_declared_lag=mature, source_rows=[r['source_row'] for r in rows],
                 per_calendar_day={k: ratio(v, Decimal(days)) for k,v in m['totals'].items()},
                 per_active_day={k: ratio(v, Decimal(active_days)) if active_days is not None else None for k,v in m['totals'].items()},
                 units={u: summarize([r for r in rows if r['unit']==u], complete) for u in units})
        results[name] = m
    if issues: blockers.append('data_quality_issues')
    comparable = not blockers
    before, after = results['before'], results['after']
    delta = {}
    for section in ('totals', 'ratios', 'per_calendar_day', 'per_active_day'):
        delta[section] = {}
        for key, old in before[section].items():
            new = after[section][key]
            valid = comparable and old is not None and new is not None
            delta[section][key] = {'absolute': new-old if valid else None, 'relative': ratio(new-old,old) if valid else None}
    pooled_old, pooled_new = before['ratios']['acos'], after['ratios']['acos']
    worsening = [u for u in units if comparable and before['units'][u]['ratios']['acos'] is not None and after['units'][u]['ratios']['acos'] is not None and after['units'][u]['ratios']['acos'] > before['units'][u]['ratios']['acos']]
    mix = comparable and pooled_old is not None and pooled_new is not None and pooled_new < pooled_old and len(worsening)==len(units)
    return serial({'schema_version':1, 'data_kind':data['data_kind'], 'scope':s, 'snapshot_date':data['snapshot_date'],
                   'status':'COMPARABLE_DESCRIPTIVE' if comparable else 'BLOCKED_COMPARISON',
                   'periods':results, 'deltas':delta, 'blockers':blockers, 'issues':issues, 'events':data['events'],
                   'mix_shift_warning':mix, 'all_units_acos_worsened':worsening, 'business_writes':0, 'causal_effect_verified':False,
                   'limits':['Descriptive comparison only; declared lags do not certify final source data.',
                             'Active-day averages exclude inactive dates; inspect both denominators.',
                             'No product facts, financial reconciliation, bid recommendation or backend execution.']})


def render(r):
    def fmt(v): return '未知' if v is None else f'{v:,.4f}'
    rows=[]
    for section in ('totals','per_calendar_day','per_active_day','ratios'):
        for metric in r['periods']['before'][section]:
            b=r['periods']['before'][section][metric];a=r['periods']['after'][section][metric]
            d=r['deltas'][section][metric]
            rows.append('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in [section,metric,fmt(b),fmt(a),fmt(d['absolute']),'未知' if d['relative'] is None else f"{d['relative']:.2%}"] )+'</tr>')
    label='完全合成练习' if r['data_kind']=='synthetic' else '匿名本地输入 · 不供公开'
    details=escape(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False))
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AIPANDA 匿名广告周期复盘</title><style>*{{box-sizing:border-box}}body{{font:16px/1.8 system-ui;background:#fbfbfd;color:#17233b;margin:0}}main{{max-width:1040px;margin:auto;padding:32px 24px}}a{{color:#6950c7}}p,.note{{overflow-wrap:anywhere}}.note{{padding:18px;background:#f0ecfa;border-left:4px solid #a995e7}}.table{{overflow:auto}}table{{border-collapse:collapse;min-width:680px;width:100%;font-size:14px}}td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf0f7;padding:18px}}code{{overflow-wrap:anywhere}}</style><main><p>🐼 AIPANDA · {label} · MIT</p><h1>广告周期复盘，先核对比较条件。</h1><div class="note"><strong>{escape(r['status'])}</strong><br>金额均按输入声明的 {escape(r['scope']['currency'])} 展示；百分比率以小数存储。只做描述性比较，未验证因果效果，不输出竞价或否词操作。</div><p>阻断：{escape(', '.join(r['blockers']) or '无')} · 聚合改善但各单元恶化：{'是' if r['mix_shift_warning'] else '否'}</p><p>完整覆盖、日历天数、实际投放天数、分单元结果与源行号见下方 JSON。空缺不补零；归因未成熟时仍展示原始数据，但比较变化保留未知。</p><div class="table"><table><tr><th>口径</th><th>指标</th><th>之前</th><th>之后</th><th>绝对变化</th><th>相对变化</th></tr>{''.join(rows)}</table></div><details><summary>展开完整审计结果</summary><pre>{details}</pre></details><p>声明的成熟窗口不代表后续不会回填；事件与投放结构变化仍需人工解释。本报告不包含产品成本、费用账本或利润核对。</p><p><a href="https://github.com/KECHENAaron/aipanda-amazon-ai-skills/tree/main/skills/aipanda-ads-period-review">源码与使用说明</a></p></main></html>'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    if a.output_dir.exists():p.error('output_directory_exists')
    try:r=review(json.loads(a.input.read_text(encoding='utf-8')))
    except (ValueError,TypeError,KeyError,OverflowError):p.error('invalid_input; review the public contract; input values are not echoed')
    a.output_dir.mkdir(parents=True)
    (a.output_dir/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (a.output_dir/'report.html').write_text(render(r),encoding='utf-8')
    print(json.dumps({'status':r['status'],'business_writes':0}))

if __name__=='__main__':main()
