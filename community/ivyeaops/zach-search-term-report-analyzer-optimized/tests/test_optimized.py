import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_analysis import analyze, load_config
import analyze_search_term_decisions as engine


class OptimizedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def args(self,rows,**changes):
        f=self.root/'report.csv';pd.DataFrame(rows).to_csv(f,index=False)
        values=dict(input_file=str(f),asin='B0DEMO0001',brand='DemoBrand',mode='auto',start_date='2026-10-01',end_date='2026-10-30',deduplicate=False,config=None,live_listing=False,listing_context_file=None,site='US',report_type='SP',target_acos=None)
        values.update(changes);return argparse.Namespace(**values)
    def row(self,**changes):
        return dict(asin='B0DEMO0001',search_term='white bounce house',clicks=20,spend=20,orders=2,sales=200,match_type='exact',**changes)
    def test_aggregate_has_no_fake_daily_windows(self):
        frame,summary=analyze(self.args([self.row()]))
        self.assertEqual(summary['input_mode'],'aggregate');self.assertFalse(any(c.startswith(('7d_','14d_','30d_')) for c in frame));self.assertEqual(frame['period_clicks'].sum(),20)
    def test_daily_match_types_align_stably(self):
        a=self.row(date='2026-10-05');a['match_type']='broad'
        b=self.row(date='2026-10-25')
        frame,_=analyze(self.args([a,b]));self.assertEqual(len(frame),1);self.assertEqual(frame.iloc[0]['7d_clicks'],20);self.assertEqual(frame.iloc[0]['30d_clicks'],40)
    def test_missing_conversion_is_not_zero_order(self):
        row=self.row();row.pop('orders');row.pop('sales')
        frame,summary=analyze(self.args([row]));self.assertFalse(summary['orders_complete']);self.assertIsNone(summary['reference_acos']);self.assertEqual(frame.iloc[0]['decision_tag'],'manual_review');self.assertTrue(pd.isna(frame.iloc[0]['period_orders']))
    def test_invalid_number_rejected(self):
        row=self.row();row['spend']='oops'
        with self.assertRaises(ValueError):analyze(self.args([row]))
    def test_invalid_date_not_silently_dropped(self):
        with self.assertRaises(ValueError):analyze(self.args([self.row(date='invalid')]))
    def test_missing_aggregate_window_rejected(self):
        with self.assertRaises(ValueError):analyze(self.args([self.row()],start_date=None,end_date=None))
    def test_source_ids_keep_string_precision(self):
        row=self.row();row['Source Record ID']='00001234567890123456'
        frame,_=analyze(self.args([row]));self.assertIn('00001234567890123456',frame.iloc[0]['source_entities'])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):analyze(self.args([self.row(),self.row()]))
    def test_other_asin_excluded(self):
        other=self.row();other['asin']='B0PUBLIC01';other['spend']=100
        frame,s=analyze(self.args([self.row(),other]));self.assertEqual(s['excluded_other_asin'],1);self.assertEqual(frame['period_spend'].sum(),20)
    def test_nan_config_rejected(self):
        f=self.root/'config.json';f.write_text('{"thresholds":{"min_clicks_for_priority":NaN}}')
        with self.assertRaises(ValueError):load_config(f)
    def test_frequency_is_not_verified_competitor_brand(self):
        frame,_=analyze(self.args([self.row()]));self.assertNotEqual(frame.iloc[0]['term_category'],'competitor_term')
    def test_multiword_brand_does_not_match_one_generic_word(self):
        f=self.root/'config.json';f.write_text(json.dumps({'competitor_brands':['Little Tikes']}))
        a=self.row();a['search_term']='little bounce house'
        b=self.row();b['search_term']='little tikes bounce house'
        frame,_=analyze(self.args([a,b],config=str(f)));categories=dict(zip(frame['search_term'],frame['term_category']))
        self.assertNotEqual(categories[a['search_term']],'competitor_term');self.assertEqual(categories[b['search_term']],'competitor_term')
    def test_zero_clicks_reference_cvr_is_unknown(self):
        r=self.row();r['clicks']=0;r['orders']=0
        _,s=analyze(self.args([r]));self.assertIsNone(s['reference_cvr'])
    def test_daily_window_uses_declared_end(self):
        a=self.row(date='2026-10-20');b=self.row(date='2026-10-25')
        frame,_=analyze(self.args([a,b]));self.assertEqual(frame.iloc[0]['7d_clicks'],20)
    def test_empty_recent_window_reports_coverage_problem(self):
        with self.assertRaisesRegex(ValueError,'数据覆盖'):analyze(self.args([self.row(date='2026-08-01')],start_date='2026-08-01',end_date='2026-10-30'))

if __name__=='__main__':unittest.main()
