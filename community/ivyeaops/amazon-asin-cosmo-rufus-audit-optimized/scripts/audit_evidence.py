# AIPANDA public curation, modified 2026-11-14; AGPL-3.0; see PUBLIC_CHANGES.md.
"""Check product-fact consistency and whether proposed copy is supported."""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

CRITICAL = {'material','dimensions','total_load','individual_load','max_users','age_range','voltage','wattage','included_quantity','warranty','certification'}


def normalized(value, unit=''):
    aliases={'lbs':'lb','pounds':'lb','inches':'in','feet':'ft','kilograms':'kg'}
    unit=aliases.get(unit.lower().strip(),unit.lower().strip())
    return json.dumps(value,ensure_ascii=False,sort_keys=True).strip().lower(),unit


def audit(data, as_of=None):
    product=data['product'];asin=product['asin'];sku=product.get('sku');batch=product.get('batch_id')
    if not asin or not product.get('marketplace'):raise ValueError('必须提供ASIN与站点')
    today=date.fromisoformat(as_of) if as_of else date.today()
    sources={s['id']:s for s in data.get('sources',[])}
    if len(sources)!=len(data.get('sources',[])):raise ValueError('source id 重复')
    groups=defaultdict(list);excluded=[];ids=set()
    for claim in data.get('claims',[]):
        if claim['id'] in ids:raise ValueError('claim id 重复')
        ids.add(claim['id'])
        source=sources.get(claim.get('source_id'))
        if not source:raise ValueError('claim 缺少可追溯 source_id')
        claim_asin=claim.get('asin') or source.get('asin')
        if claim_asin!=asin:
            excluded.append({'claim_id':claim['id'],'reason':'other_or_unknown_variant'});continue
        groups[(claim['field'],claim.get('component','unspecified'))].append(claim)
    facts=[];by_claim={}
    for (field,component),claims in groups.items():
        values={normalized(c.get('value'),c.get('unit','')) for c in claims if c.get('value') is not None}
        reasons=[];confirmations=[]
        for claim in claims:
            source=sources[claim['source_id']]
            if claim.get('value') is None:continue
            observed=source.get('observed_at')
            valid_date=False
            if observed:
                day=date.fromisoformat(observed[:10]);valid_date=day<=today
                if not valid_date:reasons.append('future_source_date')
            exact_sku=bool(sku and source.get('sku')==sku)
            exact_batch=bool(batch and source.get('batch_id')==batch)
            evidence=source.get('verification')=='reviewed_original' and bool(source.get('reference'))
            scope_ok=source.get('asin')==asin and source.get('marketplace')==product['marketplace'] and exact_sku
            batch_ok=(exact_batch or source.get('applies_to_all_current_batches') is True) if field in CRITICAL else True
            if evidence and scope_ok and batch_ok and valid_date:confirmations.append(claim['id'])
        if not values:status='missing'
        elif len(values)>1:status='disputed';reasons.append('conflicting_values_or_units')
        elif confirmations:status='confirmed'
        else:status='unverified';reasons.append('needs_reviewed_original_and_exact_sku_batch_binding')
        fact={'field':field,'component':component,'status':status,'claims':claims,'confirmed_claim_ids':confirmations,'reasons':sorted(set(reasons))}
        facts.append(fact)
        for c in claims:by_claim[c['id']]=fact
    copy_results=[]
    for copy in data.get('copy_claims',[]):
        references=copy.get('fact_ids',[])
        blocked=[i for i in references if i not in by_claim or by_claim[i]['status']!='confirmed']
        status='references_validated_manual_text_review_required' if references and not blocked else 'blocked_missing_or_conflicting_evidence'
        copy_results.append({'id':copy['id'],'location':copy.get('location'),'text':copy['text'],'status':status,'blocked_fact_ids':blocked,'fact_ids':references,'text_semantics_verified':False})
    seen=set();matched=[];unknown=[];other=[];duplicates=0
    for review in data.get('reviews',[]):
        key=review.get('id') or hashlib.sha256(json.dumps([review.get('date'),review.get('rating'),review.get('text','').strip()],ensure_ascii=False).encode()).hexdigest()
        if key in seen:duplicates+=1;continue
        seen.add(key)
        if not review.get('asin'):unknown.append(review)
        elif review['asin']!=asin:other.append(review)
        else:matched.append(review)
    dates=sorted(r['date'] for r in matched if r.get('date'))
    review_stats={'returned':len(data.get('reviews',[])),'deduplicated':len(seen),'duplicate_count':duplicates,'exact_variant':len(matched),'unknown_variant':len(unknown),'other_variant':len(other),
        'first_date':dates[0] if dates else None,'last_date':dates[-1] if dates else None,'topic_counts':dict((t,sum(t in r.get('topics',[]) for r in matched)) for t in sorted({t for r in matched for t in r.get('topics',[])})),
        'population_complete':False,'not_a_defect_rate':True}
    blockers=[f for f in facts if f['status']!='confirmed']
    missing_fields=sorted(set(data.get('required_fields',[]))-{f['field'] for f in facts})
    return {'product':product,'as_of':today.isoformat(),'status':'DRAFT_WITH_BLOCKERS' if not facts or blockers or missing_fields or any(c['status'].startswith('blocked') for c in copy_results) else 'EVIDENCE_CHECKED_DRAFT',
        'facts':facts,'excluded_claims':excluded,'copy_claims':copy_results,'reviews':review_stats,'missing_critical_fields':missing_fields,
        'official_algorithm_score':None,'rufus_live_test_performed':False,'authenticity_independently_verified':False,'copy_text_semantics_verified':False,
        'verification_limit':'检查输入声明、冲突及范围绑定，不替代原件内容人工审阅或实际Rufus测试','business_writes':0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--as-of');p.add_argument('--strict',action='store_true');a=p.parse_args()
    out=Path(a.out)
    if out.exists():raise FileExistsError('输出已存在')
    result=audit(json.loads(Path(a.input).read_text()),a.as_of)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'status':result['status'],'facts':len(result['facts']),'blocked_copy':sum(x['status'].startswith('blocked') for x in result['copy_claims']),'reviews':result['reviews'],'business_writes':0},ensure_ascii=False))
    return 2 if a.strict and result['status']=='DRAFT_WITH_BLOCKERS' else 0

if __name__=='__main__':raise SystemExit(main())
