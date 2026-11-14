#!/usr/bin/env python3
"""Create three wholly synthetic examples from constants, without any data input. MIT."""
import copy
from datetime import date,timedelta
import json
from pathlib import Path


def demo(kind='unequal-days'):
    if kind not in ('unequal-days','immature','mix-shift'):raise ValueError('unknown_demo')
    a,b=date(2026,1,1),date(2026,1,10)
    ndays=3 if kind=='mix-shift' else 6
    d={'schema_version':1,'data_kind':'synthetic','scope':{'scope_token':'SCOPE-001','marketplace':'US','currency':'USD','ad_type':'SP','attribution_basis':'click','attribution_days':7,'reporting_lag_days':2},'snapshot_date':'2026-03-01','units':['UNIT-A','UNIT-B'],'periods':[{'period':'before','start_date':str(a),'end_date':str(a+timedelta(days=2))},{'period':'after','start_date':str(b),'end_date':str(b+timedelta(days=ndays-1))}],'rows':[],'events':[]}
    for period,start,days in [('before',a,3),('after',b,ndays)]:
        for i in range(days):
            for unit in d['units']:
                if kind=='mix-shift':
                    spend,sales={( 'before','UNIT-A'):(1,10),('before','UNIT-B'):(9,30),('after','UNIT-A'):(6,50),('after','UNIT-B'):(3.5,10)}[(period,unit)]
                    orders=1
                else:
                    spend=(8 if unit=='UNIT-A' else 4)*(0.75 if period=='after' else 1)
                    sales=20 if unit=='UNIT-A' else 40;orders=1 if unit=='UNIT-A' else 2
                d['rows'].append({'period':period,'date':str(start+timedelta(days=i)),'unit':unit,'active':True,'impressions':100,'clicks':10,'spend':spend,'orders':orders,'sales':sales})
    if kind=='immature':d['snapshot_date']='2026-01-18'
    if kind=='mix-shift':d['events']=[{'period':'after','date':str(b),'kind':'promotion'}]
    return d

if __name__=='__main__':
    out=Path(__file__).resolve().parents[1]/'assets'
    for kind in ('unequal-days','immature','mix-shift'):
        target=out/(kind+'.json')
        if target.exists():raise SystemExit('example_exists; no files overwritten')
        target.write_text(json.dumps(demo(kind),ensure_ascii=False,indent=2)+'\n')
