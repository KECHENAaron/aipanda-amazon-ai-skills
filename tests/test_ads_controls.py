import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
BASE=Path(__file__).resolve().parents[1]/'skills/aipanda-ads-period-review'
sys.path.insert(0,str(BASE/'scripts'))
from control_scenarios import assess,render
from make_control_demo import demo,KINDS

class ControlScenarioTests(unittest.TestCase):
 def first(self,r):return r['candidates'][0]
 def test_bid_scenario_separates_cpc_base_and_hypothesis(self):
  r=assess(demo('bid'));self.assertAlmostEqual(r['historical_cpc'],2/3,places=7);self.assertEqual(r['current']['base_bid'],.8)
  self.assertEqual(r['target_cost_cpc_reference'],1);self.assertEqual(r['fixed_only_placement_scenarios']['top']['proposed'],1.125)
  self.assertEqual(self.first(r)['state'],'REVIEW_ONLY');self.assertFalse(self.first(r)['executable'])
 def test_budget_increase_needs_constraint_not_just_efficiency(self):
  d=demo('budget')
  for row in d['daily']:row['budget_exhausted']=False
  c=self.first(assess(d));self.assertIn('no_declared_budget_constraint',c['blockers'])
 def test_budget_unknown_signal_blocks(self):
  d=demo('budget');d['daily'][0]['budget_exhausted']=None
  self.assertIn('budget_constraint_evidence_incomplete',self.first(assess(d))['blockers'])
 def test_budget_is_not_daily_hard_cap(self):
  d=demo('budget');d['current']['average_daily_budget']=18;d['proposal']['average_daily_budget']=19
  r=assess(d);self.assertEqual(self.first(r)['state'],'REVIEW_ONLY');self.assertFalse(r['budget_evidence']['daily_budget_is_hard_cap']);self.assertFalse(r['budget_evidence']['spend_cap_guaranteed'])
 def test_budget_positive_case(self):
  r=assess(demo('budget'));self.assertEqual(self.first(r)['state'],'REVIEW_ONLY');self.assertEqual(len(r['budget_evidence']['declared_exhausted_dates']),3)
 def test_placement_positive_case(self):
  r=assess(demo('placement'));self.assertEqual(self.first(r)['state'],'REVIEW_ONLY')
  self.assertEqual(r['fixed_only_placement_scenarios']['top']['current'],1);self.assertEqual(r['fixed_only_placement_scenarios']['top']['proposed'],1.2)
 def test_joint_effect_is_multiplicative_and_blocked(self):
  r=assess(demo('joint-change'));self.assertEqual(r['fixed_only_placement_scenarios']['top']['relative_change'],.925)
  self.assertTrue(all('multiple_levers_changed' in c['blockers'] for c in r['candidates']));self.assertTrue(all('exceeds_user_placement_adjusted_guardrail' in c['blockers'] for c in r['candidates']))
 def test_dynamic_bids_do_not_get_false_ceiling(self):
  for strategy in ['dynamic_down_only','dynamic_up_down','rule_based','unknown']:
   d=demo('bid');d['context']['strategy']=strategy;r=assess(d)
   self.assertFalse(r['scenario_ceiling_model_available']);self.assertTrue(all(x['proposed'] is None for x in r['fixed_only_placement_scenarios'].values()))
   self.assertIn('bid_strategy_or_adjustments_not_modelled',self.first(r)['blockers'])
 def test_extra_adjustments_and_mixed_bids_block_math(self):
  for k,v in [('other_bid_adjustments','present'),('other_bid_adjustments','unknown'),('bid_basis','mixed')]:
   d=demo('placement');d['context'][k]=v;r=assess(d);self.assertIsNone(r['fixed_only_placement_scenarios']['top']['proposed']);self.assertEqual(self.first(r)['state'],'BLOCKED')
 def test_budget_review_does_not_invent_dynamic_bid_ceiling(self):
  d=demo('budget');d['context']['strategy']='dynamic_up_down';r=assess(d)
  self.assertEqual(self.first(r)['state'],'REVIEW_ONLY');self.assertIsNone(r['fixed_only_placement_scenarios']['top']['proposed'])
 def test_current_snapshot_and_stability_gates(self):
  for k,v,code in [('configuration_as_of','2026-03-31','current_configuration_stale'),('observation_status','recent_change','observation_not_stable'),('state','paused','unit_paused'),('ownership','shared','ownership_not_exclusive'),('relevance','unknown','relevance_not_declared_supported'),('capacity','limited','capacity_not_declared_adequate'),('budget_rules','present','budget_rules_not_modelled'),('performance_scope','partial_or_unknown','campaign_scope_not_declared'),('placement_partition','unknown','placement_partition_not_declared')]:
   d=demo('budget');d['context'][k]=v;self.assertIn(code,self.first(assess(d))['blockers'])
 def test_immature_blocks_all_changes(self):
  d=demo('joint-change');d['window']['snapshot_date']='2026-03-09';d['context']['configuration_as_of']='2026-03-09'
  self.assertTrue(all('attribution_not_mature' in c['blockers'] for c in assess(d)['candidates']))
 def test_missing_day_is_not_zero(self):
  d=demo();d['daily'].pop();r=assess(d);self.assertIsNone(r['daily_summary']['totals']['spend']);self.assertIn('data_or_scope_issues',self.first(r)['blockers'])
 def test_duplicate_days_and_placements_rejected(self):
  for key in ['daily','placements']:
   d=demo();d[key].append(copy.deepcopy(d[key][0]))
   with self.assertRaises(ValueError):assess(d)
 def test_scope_reconciliation_blocks_placement(self):
  d=demo('placement');d['placements'][0]['spend']+=1;r=assess(d)
  self.assertEqual(r['placement_residual']['spend'],-1);self.assertIn('data_or_scope_issues',self.first(r)['blockers'])
 def test_missing_placement_is_not_zero(self):
  d=demo('placement');d['placements'].pop();r=assess(d)
  self.assertIsNone(r['placement_residual']['spend']);self.assertIn('data_or_scope_issues',self.first(r)['blockers'])
 def test_unknown_metrics_not_healthy(self):
  d=demo('bid');d['daily'][0]['sales']=None;r=assess(d)
  self.assertIsNone(r['daily_summary']['totals']['sales']);self.assertEqual(self.first(r)['state'],'BLOCKED')
 def test_placement_sample_and_efficiency_gate(self):
  d=demo('placement');d['guardrails']['min_orders']=8
  self.assertIn('placement_efficiency_not_supported',self.first(assess(d))['blockers'])
  d=demo('placement');d['guardrails']['target_acos']=.1
  self.assertIn('placement_efficiency_not_supported',self.first(assess(d))['blockers'])
 def test_direction_specific_reduction_gate(self):
  for kind,path in [('bid','base_bid'),('budget','average_daily_budget')]:
   d=demo(kind);d['proposal'][path]=round(d['current'][path]*.9,6)
   self.assertIn('reduction_not_supported_by_selected_metrics',self.first(assess(d))['blockers'])
   d['guardrails']['target_acos']=.1;self.assertEqual(self.first(assess(d))['state'],'REVIEW_ONLY')
 def test_placement_reduction_gate(self):
  d=demo('placement');d['proposal']['placement_pct']['top']=0
  self.assertIn('placement_reduction_not_supported',self.first(assess(d))['blockers'])
  d['guardrails']['target_acos']=.1;self.assertEqual(self.first(assess(d))['state'],'REVIEW_ONLY')
 def test_user_guardrails_are_not_platform_limits(self):
  for key,value,code in [('max_base_bid',.85,'exceeds_user_base_bid_guardrail'),('max_average_daily_budget',10,'exceeds_user_budget_guardrail'),('max_placement_adjusted_bid',1.1,'exceeds_user_placement_adjusted_guardrail')]:
   d=demo('bid');d['guardrails'][key]=value;self.assertIn(code,self.first(assess(d))['blockers'])
 def test_two_placement_changes_are_multiple_levers(self):
  d=demo('placement');d['proposal']['placement_pct']['rest']=10;r=assess(d)
  self.assertTrue(all('multiple_levers_changed' in c['blockers'] for c in r['candidates']))
 def test_no_change_has_no_candidate(self):
  d=demo();d['proposal']=copy.deepcopy(d['current']);r=assess(d)
  self.assertEqual(r['changed_levers'],[]);self.assertEqual(r['candidates'],[])
 def test_unknown_private_fields_rejected(self):
  for field in ['asin','seller_name','unit_cost','fees','comment']:
   d=demo();d[field]='not_for_output'
   with self.assertRaises(ValueError):assess(d)
  d=demo();d['context']['note']='not_for_output'
  with self.assertRaises(ValueError):assess(d)
 def test_invalid_numbers_rejected(self):
  for field,value in [('spend','NaN'),('clicks',1.5),('orders',True),('sales',-1)]:
   d=demo();d['daily'][0][field]=value
   with self.assertRaises(ValueError):assess(d)
  d=demo();d['proposal']['placement_pct']['top']=901
  with self.assertRaises(ValueError):assess(d)
 def test_unrepresentable_input_precision_rejected(self):
  d=demo();d["proposal"]["base_bid"]="1e-12"
  with self.assertRaises(ValueError):assess(d)
  d=demo();d["daily"][0]["spend"]="1e-12"
  with self.assertRaises(ValueError):assess(d)
 def test_inconsistent_metrics_block(self):
  d=demo();d['daily'][0]['clicks']=0
  self.assertEqual(self.first(assess(d))['state'],'BLOCKED')
 def test_scope_and_dates_rejected(self):
  d=demo();d['scope']['ad_type']='SB'
  with self.assertRaises(ValueError):assess(d)
  d=demo();d['context']['configuration_as_of']='2026-05-01'
  with self.assertRaises(ValueError):assess(d)
 def test_constant_fixture_generation(self):
  for kind in KINDS:self.assertEqual(json.loads((BASE/f'assets/control-{kind}.json').read_text()),demo(kind))
 def test_declarations_not_independently_verified(self):
  r=assess(demo());self.assertFalse(r['source_declarations_independently_verified']);self.assertFalse(r['causal_effect_verified']);self.assertFalse(self.first(r)['live_state_independently_verified']);self.assertEqual(r['business_writes'],0)
 def test_local_label_not_for_publication(self):
  d=demo();d['data_kind']='anonymized_local';self.assertIn('不供公开',render(assess(d)))
 def test_existing_outputs_preserved_and_bad_values_not_echoed(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);out=p/'out';out.mkdir();mark=out/'report.json';mark.write_text('preserve')
   r=subprocess.run([sys.executable,str(BASE/'scripts/control_scenarios.py'),'--input',str(BASE/'assets/control-bid.json'),'--output-dir',str(out)],capture_output=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(mark.read_text(),'preserve')
   d=demo();d['unknown']='DO_NOT_ECHO';(p/'in.json').write_text(json.dumps(d))
   r=subprocess.run([sys.executable,str(BASE/'scripts/control_scenarios.py'),'--input',str(p/'in.json'),'--output-dir',str(p/'new')],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertNotIn('DO_NOT_ECHO',r.stdout+r.stderr);self.assertFalse((p/'new').exists())

if __name__=='__main__':unittest.main()
