#!/usr/bin/env python3
"""Anonymous architecture and search-term diagnostic candidates. Original AIPANDA; MIT."""
import argparse
from collections import defaultdict
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import re
from review import exact, day, integer, number, ratio, serial, summarize

ROLES={'discovery','harvest','defense','product','unknown'}
MATCHES={'auto','broad','phrase','exact','product'}
METRICS=('impressions','clicks','spend','orders','sales')


def label(value,prefix):
    if not isinstance(value,str) or not re.fullmatch(prefix+r'-[A-Z]{1,3}',value):
        raise ValueError('anonymous_label_required')
    return value


def boolean(value):
    if type(value) is not bool:raise ValueError('boolean_required')
    return value


def diagnostic(data):
    exact(data,('schema_version','data_kind','scope','window','thresholds','units','terms','rows','controls','existing_negatives'))
    if type(data['schema_version']) is not int or data['schema_version']!=1 or data['data_kind'] not in ('synthetic','anonymized_local'):
        raise ValueError('unsupported_schema')
    scope=data['scope'];exact(scope,('scope_token','marketplace','currency','ad_type','attribution_basis','attribution_days','reporting_lag_days'))
    if not isinstance(scope['scope_token'],str) or not re.fullmatch(r'SCOPE-\d{3}',scope['scope_token']):raise ValueError('anonymous_scope_required')
    if scope['marketplace'] not in {'US','CA','MX','UK','DE','FR','IT','ES','JP','AU','IN'} or scope['currency'] not in {'USD','CAD','MXN','GBP','EUR','JPY','AUD','INR'} or scope['ad_type']!='SP' or scope['attribution_basis']!='click':raise ValueError('unsupported_scope')
    lag=integer(scope['attribution_days'],1,90)+integer(scope['reporting_lag_days'],0,30)
    w=data['window'];exact(w,('start_date','end_date','snapshot_date'))
    start,end,snapshot=(day(w[k]) for k in ('start_date','end_date','snapshot_date'))
    if not start<=end<=snapshot or (end-start).days>365:raise ValueError('invalid_window')
    mature=(snapshot-end).days>=lag
    t=data['thresholds'];exact(t,('target_acos','min_clicks','min_orders','review_spend'))
    target=number(t['target_acos']);spend_line=number(t['review_spend'])
    if target is None or target<=0 or spend_line is None or spend_line<=0:raise ValueError('explicit_positive_thresholds_required')
    min_clicks=integer(t['min_clicks'],1,1000000);min_orders=integer(t['min_orders'],1,1000000)
    for k in ('units','terms','rows','controls','existing_negatives'):
        if not isinstance(data[k],list):raise ValueError('list_required')
    units={};terms={};issues=[]
    for u in data['units']:
        exact(u,('unit','role','match','state','ownership','budget_headroom','negative_list_complete'))
        uid=label(u['unit'],'UNIT')
        if uid in units or u['role'] not in ROLES or u['match'] not in MATCHES or u['state'] not in {'enabled','paused'} or u['ownership'] not in {'exclusive','shared','unknown'} or u['budget_headroom'] not in {'yes','no','unknown'}:raise ValueError('invalid_unit')
        boolean(u['negative_list_complete']);units[uid]=u
        if u['role']=='unknown':issues.append({'unit':uid,'code':'role_not_declared'})
    if not units:raise ValueError('units_required')
    for q in data['terms']:
        exact(q,('term','kind','tokens','relevance','protected','owner','owner_continuity_declared'))
        qid=label(q['term'],'TERM')
        if qid in terms or q['kind'] not in {'query','product_target'} or q['relevance'] not in {'relevant','irrelevant','unknown'} or not isinstance(q['tokens'],list):raise ValueError('invalid_term')
        boolean(q['protected']);boolean(q['owner_continuity_declared'])
        for token in q['tokens']:label(token,'TOKEN')
        if (q['kind']=='product_target' and q['tokens']) or (q['kind']=='query' and not q['tokens']):raise ValueError('token_kind_mismatch')
        if q['owner'] is not None and q['owner'] not in units:raise ValueError('unknown_owner')
        terms[qid]=q
    if not terms:raise ValueError('terms_required')
    rows=[];seen=set();ids=set()
    for index,row in enumerate(data['rows'],1):
        exact(row,('row_id','unit','term')+METRICS)
        rid=row['row_id']
        if not isinstance(rid,str) or not re.fullmatch(r'ROW-\d{3,6}',rid) or rid in ids or row['unit'] not in units or row['term'] not in terms:raise ValueError('invalid_row_identity')
        key=(row['unit'],row['term'])
        if key in seen:raise ValueError('duplicate_source_term')
        seen.add(key);ids.add(rid)
        q=terms[row['term']];u=units[row['unit']]
        if (u['match']=='product' and q['kind']!='product_target') or (u['match'] in {'broad','phrase','exact'} and q['kind']!='query'):raise ValueError('target_kind_mismatch')
        values={k:number(row[k],k in ('impressions','clicks','orders')) for k in METRICS}
        bad=[]
        if any(v is None for v in values.values()):bad.append('missing_metric')
        if values['clicks'] is not None and values['impressions'] is not None and values['clicks']>values['impressions']:bad.append('clicks_above_impressions')
        if (values['clicks']==0 and any(values[k] is not None and values[k]>0 for k in ('spend','orders','sales'))) or (values['orders']==0 and values['sales'] is not None and values['sales']>0):bad.append('inconsistent_metrics')
        if bad:issues.append({'row_id':rid,'codes':bad})
        rows.append(dict(values,row_id=rid,unit=row['unit'],term=row['term'],source_row=index,quality_issues=bad))
    if not rows:raise ValueError('rows_required')
    controls={}
    for c in data['controls']:
        exact(c,('unit',)+METRICS)
        if c['unit'] not in units or c['unit'] in controls:raise ValueError('invalid_control_identity')
        controls[c['unit']]={k:number(c[k],k in ('impressions','clicks','orders')) for k in METRICS}
    if set(controls)!=set(units):raise ValueError('control_for_each_unit_required')
    negatives=set();phrase_units=set()
    for n in data['existing_negatives']:
        exact(n,('unit','term','kind'))
        if n['unit'] not in units or n['term'] not in terms or n['kind'] not in {'exact','phrase','product'}:raise ValueError('invalid_negative')
        if (n['kind']=='product')!=(terms[n['term']]['kind']=='product_target'):raise ValueError('negative_kind_mismatch')
        key=(n['unit'],n['term'],n['kind'])
        if key in negatives:raise ValueError('duplicate_negative')
        negatives.add(key)
        if n['kind']=='phrase':phrase_units.add(n['unit'])
    unit_results={};control_gaps={}
    for uid,u in units.items():
        part=[r for r in rows if r['unit']==uid];observed=summarize(part,True)
        residual={k:controls[uid][k]-observed['totals'][k] if controls[uid][k] is not None and observed['totals'][k] is not None else None for k in METRICS}
        gaps=[]
        cv=controls[uid]
        if (cv['clicks'] is not None and cv['impressions'] is not None and cv['clicks']>cv['impressions']) or (cv['clicks']==0 and any(cv[k] is not None and cv[k]>0 for k in ('spend','orders','sales'))) or (cv['orders']==0 and cv['sales'] is not None and cv['sales']>0):gaps.append('invalid_control_metrics')
        if any(x is None for x in residual.values()):gaps.append('reconciliation_unknown')
        if any(x is not None and x<0 for x in residual.values()):gaps.append('observed_above_control')
        if any(x is not None and x>0 for x in residual.values()):gaps.append('undisclosed_or_scope_gap')
        control_gaps[uid]=gaps
        if gaps:issues.append({'unit':uid,'codes':gaps})
        unit_results[uid]={'declared_role':u['role'],'declared_state':u['state'],'observed':observed,'control':controls[uid],'residual':residual,'reconciliation_issues':gaps}
    candidates=[];diagnoses=[];term_summaries={};unigrams=defaultdict(list);bigrams=defaultdict(list)
    for qid,q in terms.items():
        part=[r for r in rows if r['term']==qid];summary=summarize(part,True)
        observed_orders=[r['orders'] for r in part]
        converted=any(o is not None and o>0 for o in observed_orders)
        conversion_unknown=not part or any(o is None for o in observed_orders)
        term_bad=any(r['quality_issues'] for r in part)
        protected=q['protected'] or converted
        active_routes=sorted({r['unit'] for r in part if units[r['unit']]['state']=='enabled'})
        term_summaries[qid]={'kind':q['kind'],'observed':summary,'protected_by_declaration_or_observed_orders':protected,'conversion_unknown':conversion_unknown,'active_routes':active_routes,'source_row_ids':[r['row_id'] for r in part]}
        if len(active_routes)>1:issues.append({'term':qid,'code':'multiple_routes_not_evidence_of_bid_inflation'})
        for r in part:
            u=units[r['unit']];stats=summarize([r],True);o=r['orders'];c=r['clicks'];sp=r['spend'];acos=stats['ratios']['acos']
            if r['quality_issues']:bucket='data_incomplete'
            elif not mature:bucket='wait_for_attribution'
            elif protected and o==0:bucket='protect_term_with_other_evidence'
            elif o==0 and c<min_clicks:bucket='observe_sample'
            elif o==0 and sp>=spend_line:bucket='zero_order_review'
            elif o==0:bucket='observe_sample'
            elif o<min_orders:bucket='small_conversion_sample'
            elif acos is None:bucket='sales_denominator_unavailable'
            elif acos is not None and acos>target:bucket='efficiency_review'
            else:bucket='retain_or_expand_review'
            diagnoses.append({'row_id':r['row_id'],'unit':r['unit'],'term':qid,'bucket':bucket,'ratios':stats['ratios'],'source_row':r['source_row']})
            def proposal(kind,more=()):
                blockers=list(more)+list(control_gaps[r['unit']])
                if not mature:blockers.append('attribution_not_mature')
                if r['quality_issues']:blockers.append('row_quality_issues')
                if u['state']!='enabled':blockers.append('source_paused')
                if u['role']=='unknown':blockers.append('role_not_declared')
                if u['ownership']!='exclusive':blockers.append('source_ownership_not_exclusive')
                if not u['negative_list_complete'] and ('negative' in kind or 'exclusion' in kind or 'migration' in kind):blockers.append('negative_registry_incomplete')
                if r['unit'] in phrase_units:blockers.append('phrase_negative_requires_manual_semantic_check')
                nk='product' if q['kind']=='product_target' else 'exact'
                if (r['unit'],qid,nk) in negatives:blockers.append('already_negative')
                candidates.append({'kind':kind,'row_id':r['row_id'],'unit':r['unit'],'term':qid,'state':'BLOCKED' if blockers else 'REVIEW_ONLY','blockers':sorted(set(blockers)),'executable':False,'live_state_independently_verified':False})
            if o==0 and c is not None and c>=min_clicks and sp is not None and sp>=spend_line:
                if q['relevance']=='irrelevant':
                    blockers=[]
                    if protected:blockers.append('protected_or_converted_term')
                    if conversion_unknown:blockers.append('conversion_unknown_in_other_sources')
                    if term_bad:blockers.append('term_evidence_incomplete')
                    proposal('product_exclusion_review' if q['kind']=='product_target' else 'query_exact_negative_review',blockers)
                elif q['relevance']=='unknown':proposal('relevance_review',['relevance_not_declared'])
                else:proposal('traffic_or_bid_context_review',['current_bid_and_context_not_supplied'])
            if bucket in {'efficiency_review','retain_or_expand_review'}:proposal('efficiency_or_capacity_review',['current_bid_and_context_not_supplied'])
            if q['owner'] is not None and q['owner']!=r['unit'] and converted:
                owner=units[q['owner']];owner_rows=[x for x in part if x['unit']==q['owner']];om=summarize(owner_rows,True);guards=[]
                if q['protected']:guards.append('explicitly_protected_term')
                if r['orders'] is not None and r['orders']>0:guards.append('source_has_orders')
                if term_bad:guards.append('term_evidence_incomplete')
                if conversion_unknown:guards.append('conversion_unknown_in_other_sources')
                if q['relevance']!='relevant':guards.append('relevance_not_relevant')
                if r['clicks'] is None or r['clicks']<min_clicks or r['spend'] is None or r['spend']<spend_line:guards.append('source_sample_below_review_gate')
                if owner['role']=='unknown':guards.append('owner_role_not_declared')
                if owner['state']!='enabled':guards.append('owner_paused')
                if owner['budget_headroom']!='yes':guards.append('owner_capacity_not_declared')
                if owner['ownership']!='exclusive':guards.append('owner_ownership_not_exclusive')
                if owner['match']!=('product' if q['kind']=='product_target' else 'exact'):guards.append('owner_target_kind_not_ready')
                if not q['owner_continuity_declared']:guards.append('owner_continuity_not_declared')
                if not owner_rows or any(x['quality_issues'] for x in owner_rows):guards.append('owner_evidence_missing_or_invalid')
                if om['totals']['orders'] is None or om['totals']['orders']<min_orders or om['ratios']['acos'] is None or om['ratios']['acos']>target:guards.append('owner_performance_not_supported')
                guards+=control_gaps[q['owner']]
                proposal('migration_source_exact_review' if q['kind']=='query' else 'migration_source_product_review',guards)
            if q['kind']=='query':
                for token in set(q['tokens']):unigrams[token].append(r)
                for pair in set(zip(q['tokens'],q['tokens'][1:])):bigrams[' '.join(pair)].append(r)
    control_sum={k:sum((c[k] for c in controls.values()),Decimal(0)) if all(c[k] is not None for c in controls.values()) else None for k in METRICS}
    role_views={}
    for role in sorted(ROLES):
        ids=[u for u in units if units[u]['role']==role]
        spend=sum((controls[u]['spend'] for u in ids),Decimal(0)) if all(controls[u]['spend'] is not None for u in ids) else None
        role_views[role]={'units':ids,'control_spend':spend,'spend_share':ratio(spend,control_sum['spend'])}
    def tokens(table):return {k:dict(summarize(v,True),source_row_ids=[r['row_id'] for r in v]) for k,v in sorted(table.items())}
    return serial({'schema_version':1,'data_kind':data['data_kind'],'scope':scope,'window':w,'input_grain':'aggregate_no_daily_trends',
                   'mature_under_declared_lag':mature,'thresholds':t,'architecture':{'units':unit_results,'roles':role_views,'control_totals':control_sum},
                   'terms':term_summaries,'diagnoses':diagnoses,'candidates':candidates,'issues':issues,
                   'token_views':{'non_additive':True,'unigrams':tokens(unigrams),'adjacent_bigrams':tokens(bigrams)},
                   'business_writes':0,'causal_effect_verified':False,'source_declarations_independently_verified':False,
                   'limits':['Opaque tokens do not verify relevance or actual phrase-negative matching.','Controls and search rows must refer to the same declared scope; residuals are not invented terms.','All proposals require human review and a fresh live-state check; no bid values or execution payloads.']})


def render(r):
    def val(x):return '未知' if x is None else str(x)
    body=[]
    for d in r['diagnoses']:
        body.append('<tr>'+''.join('<td>'+escape(val(v))+'</td>' for v in [d['row_id'],d['unit'],d['term'],d['bucket'],d['ratios']['acos']])+'</tr>')
    proposals=[]
    for c in r['candidates']:
        proposals.append('<tr>'+''.join('<td>'+escape(val(v))+'</td>' for v in [c['unit'],c['term'],c['kind'],c['state'],', '.join(c['blockers']) or '仍须人工复核与实时重查'])+'</tr>')
    label='完全合成练习' if r['data_kind']=='synthetic' else '匿名本地输入 · 不供公开'
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AIPANDA 广告架构与搜索词诊断</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#fbfbfd;color:#17233b;font:16px/1.8 system-ui}}main{{max-width:1100px;margin:auto;padding:30px 24px}}p,.note,td{{overflow-wrap:anywhere}}.note{{padding:18px;background:#f0ecfa;border-left:4px solid #a995e7}}.table{{overflow:auto}}table{{width:100%;min-width:760px;border-collapse:collapse;font-size:14px}}th,td{{padding:12px;border-bottom:1px solid #ddd;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf0f7;padding:18px}}a{{color:#6950c7}}</style><main><p>🐼 AIPANDA · {label} · MIT</p><h1>先看广告角色，再回查完整词。</h1><div class="note">声明窗口下归因成熟：{'是' if r['mature_under_declared_lag'] else '否'}。全部为复核候选，executable=false。没有商品、店铺、真实词或经营来源；所有示例指标均为常量合成。</div><h2>逐来源诊断</h2><div class="table"><table><tr><th>源行</th><th>单元</th><th>词标签</th><th>诊断</th><th>ACOS（小数）</th></tr>{''.join(body)}</table></div><h2>候选与阻断条件</h2><div class="table"><table><tr><th>单元</th><th>词标签</th><th>候选类型</th><th>状态</th><th>阻断 / 待核对</th></tr>{''.join(proposals)}</table></div><p>UNIT、TERM 与 TOKEN 是匿名符号。相关性、预算余量、归属、否定表完整和持续承接都是输入声明，未独立核实。词根与双词视图不可相加当总额，商品目标与关键词否定分开。完整结构、残差和符号聚合见审计 JSON。</p><details><summary>完整审计结果</summary><pre>{escape(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False))}</pre></details><p><a href="https://github.com/KECHENAaron/aipanda-amazon-ai-skills/tree/main/skills/aipanda-ads-period-review">源码、方法与输入契约</a></p></main></html>'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    if a.output_dir.exists():p.error('output_directory_exists')
    try:r=diagnostic(json.loads(a.input.read_text(encoding='utf-8')))
    except (ValueError,TypeError,KeyError,ArithmeticError):p.error('invalid_input; values are not echoed; read the diagnostic contract')
    a.output_dir.mkdir(parents=True);(a.output_dir/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');(a.output_dir/'report.html').write_text(render(r),encoding='utf-8')
    print(json.dumps({'candidates':len(r['candidates']),'business_writes':0,'executable':False}))

if __name__=='__main__':main()
