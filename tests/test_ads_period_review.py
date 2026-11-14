import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'skills/aipanda-ads-period-review'
def load(name,file):
 s=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
engine=load('period_review',BASE/'scripts/review.py')
generator=load('period_demo',BASE/'scripts/make_demo.py')

class PeriodReviewTests(unittest.TestCase):
 def test_unequal_days_distinguishes_total_from_daily(self):
  r=engine.review(generator.demo());self.assertEqual(r['status'],'COMPARABLE_DESCRIPTIVE')
  self.assertEqual(r['deltas']['totals']['sales']['relative'],1)
  self.assertEqual(r['deltas']['per_calendar_day']['sales']['relative'],0)
  self.assertEqual(r['deltas']['per_active_day']['spend']['relative'],-.25)
  self.assertEqual(r['periods']['before']['ratios']['acos'],.2)
 def test_weighted_ratio_and_mix_shift(self):
  r=engine.review(generator.demo('mix-shift'));self.assertTrue(r['mix_shift_warning'])
  self.assertEqual(r['periods']['before']['ratios']['acos'],.25)
  self.assertEqual(r['all_units_acos_worsened'],['UNIT-A','UNIT-B'])
  self.assertFalse(r['causal_effect_verified'])
 def test_immature_blocks_changes_but_keeps_raw_metrics(self):
  r=engine.review(generator.demo('immature'));self.assertEqual(r['status'],'BLOCKED_COMPARISON')
  self.assertEqual(r['periods']['after']['totals']['spend'],54)
  self.assertIsNone(r['deltas']['totals']['sales']['relative'])
 def test_missing_day_is_not_zero(self):
  d=generator.demo();d['rows'].pop();r=engine.review(d)
  self.assertEqual(r['status'],'BLOCKED_COMPARISON');self.assertIsNone(r['periods']['after']['totals']['spend'])
 def test_missing_metric_is_not_zero(self):
  d=generator.demo();d['rows'][0]['sales']=None;r=engine.review(d)
  self.assertIsNone(r['periods']['before']['totals']['sales']);self.assertEqual(r['status'],'BLOCKED_COMPARISON')
 def test_zero_denominators_are_unknown(self):
  d=generator.demo()
  for row in d['rows']:
   for k in engine.METRICS:row[k]=0
  r=engine.review(d);self.assertTrue(all(v is None for v in r['periods']['before']['ratios'].values()))
  self.assertIsNone(r['deltas']['totals']['sales']['relative'])
 def test_duplicate_daily_unit_rejected(self):
  d=generator.demo();d['rows'].append(copy.deepcopy(d['rows'][0]))
  with self.assertRaises(ValueError):engine.review(d)
 def test_overlap_rejected(self):
  d=generator.demo();d['periods'][1]['start_date']='2026-01-03'
  with self.assertRaises(ValueError):engine.review(d)
 def test_reversed_or_future_dates_rejected(self):
  for key,value in [('start_date','2026-02-01'),('end_date','2026-04-01')]:
   d=generator.demo();d['periods'][1][key]=value
   with self.assertRaises(ValueError):engine.review(d)
 def test_outside_date_rejected(self):
  d=generator.demo();d['rows'][0]['date']='2025-01-01'
  with self.assertRaises(ValueError):engine.review(d)
 def test_scope_unit_mismatch_rejected(self):
  d=generator.demo();d['rows'][0]['unit']='UNIT-Z'
  with self.assertRaises(ValueError):engine.review(d)
 def test_extra_product_or_cost_field_rejected(self):
  for field in ['asin','product_title','unit_cost','seller_name']:
   d=generator.demo();d[field]='not_for_output'
   with self.assertRaises(ValueError):engine.review(d)
 def test_nested_extra_field_rejected(self):
  d=generator.demo();d['rows'][0]['note']='private'
  with self.assertRaises(ValueError):engine.review(d)
 def test_free_text_events_rejected(self):
  d=generator.demo();d['events']=[{'period':'after','date':'2026-01-10','kind':'private free text'}]
  with self.assertRaises(ValueError):engine.review(d)
 def test_illegal_numbers_rejected(self):
  for key,value in [('spend','NaN'),('spend','Infinity'),('sales',-1),('clicks',1.5),('orders',True)]:
   d=generator.demo();d['rows'][0][key]=value
   with self.assertRaises(ValueError):engine.review(d)
 def test_unserializable_metric_magnitude_rejected(self):
  d=generator.demo();d["rows"][0]["spend"]="1e1000"
  with self.assertRaises(ValueError):engine.review(d)
 def test_contradictory_metrics_block_comparison(self):
  d=generator.demo();d['rows'][0]['clicks']=101
  self.assertEqual(engine.review(d)['status'],'BLOCKED_COMPARISON')
 def test_inactive_row_with_metrics_blocks(self):
  d=generator.demo();d['rows'][0]['active']=False
  self.assertEqual(engine.review(d)['status'],'BLOCKED_COMPARISON')
 def test_active_day_denominator_is_separate(self):
  d=generator.demo()
  for row in d['rows']:
   if row['period']=='before' and row['date']=='2026-01-03':
    row['active']=False
    for key in engine.METRICS:row[key]=0
  r=engine.review(d);b=r['periods']['before'];self.assertEqual(b['calendar_days'],3);self.assertEqual(b['active_days'],2)
  self.assertEqual(b['per_calendar_day']['spend'],8);self.assertEqual(b['per_active_day']['spend'],12)
 def test_lag_setting_is_not_assumed(self):
  d=generator.demo('immature');d['scope']['attribution_days']=1;d['scope']['reporting_lag_days']=0
  self.assertEqual(engine.review(d)['status'],'COMPARABLE_DESCRIPTIVE')
 def test_other_ad_type_or_attribution_basis_rejected(self):
  for key,value in [('ad_type','SB'),('attribution_basis','view')]:
   d=generator.demo();d['scope'][key]=value
   with self.assertRaises(ValueError):engine.review(d)
 def test_local_anonymized_input_label(self):
  d=generator.demo();d['data_kind']='anonymized_local';r=engine.review(d)
  self.assertIn('不供公开',engine.render(r));self.assertEqual(r['business_writes'],0)
 def test_published_inputs_are_exact_generator_outputs(self):
  for kind in ['unequal-days','immature','mix-shift']:
   self.assertEqual(json.loads((BASE/'assets'/f'{kind}.json').read_text()),generator.demo(kind))
 def test_existing_output_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'keep';p.mkdir();mark=p/'report.json';mark.write_text('preserve')
   r=subprocess.run([sys.executable,str(BASE/'scripts/review.py'),'--input',str(BASE/'assets/unequal-days.json'),'--output-dir',str(p)],capture_output=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(mark.read_text(),'preserve')
 def test_invalid_input_does_not_echo_values(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);d=generator.demo();d['private_field']='DO_NOT_ECHO_ME';(p/'input.json').write_text(json.dumps(d))
   r=subprocess.run([sys.executable,str(BASE/'scripts/review.py'),'--input',str(p/'input.json'),'--output-dir',str(p/'out')],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertNotIn('DO_NOT_ECHO_ME',r.stdout+r.stderr);self.assertFalse((p/'out').exists())

if __name__=='__main__':unittest.main()
