import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_evidence import audit


class EvidenceTests(unittest.TestCase):
    def data(self):
        return {'product':{'asin':'B0DEMO0001','marketplace':'US','sku':'sku','batch_id':'batch'},'sources':[{'id':'manual','reference':'original-label','observed_at':'2026-10-30','asin':'B0DEMO0001','marketplace':'US','sku':'sku','batch_id':'batch','verification':'reviewed_original'}],
            'claims':[{'id':'weight','field':'total_load','value':200,'unit':'lb','source_id':'manual'}],
            'copy_claims':[{'id':'bullet','location':'bullet','text':'200 lb','fact_ids':['weight']}]}
    def test_supported_current_original(self):
        a=audit(self.data(),'2026-10-30');self.assertEqual(a['facts'][0]['status'],'confirmed');self.assertEqual(a['copy_claims'][0]['status'],'references_validated_manual_text_review_required');self.assertFalse(a['copy_text_semantics_verified'])
    def test_conflict_blocks_copy(self):
        d=self.data();d['claims'].append({'id':'other','field':'total_load','value':300,'unit':'lb','source_id':'manual'});a=audit(d,'2026-10-30');self.assertEqual(a['facts'][0]['status'],'disputed');self.assertTrue(a['copy_claims'][0]['status'].startswith('blocked'))
    def test_historical_batch_not_current(self):
        d=self.data();d['sources'][0]['batch_id']='old';a=audit(d,'2026-10-30');self.assertEqual(a['facts'][0]['status'],'unverified')
    def test_other_asin_excluded(self):
        d=self.data();d['claims'][0]['asin']='B0PUBLIC01';a=audit(d,'2026-10-30');self.assertEqual(len(a['facts']),0);self.assertEqual(len(a['excluded_claims']),1)
    def test_reviews_dedup_and_unknown_variant(self):
        d=self.data();r={'id':'r1','asin':'B0DEMO0001','date':'2026-01-01','text':'test'};d['reviews']=[r,r,{'id':'r2','text':'unknown'}];a=audit(d,'2026-10-30');self.assertEqual(a['reviews']['duplicate_count'],1);self.assertEqual(a['reviews']['unknown_variant'],1);self.assertFalse(a['reviews']['population_complete'])
    def test_missing_copy_reference_blocks(self):
        d=self.data();d['copy_claims'][0]['fact_ids']=['missing'];self.assertTrue(audit(d,'2026-10-30')['copy_claims'][0]['status'].startswith('blocked'))
    def test_component_materials_not_false_conflict(self):
        d=self.data();d['claims']=[{'id':'a','field':'material','value':'Oxford','component':'wall','source_id':'manual'},{'id':'b','field':'material','value':'PVC','component':'floor','source_id':'manual'}];self.assertEqual([f['status'] for f in audit(d,'2026-10-30')['facts']],['confirmed','confirmed'])
    def test_future_source_date_rejected_for_confirmation(self):
        d=self.data();d['sources'][0]['observed_at']='2027-01-01';self.assertEqual(audit(d,'2026-10-30')['facts'][0]['status'],'unverified')
    def test_valid_reference_does_not_verify_arbitrary_copy(self):
        d=self.data();d['copy_claims'][0]['text']='An unsupported performance claim'
        a=audit(d,'2026-10-30')
        self.assertFalse(a['copy_claims'][0]['text_semantics_verified'])
        self.assertIn('manual_text_review',a['copy_claims'][0]['status'])

if __name__=='__main__':unittest.main()
