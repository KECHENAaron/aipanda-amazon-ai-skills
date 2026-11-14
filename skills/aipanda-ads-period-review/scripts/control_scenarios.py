#!/usr/bin/env python3
"""Read-only anonymous SP bid/budget/placement hypotheses, not recommendations. MIT."""
import argparse
from datetime import timedelta
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import re
from review import exact,day,integer,number,ratio,serial,summarize

PLACEMENTS=('top','rest','product')
METRICS=('impressions','clicks','spend','orders','sales')


def model_number(x,count=False):
    n=number(x,count)
    if n is not None and n != n.quantize(Decimal("0.000001")):
        raise ValueError("precision_outside_model_range")
    return n


def positive(x):
    n=model_number(x)
    if n is None or n<=0:raise ValueError('positive_setting_required')
    return n


def config(c):
    exact(c,('base_bid','average_daily_budget','placement_pct'))
    exact(c['placement_pct'],PLACEMENTS)
    v={k:model_number(c['placement_pct'][k]) for k in PLACEMENTS}
    if any(x is None or x>900 for x in v.values()):raise ValueError('placement_outside_model_range')
    return {'base_bid':positive(c['base_bid']),'average_daily_budget':positive(c['average_daily_budget']),'placement_pct':v}


def metrics(row):
    v={k:model_number(row[k],k in ('impressions','clicks','orders')) for k in METRICS};issues=[]
    if any(x is None for x in v.values()):issues.append('missing_metric')
    if v['clicks'] is not None and v['impressions'] is not None and v['clicks']>v['impressions']:issues.append('clicks_above_impressions')
    if (v['clicks']==0 and any(v[k] is not None and v[k]>0 for k in ('spend','orders','sales'))) or (v['orders']==0 and v['sales'] is not None and v['sales']>0):issues.append('inconsistent_metrics')
    return v,issues


def assess(data):
    exact(data,('schema_version','data_kind','unit','scope','window','context','current','proposal','guardrails','daily','placements'))
    if type(data['schema_version']) is not int or data['schema_version']!=1 or data['data_kind'] not in ('synthetic','anonymized_local'):raise ValueError('unsupported_schema')
    if not isinstance(data['unit'],str) or not re.fullmatch(r'UNIT-[A-Z]{1,3}',data['unit']):raise ValueError('anonymous_unit_required')
    s=data['scope'];exact(s,('scope_token','marketplace','currency','ad_type','attribution_basis','attribution_days','reporting_lag_days'))
    if not isinstance(s['scope_token'],str) or not re.fullmatch(r'SCOPE-\d{3}',s['scope_token']):raise ValueError('anonymous_scope_required')
    if s['marketplace'] not in {'US','CA','MX','UK','DE','FR','IT','ES','JP','AU','IN'} or s['currency'] not in {'USD','CAD','MXN','GBP','EUR','JPY','AUD','INR'} or s['ad_type']!='SP' or s['attribution_basis']!='click':raise ValueError('unsupported_scope')
    lag=integer(s['attribution_days'],1,90)+integer(s['reporting_lag_days'],0,30)
    w=data['window'];exact(w,('start_date','end_date','snapshot_date'))
    start,end,snapshot=(day(w[k]) for k in ('start_date','end_date','snapshot_date'))
    if not start<=end<=snapshot or (end-start).days>30:raise ValueError('window_outside_model_range')
    ctx=data['context'];exact(ctx,('configuration_as_of','state','ownership','relevance','capacity','observation_status','strategy','other_bid_adjustments','budget_rules','bid_basis','performance_scope','placement_partition'))
    config_date=day(ctx['configuration_as_of'])
    if config_date>snapshot:raise ValueError('future_configuration_date')
    if ctx['state'] not in {'enabled','paused'} or ctx['ownership'] not in {'exclusive','shared','unknown'} or ctx['relevance'] not in {'supported','unknown'} or ctx['capacity'] not in {'adequate','limited','unknown'} or ctx['observation_status'] not in {'stable','recent_change','unknown'} or ctx['strategy'] not in {'fixed','dynamic_down_only','dynamic_up_down','rule_based','unknown'} or ctx['other_bid_adjustments'] not in {'none_declared','present','unknown'} or ctx['budget_rules'] not in {'none_declared','present','unknown'} or ctx['bid_basis'] not in {'single_or_uniform_declared','mixed','unknown'} or ctx['performance_scope'] not in {'campaign_declared','partial_or_unknown'} or ctx['placement_partition'] not in {'exclusive_three_declared','unknown'}:raise ValueError('invalid_context')
    before,after=config(data['current']),config(data['proposal'])
    g=data['guardrails'];exact(g,('target_acos','min_clicks','min_orders','max_base_bid','max_average_daily_budget','max_placement_adjusted_bid'))
    target=positive(g['target_acos']);min_clicks=integer(g['min_clicks'],1,1000000);min_orders=integer(g['min_orders'],1,1000000)
    max_base=positive(g['max_base_bid']);max_budget=positive(g['max_average_daily_budget']);max_adjusted=positive(g['max_placement_adjusted_bid'])
    if not isinstance(data['daily'],list) or not isinstance(data['placements'],list):raise ValueError('lists_required')
    days={};issues=[]
    for r in data['daily']:
        exact(r,('date','budget_exhausted')+METRICS);d=day(r['date'])
        if not start<=d<=end or d in days:raise ValueError('invalid_or_duplicate_day')
        if r['budget_exhausted'] is not None and type(r['budget_exhausted']) is not bool:raise ValueError('budget_status_must_be_boolean_or_null')
        v,bad=metrics(r);days[d]=dict(v,budget_exhausted=r['budget_exhausted']);issues.extend({'date':r['date'],'code':x} for x in bad)
    complete=len(days)==(end-start).days+1
    if not complete:issues.append({'code':'daily_coverage_incomplete'})
    placement_rows={}
    for r in data['placements']:
        exact(r,('placement',)+METRICS);key=r['placement']
        if key not in PLACEMENTS or key in placement_rows:raise ValueError('invalid_or_duplicate_placement')
        v,bad=metrics(r);placement_rows[key]=v;issues.extend({'placement':key,'code':x} for x in bad)
    daily=summarize(list(days.values()),complete)
    placements={k:summarize([v],True) for k,v in placement_rows.items()}
    placement_complete=set(placement_rows)==set(PLACEMENTS)
    ptotal=summarize(list(placement_rows.values()),placement_complete)['totals']
    residual={k:daily['totals'][k]-ptotal[k] if daily['totals'][k] is not None and ptotal[k] is not None else None for k in METRICS}
    if not placement_complete:issues.append({'code':'placement_coverage_incomplete'})
    if any(v is None for v in residual.values()):issues.append({'code':'placement_reconciliation_unknown'})
    if any(v is not None and v!=0 for v in residual.values()):issues.append({'code':'placement_scope_gap'})
    mature=(snapshot-end).days>=lag
    eligible_math=ctx['strategy']=='fixed' and ctx['other_bid_adjustments']=='none_declared' and ctx['bid_basis']=='single_or_uniform_declared'
    scenarios={}
    for k in PLACEMENTS:
        old=before['base_bid']*(Decimal(1)+before['placement_pct'][k]/100) if eligible_math else None
        new=after['base_bid']*(Decimal(1)+after['placement_pct'][k]/100) if eligible_math else None
        scenarios[k]={'current':old,'proposed':new,'relative_change':ratio(new-old,old) if new is not None and old is not None else None,'actual_auction_bid_verified':False}
    changed=[]
    for k in ('base_bid','average_daily_budget'):
        if before[k]!=after[k]:changed.append(k)
    changed.extend('placement:'+k for k in PLACEMENTS if before['placement_pct'][k]!=after['placement_pct'][k])
    common=[]
    if not mature:common.append('attribution_not_mature')
    if issues:common.append('data_or_scope_issues')
    if config_date!=snapshot:common.append('current_configuration_stale')
    if ctx['state']!='enabled':common.append('unit_paused')
    if ctx['ownership']!='exclusive':common.append('ownership_not_exclusive')
    if ctx['performance_scope']!='campaign_declared':common.append('campaign_scope_not_declared')
    if ctx['placement_partition']!='exclusive_three_declared':common.append('placement_partition_not_declared')
    if ctx['relevance']!='supported':common.append('relevance_not_declared_supported')
    if ctx['observation_status']!='stable':common.append('observation_not_stable')
    if ctx['budget_rules']!='none_declared':common.append('budget_rules_not_modelled')
    if len(changed)>1:common.append('multiple_levers_changed')
    if after['base_bid']>max_base:common.append('exceeds_user_base_bid_guardrail')
    if after['average_daily_budget']>max_budget:common.append('exceeds_user_budget_guardrail')
    if eligible_math and any(v['proposed']>max_adjusted for v in scenarios.values()):common.append('exceeds_user_placement_adjusted_guardrail')
    def enough(m):return m['totals']['orders'] is not None and m['totals']['orders']>=min_orders and m['totals']['clicks'] is not None and m['totals']['clicks']>=min_clicks
    def efficient(m):return enough(m) and m['ratios']['acos'] is not None and m['ratios']['acos']<=target
    def deviation(m):
        return m['totals']['clicks'] is not None and m['totals']['clicks']>=min_clicks and ((m['ratios']['acos'] is not None and m['ratios']['acos']>target) or m['totals']['orders']==0)
    budget_unknown=any(v['budget_exhausted'] is None for v in days.values()) or not complete
    exhausted_dates=[d.isoformat() for d,v in sorted(days.items()) if v['budget_exhausted'] is True]
    candidates=[]
    for lever in changed:
        blockers=list(common)
        if lever=='base_bid':
            increasing=after['base_bid']>before['base_bid']
            if not eligible_math:blockers.append('bid_strategy_or_adjustments_not_modelled')
            if increasing and not efficient(daily):blockers.append('aggregate_efficiency_not_supported')
            if not increasing and not deviation(daily):blockers.append('reduction_not_supported_by_selected_metrics')
        elif lever=='average_daily_budget':
            increasing=after['average_daily_budget']>before['average_daily_budget']
            if increasing:
                if not efficient(daily):blockers.append('aggregate_efficiency_not_supported')
                if budget_unknown:blockers.append('budget_constraint_evidence_incomplete')
                if not exhausted_dates:blockers.append('no_declared_budget_constraint')
            elif not deviation(daily):blockers.append('reduction_not_supported_by_selected_metrics')
        else:
            k=lever.split(':')[1];increasing=after['placement_pct'][k]>before['placement_pct'][k]
            if not eligible_math:blockers.append('bid_strategy_or_adjustments_not_modelled')
            m=placements.get(k)
            if m is None:blockers.append('selected_placement_missing')
            elif increasing and not efficient(m):blockers.append('placement_efficiency_not_supported')
            elif not increasing and not deviation(m):blockers.append('placement_reduction_not_supported')
        if increasing and ctx['capacity']!='adequate':blockers.append('capacity_not_declared_adequate')
        candidates.append({'lever':lever,'direction':'increase' if increasing else 'decrease','state':'BLOCKED' if blockers else 'REVIEW_ONLY','blockers':sorted(set(blockers)),'executable':False,'live_state_independently_verified':False})
    aov=ratio(daily['totals']['sales'],daily['totals']['orders']);cvr=daily['ratios']['order_per_click']
    cost_ref=target*aov*cvr if aov is not None and cvr is not None else None
    return serial({'schema_version':1,'data_kind':data['data_kind'],'unit':data['unit'],'scope':s,'window':w,'context_declarations':ctx,
                   'current':before,'proposal_hypothesis':after,'guardrails':g,'daily_summary':daily,'placement_summaries':placements,'placement_residual':residual,'issues':issues,
                   'mature_under_declared_lag':mature,'historical_cpc':daily['ratios']['cpc'],'target_cost_cpc_reference':cost_ref,
                   'fixed_only_placement_scenarios':scenarios,'scenario_ceiling_model_available':eligible_math,'changed_levers':changed,'candidates':candidates,
                   'budget_evidence':{'declared_exhausted_dates':exhausted_dates,'has_unknown_status':budget_unknown,'daily_budget_is_hard_cap':False,'spend_cap_guaranteed':False},
                   'business_writes':0,'causal_effect_verified':False,'source_declarations_independently_verified':False,
                   'limits':['Proposals are supplied hypotheses, never calculated bid recommendations.','Cost CPC reference is descriptive, not a break-even line or a bid.','Fixed-only scenarios exclude audience, schedules, business and dynamic adjustments; no actual auction ceiling certified.','Average daily budget is not a guaranteed daily spend cap.']})


def render(r):
    def show(x):return '未知' if x is None else str(x)
    performance=[]
    for k,m in r['placement_summaries'].items():
        performance.append('<tr>'+''.join('<td>'+escape(show(x))+'</td>' for x in [k,m['totals']['clicks'],m['totals']['orders'],m['ratios']['cpc'],m['ratios']['acos']])+'</tr>')
    scenario=[]
    for k,v in r['fixed_only_placement_scenarios'].items():
        scenario.append('<tr>'+''.join('<td>'+escape(show(x))+'</td>' for x in [k,v['current'],v['proposed'],v['relative_change']])+'</tr>')
    candidates=[]
    for c in r['candidates']:
        candidates.append('<tr>'+''.join('<td>'+escape(show(x))+'</td>' for x in [c['lever'],c['direction'],c['state'],', '.join(c['blockers']) or '仍需人工复核与现场重查'])+'</tr>')
    label='完全合成练习' if r['data_kind']=='synthetic' else '匿名本地输入 · 不供公开'
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AIPANDA 竞价预算广告位情景</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#fbfbfd;color:#17233b;font:16px/1.8 system-ui}}main{{max-width:1080px;margin:auto;padding:30px 24px}}p,li,.note,td{{overflow-wrap:anywhere}}.note{{padding:18px;background:#f0ecfa;border-left:4px solid #a995e7}}.table{{overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:720px;font-size:14px}}th,td{{padding:12px;border-bottom:1px solid #ddd;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf0f7;padding:18px}}a{{color:#6950c7}}</style><main><p>🐼 AIPANDA · {label} · MIT</p><h1>竞价、预算与广告位，分开验证。</h1><div class="note">{escape(r['scope']['marketplace'])} · {escape(r['scope']['currency'])} · SP · {escape(r['window']['start_date'])} 至 {escape(r['window']['end_date'])}。只检查调用者提出的假设，全部候选 executable=false。所有示例值由常量构造，未使用经营资料。</div><h2>三个值分别看</h2><p>历史 CPC：{show(r['historical_cpc'])}；声明的基础竞价：{show(r['current']['base_bid'])}；目标成本 CPC 参考：{show(r['target_cost_cpc_reference'])}。参考不是盈亏线或建议 Bid，历史表现不证明下一期转化率。</p><h2>同窗口广告位表现</h2><div class="table"><table><tr><th>广告位</th><th>点击</th><th>订单</th><th>历史 CPC</th><th>ACOS（小数）</th></tr>{''.join(performance)}</table></div><h2>固定竞价乘数情景</h2><p>仅在 fixed、统一基础竞价和无其他加价声明下计算 base × (1 + placement_pct / 100)；不证明实际竞拍上限。动态策略或其他调整不在模型内时显示未知。</p><div class="table"><table><tr><th>广告位</th><th>当前简化情景</th><th>提议简化情景</th><th>相对变化（小数）</th></tr>{''.join(scenario)}</table></div><h2>平均日预算与约束信号</h2><p>声明的平均日预算：{show(r['current']['average_daily_budget'])} → 提议 {show(r['proposal_hypothesis']['average_daily_budget'])}；声明的预算耗尽日期数：{len(r['budget_evidence']['declared_exhausted_dates'])}。预算不是每日硬上限，本报告不保证任何花费上限。</p><h2>候选与阻断</h2><div class="table"><table><tr><th>变量</th><th>方向</th><th>状态</th><th>阻断 / 待复核</th></tr>{''.join(candidates)}</table></div><p>当前状态、预算耗尽、容量和相关性均为输入声明，未独立核实。多变量同改会阻断本脚本的单变量试验候选；不意味着所有联合策略都不可用。没有利润核对或后台执行。</p><details><summary>完整审计 JSON</summary><pre>{escape(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False))}</pre></details><p><a href="https://github.com/KECHENAaron/aipanda-amazon-ai-skills/tree/main/skills/aipanda-ads-period-review">源码、方法与契约</a></p></main></html>'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    if a.output_dir.exists():p.error('output_directory_exists')
    try:r=assess(json.loads(a.input.read_text(encoding='utf-8')))
    except (ValueError,TypeError,KeyError,ArithmeticError):p.error('invalid_input; values are not echoed; read the control contract')
    a.output_dir.mkdir(parents=True);(a.output_dir/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');(a.output_dir/'report.html').write_text(render(r),encoding='utf-8');print(json.dumps({'changed_levers':len(r['changed_levers']),'business_writes':0,'executable':False}))

if __name__=='__main__':main()
