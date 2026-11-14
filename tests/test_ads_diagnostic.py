import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
BASE=Path(__file__).resolve().parents[1]/'skills/aipanda-ads-period-review'
sys.path.insert(0,str(BASE/'scripts'))
from diagnose import diagnostic,render
from make_diagnostic_demo import demo,KINDS

class DiagnosticTests(unittest.TestCase):
 def candidate(self,r,kind,term='TERM-A'):
  return next(c for c in r['candidates'] if c['kind']==kind and c['term']==term)
 def test_architecture_preserves_residual_and_unknown_role(self):
  r=diagnostic(demo('architecture'));self.assertEqual(r['architecture']['units']['UNIT-A']['residual']['spend'],3)
  self.assertIn({'unit':'UNIT-C','code':'role_not_declared'},r['issues'])
  self.assertAlmostEqual(sum(x['spend_share'] for x in r['architecture']['roles'].values()),1,places=7)
 def test_paused_owner_blocks_migration(self):
  c=self.candidate(diagnostic(demo('architecture')),'migration_source_exact_review');self.assertEqual(c['state'],'BLOCKED');self.assertIn('owner_paused',c['blockers'])
 def test_conversion_protects_across_sources_despite_relevance_claim(self):
  r=diagnostic(demo('term-safety'));c=self.candidate(r,'query_exact_negative_review');self.assertIn('protected_or_converted_term',c['blockers'])
  self.assertTrue(r['terms']['TERM-A']['protected_by_declaration_or_observed_orders'])
 def test_product_exclusion_is_not_keyword_negative(self):
  r=diagnostic(demo('term-safety'));c=self.candidate(r,'product_exclusion_review','TERM-C');self.assertEqual(c['state'],'REVIEW_ONLY')
  self.assertFalse(any(x['kind']=='query_exact_negative_review' and x['term']=='TERM-C' for x in r['candidates']))
 def test_repeated_tokens_count_each_row_once(self):
  r=diagnostic(demo('optimization'));self.assertEqual(r['token_views']['unigrams']['TOKEN-A']['totals']['spend'],27)
  pairs=r['token_views']['adjacent_bigrams'];self.assertEqual(pairs['TOKEN-A TOKEN-B']['totals']['spend'],15)
  self.assertNotIn('TOKEN-B TOKEN-C',pairs)
 def test_token_views_are_nonadditive_and_exclude_product_targets(self):
  r=diagnostic(demo('optimization'));v=r['token_views'];self.assertTrue(v['non_additive'])
  self.assertGreater(sum(x['totals']['spend'] for x in v['unigrams'].values()),r['architecture']['control_totals']['spend'])
  self.assertFalse(any('ROW-004' in x['source_row_ids'] for x in v['unigrams'].values()))
 def test_duplicate_source_key_rejected(self):
  d=demo();q=copy.deepcopy(d['rows'][0]);q['row_id']='ROW-999';d['rows'].append(q)
  with self.assertRaises(ValueError):diagnostic(d)
 def test_duplicate_row_id_rejected(self):
  d=demo();d['rows'][1]['row_id']=d['rows'][0]['row_id']
  with self.assertRaises(ValueError):diagnostic(d)
 def test_unknown_conversion_in_other_source_blocks_negative(self):
  d=demo('term-safety');d['rows'][1]['orders']=None;d['rows'][1]['sales']=None
  c=self.candidate(diagnostic(d),'query_exact_negative_review');self.assertIn('conversion_unknown_in_other_sources',c['blockers'])
 def test_bad_evidence_in_other_source_blocks_negative(self):
  d=demo('term-safety');d['rows'][1].update(orders=0,sales=60)
  c=self.candidate(diagnostic(d),'query_exact_negative_review');self.assertIn('term_evidence_incomplete',c['blockers'])
 def test_source_ownership_and_registry_gate(self):
  for field,value,code in [('ownership','shared','source_ownership_not_exclusive'),('negative_list_complete',False,'negative_registry_incomplete'),('state','paused','source_paused')]:
   d=demo('optimization');d['units'][0][field]=value
   c=self.candidate(diagnostic(d),'migration_source_exact_review');self.assertIn(code,c['blockers'])
 def test_owner_readiness_gates(self):
  for field,value,code in [('budget_headroom','unknown','owner_capacity_not_declared'),('ownership','shared','owner_ownership_not_exclusive'),('match','broad','owner_target_kind_not_ready')]:
   d=demo('optimization');d['units'][1][field]=value
   c=self.candidate(diagnostic(d),'migration_source_exact_review');self.assertIn(code,c['blockers'])
 def test_continuity_and_sample_gates(self):
  d=demo('optimization');d['terms'][0]['owner_continuity_declared']=False
  self.assertIn('owner_continuity_not_declared',self.candidate(diagnostic(d),'migration_source_exact_review')['blockers'])
  d=demo('optimization');d['thresholds']['min_clicks']=100
  self.assertIn('source_sample_below_review_gate',self.candidate(diagnostic(d),'migration_source_exact_review')['blockers'])
 def test_owner_performance_gate(self):
  d=demo('optimization');d['rows'][1]['orders']=1
  self.assertIn('owner_performance_not_supported',self.candidate(diagnostic(d),'migration_source_exact_review')['blockers'])
 def test_converting_source_cannot_be_silently_removed(self):
  d=demo('optimization');d['rows'][0].update(orders=1,sales=5)
  self.assertIn('source_has_orders',self.candidate(diagnostic(d),'migration_source_exact_review')['blockers'])
 def test_explicitly_protected_migration_blocked(self):
  d=demo('optimization');d['terms'][0]['protected']=True
  self.assertIn('explicitly_protected_term',self.candidate(diagnostic(d),'migration_source_exact_review')['blockers'])
 def test_existing_negative_is_not_reissued(self):
  c=self.candidate(diagnostic(demo('optimization')),'query_exact_negative_review','TERM-B');self.assertIn('already_negative',c['blockers'])
 def test_phrase_negatives_require_semantic_review(self):
  d=demo('term-safety');d['existing_negatives']=[{'unit':'UNIT-A','term':'TERM-B','kind':'phrase'}]
  c=self.candidate(diagnostic(d),'query_exact_negative_review','TERM-B');self.assertIn('phrase_negative_requires_manual_semantic_check',c['blockers'])
 def test_immature_blocks_all_candidates(self):
  d=demo('optimization');d['window']['snapshot_date']='2026-02-10';r=diagnostic(d)
  self.assertFalse(r['mature_under_declared_lag']);self.assertTrue(all(c['state']=='BLOCKED' for c in r['candidates']))
 def test_reconciliation_gap_cannot_be_invented_as_term(self):
  r=diagnostic(demo('architecture'));self.assertEqual(set(r['terms']),{f'TERM-{x}' for x in 'ABCDEF'})
  self.assertIn('undisclosed_or_scope_gap',self.candidate(r,'query_exact_negative_review','TERM-B')['blockers'])
 def test_control_excess_and_unknown_are_blockers(self):
  for value,code in [(0,'observed_above_control'),(None,'reconciliation_unknown')]:
   d=demo('term-safety');d['controls'][0]['spend']=value
   self.assertIn(code,self.candidate(diagnostic(d),'query_exact_negative_review','TERM-B')['blockers'])
 def test_invalid_control_relationship_is_blocker(self):
  d=demo('term-safety');d['controls'][0]['clicks']=9999
  self.assertIn('invalid_control_metrics',self.candidate(diagnostic(d),'query_exact_negative_review','TERM-B')['blockers'])
 def test_unknown_relevance_is_not_negative(self):
  r=diagnostic(demo('term-safety'));c=self.candidate(r,'relevance_review','TERM-D');self.assertEqual(c['state'],'BLOCKED')
  self.assertFalse(any(c['kind'].endswith('negative_review') and c['term']=='TERM-D' for c in r['candidates']))
 def test_thresholds_are_explicit_configuration(self):
  d=demo('term-safety');d['thresholds']['min_clicks']=100
  self.assertFalse(any(c['kind']=='query_exact_negative_review' and c['term']=='TERM-B' for c in diagnostic(d)['candidates']))
 def test_unknown_fields_and_real_text_rejected(self):
  for field in ['asin','seller_name','unit_cost','note']:
   d=demo();d[field]='not_for_output'
   with self.assertRaises(ValueError):diagnostic(d)
  d=demo();d['terms'][0]['tokens']=['unstructured free text']
  with self.assertRaises(ValueError):diagnostic(d)
 def test_number_and_kind_contracts(self):
  for key,value in [('spend','NaN'),('spend',-1),('clicks',1.5),('orders',True)]:
   d=demo();d['rows'][0][key]=value
   with self.assertRaises(ValueError):diagnostic(d)
  d=demo();d['rows'][0]['unit']='UNIT-C'
  with self.assertRaises(ValueError):diagnostic(d)
 def test_migration_remains_nonexecutable_with_declared_readiness(self):
  r=diagnostic(demo('optimization'));c=self.candidate(r,'migration_source_exact_review');self.assertEqual(c['state'],'REVIEW_ONLY')
  self.assertFalse(c['executable']);self.assertFalse(c['live_state_independently_verified']);self.assertEqual(r['business_writes'],0)
 def test_opaque_overlap_is_not_causal_bid_inflation(self):
  r=diagnostic(demo('optimization'));self.assertFalse(r['causal_effect_verified']);self.assertIn({'term':'TERM-A','code':'multiple_routes_not_evidence_of_bid_inflation'},r['issues'])
 def test_orders_without_sales_do_not_become_healthy(self):
  d=demo("optimization");d["rows"][-1]["sales"]=0
  r=diagnostic(d);q=next(x for x in r["diagnoses"] if x["term"]=="TERM-F")
  self.assertEqual(q["bucket"],"sales_denominator_unavailable")
  self.assertFalse(any(x["term"]=="TERM-F" and x["kind"]=="efficiency_or_capacity_review" for x in r["candidates"]))
 def test_zero_clicks_with_orders_are_flagged(self):
  d=demo("optimization");d["rows"][-1]["clicks"]=0
  r=diagnostic(d);q=next(x for x in r["diagnoses"] if x["term"]=="TERM-F")
  self.assertEqual(q["bucket"],"data_incomplete")
 def test_exact_constant_generator_inputs(self):
  for kind in KINDS:self.assertEqual(json.loads((BASE/f'assets/diagnostic-{kind}.json').read_text()),demo(kind))
 def test_local_input_not_public_label(self):
  d=demo();d['data_kind']='anonymized_local';self.assertIn('不供公开',render(diagnostic(d)))
 def test_existing_output_is_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'out';out.mkdir();mark=out/'report.json';mark.write_text('preserve')
   p=subprocess.run([sys.executable,str(BASE/'scripts/diagnose.py'),'--input',str(BASE/'assets/diagnostic-optimization.json'),'--output-dir',str(out)],capture_output=True)
   self.assertNotEqual(p.returncode,0);self.assertEqual(mark.read_text(),'preserve')
 def test_invalid_values_not_echoed(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);d=demo();d['secret']='DO_NOT_ECHO';(root/'in.json').write_text(json.dumps(d))
   p=subprocess.run([sys.executable,str(BASE/'scripts/diagnose.py'),'--input',str(root/'in.json'),'--output-dir',str(root/'out')],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0);self.assertNotIn('DO_NOT_ECHO',p.stdout+p.stderr);self.assertFalse((root/'out').exists())

if __name__=='__main__':unittest.main()
