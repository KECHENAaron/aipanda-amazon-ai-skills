# AIPANDA public curation, modified 2026-11-14; AGPL-3.0; see PUBLIC_CHANGES.md.
"""Validate independent image briefs without generating or uploading images."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path


def validate(brief):
    asin=brief['product']['asin'];sku=brief['product'].get('sku');batch=brief['product'].get('batch_id')
    facts={f['id']:f for f in brief.get('facts',[])}
    if len(facts)!=len(brief.get('facts',[])):raise ValueError('重复fact id')
    slots=brief['slots']
    if not slots or len({s['slot'] for s in slots})!=len(slots):raise ValueError('槽位为空或编号重复')
    if sum(s['slot']==1 for s in slots)!=1:raise ValueError('需要且仅需要一张主图slot 1')
    rows=[]
    for slot in slots:
        blockers=[]
        for key in ['question','background','subject','text_overlays','callouts','forbidden']:
            if key not in slot:raise ValueError('简报缺少字段 '+key)
        if not slot['question'].strip():blockers.append('buyer_question_missing')
        if slot['slot']==1:
            if slot['background'].strip().upper()!='#FFFFFF':blockers.append('main_background_not_white')
            if slot['text_overlays'] or slot['callouts']:blockers.append('main_has_added_text')
        for claim in slot.get('claims',[]):
            if not claim.get('fact_ids'):blockers.append('claim_without_evidence');continue
            for ident in claim['fact_ids']:
                fact=facts.get(ident,{})
                if fact.get('status')!='confirmed' or fact.get('asin')!=asin or not fact.get('source_reference'):
                    blockers.append('unverified_claim:'+ident)
                if sku and fact.get('sku')!=sku:blockers.append('wrong_sku:'+ident)
                if batch and fact.get('batch_id')!=batch:blockers.append('wrong_batch:'+ident)
        for text in slot['text_overlays']:
            if re.search(r'\d|GFCI|certified|waterproof|warranty|承重|认证|防水|保修',text,re.I):
                if not any(c.get('text')==text and c.get('fact_ids') for c in slot.get('claims',[])):
                    blockers.append('quantitative_or_sensitive_text_without_claim')
        if slot.get('role')=='comparison' and not slot.get('comparison_evidence'):
            blockers.append('comparison_evidence_missing')
        if slot.get('role')=='real_use' and not slot.get('actual_photo_reference'):
            blockers.append('real_use_photo_missing')
        if slot.get('role')=='included_items' and not slot.get('bom_reference'):
            blockers.append('current_bom_missing')
        if slot['slot']==1 and slot.get('accessories_visible') and not slot.get('bom_reference'):
            blockers.append('main_accessories_not_bound_to_bom')
        warnings=[]
        for text in slot['text_overlays']:
            if max((len(line.split()) for line in text.splitlines()),default=0)>7:warnings.append('long_mobile_copy')
        rows.append({'slot':slot['slot'],'role':slot.get('role'),'status':'blocked' if blockers else 'ready_for_design_review','blockers':sorted(set(blockers)),'warnings':warnings,
            'human_product_identity_review_required':True})
    return {'product':brief['product'],'slots':rows,'status':'DRAFT_WITH_BLOCKERS' if any(r['blockers'] for r in rows) else 'BRIEF_CHECKED_DRAFT',
        'suggested_slot_count':7,'actual_slot_count':len(slots),'generated_images':0,'uploaded_images':0,'business_writes':0,
        'note':'简报检查不能证明图像已经生成、合规、与实物一致或经过人工验收'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--strict',action='store_true');a=p.parse_args();out=Path(a.out)
    if out.exists():raise FileExistsError('输出已存在')
    result=validate(json.loads(Path(a.input).read_text()));out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False));return 2 if a.strict and result['status']=='DRAFT_WITH_BLOCKERS' else 0

if __name__=='__main__':raise SystemExit(main())
