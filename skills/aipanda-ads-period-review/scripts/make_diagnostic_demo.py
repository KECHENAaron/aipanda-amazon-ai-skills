#!/usr/bin/env python3
"""Generate opaque, wholly synthetic diagnostic fixtures from constants only. MIT."""
from pathlib import Path
import json

KINDS=('architecture','term-safety','optimization')


def demo(kind='architecture'):
    if kind not in KINDS:raise ValueError('unknown_demo')
    units=[{'unit':'UNIT-A','role':'discovery','match':'auto','state':'enabled','ownership':'exclusive','budget_headroom':'yes','negative_list_complete':True},
           {'unit':'UNIT-B','role':'harvest','match':'exact','state':'enabled','ownership':'exclusive','budget_headroom':'yes','negative_list_complete':True},
           {'unit':'UNIT-C','role':'product','match':'product','state':'enabled','ownership':'exclusive','budget_headroom':'unknown','negative_list_complete':True}]
    def term(name,tokens,rel='relevant',owner=None,protected=False,kind='query'):
        return {'term':name,'kind':kind,'tokens':tokens,'relevance':rel,'protected':protected,'owner':owner,'owner_continuity_declared':True}
    terms=[term('TERM-A',['TOKEN-A','TOKEN-B','TOKEN-A'],owner='UNIT-B'),term('TERM-B',['TOKEN-A','TOKEN-C'],'irrelevant'),term('TERM-C',[],'irrelevant',kind='product_target'),term('TERM-D',['TOKEN-D'],'unknown'),term('TERM-E',['TOKEN-E']),term('TERM-F',['TOKEN-F'])]
    rows=[]
    def row(unit,q,clicks,spend,orders,sales):
        rows.append({'row_id':f'ROW-{len(rows)+1:03d}','unit':unit,'term':q,'impressions':100,'clicks':clicks,'spend':spend,'orders':orders,'sales':sales})
    row('UNIT-A','TERM-A',18,9,0,0);row('UNIT-B','TERM-A',12,6,3,60)
    row('UNIT-A','TERM-B',20,12,0,0);row('UNIT-C','TERM-C',16,8,0,0)
    row('UNIT-A','TERM-D',16,8,0,0);row('UNIT-A','TERM-E',4,2,0,0)
    row('UNIT-B','TERM-F',20,12,2,20)
    controls=[]
    for u in units:
        part=[r for r in rows if r['unit']==u['unit']]
        controls.append(dict(unit=u['unit'],**{k:sum(r[k] for r in part) for k in ('impressions','clicks','spend','orders','sales')}))
    negatives=[]
    if kind=='architecture':
        units[1]['state']='paused';units[2]['role']='unknown';terms[0]['owner_continuity_declared']=False
        controls[0]['spend']+=3
    if kind=='term-safety':terms[0]['relevance']='irrelevant'
    if kind=='optimization':negatives=[{'unit':'UNIT-A','term':'TERM-B','kind':'exact'}]
    return {'schema_version':1,'data_kind':'synthetic','scope':{'scope_token':'SCOPE-001','marketplace':'US','currency':'USD','ad_type':'SP','attribution_basis':'click','attribution_days':7,'reporting_lag_days':2},'window':{'start_date':'2026-02-01','end_date':'2026-02-07','snapshot_date':'2026-03-01'},'thresholds':{'target_acos':.25,'min_clicks':12,'min_orders':2,'review_spend':8},'units':units,'terms':terms,'rows':rows,'controls':controls,'existing_negatives':negatives}

if __name__=='__main__':
    out=Path(__file__).resolve().parents[1]/'assets'
    for kind in KINDS:
        p=out/('diagnostic-'+kind+'.json')
        if p.exists():raise SystemExit('demo_exists; no files overwritten')
        p.write_text(json.dumps(demo(kind),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
