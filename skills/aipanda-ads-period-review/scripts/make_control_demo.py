#!/usr/bin/env python3
"""Independent synthetic control hypotheses, generated from constants only. MIT."""
from datetime import date,timedelta
from pathlib import Path
import copy,json
KINDS=('bid','budget','placement','joint-change')


def demo(kind='bid'):
    if kind not in KINDS:raise ValueError('unknown_demo')
    current={'base_bid':.8,'average_daily_budget':20,'placement_pct':{'top':25,'rest':0,'product':0}}
    proposal=copy.deepcopy(current)
    if kind=='bid':proposal['base_bid']=.9
    elif kind=='budget':proposal['average_daily_budget']=24
    elif kind=='placement':proposal['placement_pct']['top']=50
    else:proposal['base_bid']=1.1;proposal['placement_pct']['top']=75;proposal['average_daily_budget']=24
    daily=[]
    for i in range(7):daily.append({'date':str(date(2026,3,1)+timedelta(days=i)),'budget_exhausted':i in (1,3,5),'impressions':300,'clicks':30,'spend':20,'orders':3,'sales':120})
    placements=[]
    for key,spend in [('top',8),('rest',5),('product',7)]:placements.append({'placement':key,'impressions':700,'clicks':70,'spend':spend*7,'orders':7,'sales':280})
    return {'schema_version':1,'data_kind':'synthetic','unit':'UNIT-A','scope':{'scope_token':'SCOPE-001','marketplace':'US','currency':'USD','ad_type':'SP','attribution_basis':'click','attribution_days':7,'reporting_lag_days':2},'window':{'start_date':'2026-03-01','end_date':'2026-03-07','snapshot_date':'2026-04-01'},'context':{'configuration_as_of':'2026-04-01','state':'enabled','ownership':'exclusive','relevance':'supported','capacity':'adequate','observation_status':'stable','strategy':'fixed','other_bid_adjustments':'none_declared','budget_rules':'none_declared','bid_basis':'single_or_uniform_declared','performance_scope':'campaign_declared','placement_partition':'exclusive_three_declared'},'current':current,'proposal':proposal,'guardrails':{'target_acos':.25,'min_clicks':20,'min_orders':3,'max_base_bid':1.2,'max_average_daily_budget':30,'max_placement_adjusted_bid':1.5},'daily':daily,'placements':placements}

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]/'assets'
    for kind in KINDS:
        p=root/f'control-{kind}.json'
        if p.exists():raise SystemExit('demo_exists; no file overwritten')
        p.write_text(json.dumps(demo(kind),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
