import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_brief import validate
from audit_image import audit


class QualityTests(unittest.TestCase):
    def brief(self):return {'product':{'asin':'B0DEMO0001','sku':'s','batch_id':'b'},'facts':[],'slots':[{'slot':1,'role':'main','question':'What is it?','background':'#FFFFFF','subject':'actual product','text_overlays':[],'callouts':[],'forbidden':['text']}]}
    def test_main_text_blocked(self):
        d=self.brief();d['slots'][0]['text_overlays']=['NEW'];self.assertIn('main_has_added_text',validate(d)['slots'][0]['blockers'])
    def test_unbound_claim_blocked(self):
        d=self.brief();d['slots'][0]['claims']=[{'text':'200lb','fact_ids':['missing']}];self.assertTrue(validate(d)['slots'][0]['blockers'])
    def test_quantitative_text_needs_declared_claim(self):
        d=self.brief();d['slots'].append(dict(d['slots'][0],slot=2,role='limits',text_overlays=['300 lb']));self.assertIn('quantitative_or_sensitive_text_without_claim',validate(d)['slots'][1]['blockers'])
    def test_comparison_needs_evidence(self):
        d=self.brief();d['slots'].append(dict(d['slots'][0],slot=2,role='comparison'));self.assertIn('comparison_evidence_missing',validate(d)['slots'][1]['blockers'])
    def test_no_forced_seven_slots_or_app(self):
        a=validate(self.brief());self.assertEqual(a['actual_slot_count'],1);self.assertEqual(a['status'],'BRIEF_CHECKED_DRAFT')
    def test_bom_needed_for_accessories(self):
        d=self.brief();d['slots'][0]['accessories_visible']=True;self.assertIn('main_accessories_not_bound_to_bom',validate(d)['slots'][0]['blockers'])
    def test_raster_white_is_not_final_compliance(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'white.png';Image.new('RGB',(1000,1000),'white').save(p);r=audit(p,True)
            self.assertEqual(r['near_white_edge_fraction'],1);self.assertEqual(r['status'],'NEEDS_HUMAN_REVIEW')
    def test_colored_background_flags_review(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'green.png';Image.new('RGB',(1000,1000),'green').save(p);self.assertIn('edge_not_near_white_review_background',audit(p,True)['issues'])

if __name__=='__main__':unittest.main()
