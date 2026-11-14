"""Behavioral tests using only public, independently constructed fixtures. MIT."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LISTING = ROOT / 'skills/aipanda-listing-evidence'
COMPETITOR = ROOT / 'skills/aipanda-competitor-evidence'


def module(path, name):
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        return m
    finally:
        sys.path.pop(0)


listing = module(LISTING / 'scripts/audit.py', 'listing_new_audit')
competitor = module(COMPETITOR / 'scripts/compare.py', 'competitor_new_compare')
lg = module(LISTING / 'scripts/make_demo.py', 'listing_new_demo')
cg = module(COMPETITOR / 'scripts/make_demo.py', 'competitor_new_demo')
core = module(LISTING / 'scripts/evidence_core.py', 'new_evidence_core')


class ListingTests(unittest.TestCase):
    def test_supported_is_only_input_consistency(self):
        r = listing.analyze(lg.demo('supported'))
        self.assertTrue(all(x['status'] == 'SUPPORTED_BY_INPUT' and not x['copy_semantics_verified'] and not x['executable'] for x in r['claims']))
        self.assertFalse(r['source_authenticity_verified'])
        self.assertEqual(r['max_age_days'],30)

    def test_uncited_conflict_cannot_be_hidden(self):
        r = listing.analyze(lg.demo('conflicts'))['claims'][0]
        self.assertEqual(r['status'], 'CONFLICT')
        self.assertIn({'evidence_id': 'EV-002', 'cited': False, 'reasons': []}, r['matching_evidence'])
        self.assertIsNone(r['draft_value'])

    def test_contradicted_claim_is_not_rewritten_as_supported(self):
        self.assertEqual(listing.analyze(lg.demo('conflicts'))['claims'][1]['status'], 'CONTRADICTED')

    def test_empty_fact_pool_is_explicitly_missing(self):
        d = lg.demo('supported'); d.update(facts=[], sources=[])
        for c in d['claims']: c['evidence_ids'] = []
        self.assertTrue(all(c['status'] == 'MISSING_EVIDENCE' for c in listing.analyze(d)['claims']))

    def test_matching_fact_without_citation_is_not_approved(self):
        d = lg.demo('supported'); d['claims'][0]['evidence_ids'] = []
        self.assertEqual(listing.analyze(d)['claims'][0]['status'], 'MISSING_CITATION')

    def test_binding_dimensions_are_not_interchangeable(self):
        for field, val in [('unit','UNIT-B'),('variant','VAR-B'),('batch','BATCH-B'),('component','PART-B'),('condition','COND-B'),('attribute','ATTR-OTHER')]:
            with self.subTest(field=field):
                d = lg.demo('supported'); d['facts'][0][field] = val
                self.assertEqual(listing.analyze(d)['claims'][0]['status'], 'NOT_APPLICABLE')

    def test_units_are_not_silently_converted(self):
        d = lg.demo('supported'); d['facts'][0]['measure_unit'] = 'mm'
        self.assertIn('measure_unit_mismatch', listing.analyze(d)['claims'][0]['reasons'])

    def test_unknown_fact_is_not_zero(self):
        d = lg.demo('supported'); d['facts'][0]['value'] = None; d['claims'][0]['value'] = 0
        r = listing.analyze(d)['claims'][0]
        self.assertEqual(r['status'], 'REVIEW_REQUIRED'); self.assertIsNone(r['draft_value'])

    def test_stale_or_unavailable_source_blocks_support(self):
        for change in [dict(observed_date='2026-01-01'), dict(access='unavailable')]:
            d = lg.demo('supported'); d['sources'][0].update(change)
            self.assertTrue(all(x['status'] == 'REVIEW_REQUIRED' for x in listing.analyze(d)['claims']))

    def test_future_source_is_rejected(self):
        d = lg.demo('supported'); d['sources'][0]['observed_date'] = '2026-04-01'
        with self.assertRaises(ValueError): listing.analyze(d)

    def test_unknown_and_duplicate_references_are_rejected(self):
        for refs in [['EV-UNKNOWN'], ['EV-001','EV-001']]:
            d = lg.demo('supported'); d['claims'][0]['evidence_ids'] = refs
            with self.assertRaises(ValueError): listing.analyze(d)

    def test_additional_business_fields_are_rejected(self):
        d = lg.demo('supported'); d['claims'][0]['store_name'] = 'PRIVATE-SENTINEL'
        with self.assertRaisesRegex(ValueError, '^invalid_fields$'): listing.analyze(d)

    def test_null_claim_and_duplicate_fact_ids_are_rejected(self):
        d = lg.demo('supported'); d['claims'][0]['value'] = None
        with self.assertRaises(ValueError): listing.analyze(d)
        d = lg.demo('supported'); d['facts'].append(d['facts'][0])
        with self.assertRaises(ValueError): listing.analyze(d)

    def test_scope_is_not_externally_verified(self):
        d = lg.demo('supported'); d['data_kind'] = 'anonymized_local'
        r = listing.analyze(d); self.assertFalse(r['binding_independently_verified'])
        self.assertIn('不供公开', core.html_report(r, 'Report', 'claims', [('status','State')]))


class CompetitorTests(unittest.TestCase):
    def first(self, d): return competitor.analyze(d)['comparisons'][0]

    def test_pack_normalization_is_exact(self):
        r = self.first(cg.demo('normalized'))
        self.assertEqual(r['normalized_per_item_values'], ['10','10'])
        self.assertEqual(r['delta_exact'], '0'); self.assertTrue(r['equal_by_input'])

    def test_fractional_results_preserve_exact_arithmetic(self):
        d = cg.demo('normalized'); d['entities'][1]['pack_count'] = 3
        r = self.first(d); self.assertEqual(r['normalized_per_item_values'], ['10','20/3'])
        self.assertEqual(r['delta_exact'], '-10/3'); self.assertEqual(r['relative_change_exact'], '-1/3')

    def test_unknown_pack_count_is_not_one(self):
        d = cg.demo('normalized'); d['entities'][1]['pack_count'] = None
        self.assertIn('unknown_pack_count', self.first(d)['reasons'])

    def test_non_additive_pack_values_are_not_divided(self):
        d = cg.demo('normalized')
        for o in d['observations']: o['aggregation'] = 'non_additive'
        r = self.first(d); self.assertIn('non_additive_pack_value', r['reasons'])
        self.assertIsNone(r['normalized_per_item_values'])

    def test_observed_estimated_and_methods_are_separate(self):
        d = cg.demo('scope-mismatch'); r = competitor.analyze(d)['comparisons'][1]
        self.assertIn('kind_mismatch',r['reasons']); self.assertIn('method_mismatch',r['reasons'])

    def test_window_and_coverage_mismatch_block_comparison(self):
        r = competitor.analyze(cg.demo('scope-mismatch'))['comparisons']
        self.assertIn('window_start_mismatch',r[0]['reasons']); self.assertIn('coverage_mismatch',r[2]['reasons'])

    def test_unknown_is_not_zero(self):
        r = competitor.analyze(cg.demo('missing'))['comparisons'][1]
        self.assertIn('unknown_value',r['reasons']); self.assertIsNone(r['delta_exact'])

    def test_zero_denominator_retains_delta(self):
        d = cg.demo('normalized'); d['observations'][0]['value'] = 0
        r = self.first(d); self.assertEqual(r['delta_exact'],'10'); self.assertIsNone(r['relative_change_exact'])
        self.assertEqual(r['relative_unavailable_reason'],'zero_baseline')

    def test_multiple_sources_are_not_cherry_picked(self):
        r = competitor.analyze(cg.demo('missing'))['comparisons'][-1]
        self.assertIn('multiple_observations_no_selection',r['reasons'])
        self.assertEqual(r['peer_observation_ids'],['OBS-008','OBS-009'])

    def test_comparison_group_must_match(self):
        d = cg.demo('normalized'); d['entities'][1]['comparison_group'] = 'GROUP-B'
        self.assertIn('comparison_group_mismatch',self.first(d)['reasons'])

    def test_variants_cannot_be_misbound(self):
        d = cg.demo('normalized'); d['observations'][0]['variant'] = 'VAR-B'
        with self.assertRaises(ValueError): competitor.analyze(d)

    def test_future_or_reversed_window_rejected(self):
        for start,end in [('2026-02-08','2026-02-07'),('2026-02-01','2026-04-01')]:
            d = cg.demo('normalized'); d['observations'][0].update(window_start=start,window_end=end)
            with self.assertRaises(ValueError): competitor.analyze(d)

    def test_per_item_does_not_need_pack_count(self):
        d = cg.demo('normalized'); d['entities'][0]['pack_count'] = None
        self.assertEqual(self.first(d)['status'],'COMPARABLE_BY_INPUT')

    def test_boolean_does_not_gain_zero_baseline_math(self):
        d = cg.demo('normalized')
        for o in d['observations']: o.update(value=False,measure_unit='bool',basis='per_item',aggregation='non_additive')
        r = self.first(d); self.assertTrue(r['equal_by_input']); self.assertIsNone(r['relative_unavailable_reason'])

    def test_numeric_measure_units_do_not_auto_convert(self):
        d = cg.demo('normalized'); d['observations'][1]['measure_unit'] = 'cm'
        self.assertIn('measure_unit_mismatch',self.first(d)['reasons'])

    def test_prices_and_financial_units_are_not_in_contract(self):
        d = cg.demo('normalized'); d['observations'][0]['measure_unit'] = 'USD'
        with self.assertRaises(ValueError): competitor.analyze(d)

    def test_estimate_remains_a_declaration(self):
        d = cg.demo('normalized')
        for o in d['observations']: o['kind']='estimated'
        r = competitor.analyze(d); self.assertEqual(r['comparisons'][0]['status'],'COMPARABLE_BY_INPUT')
        self.assertEqual(r['max_age_days'],30)
        self.assertEqual(r['observations'][0]['kind'],'estimated'); self.assertFalse(r['source_authenticity_verified'])


class StandaloneAndInputTests(unittest.TestCase):
    def test_all_generator_fixtures_match_exactly(self):
        for package,generator in [(LISTING,lg),(COMPETITOR,cg)]:
            for kind in generator.KINDS:
                self.assertEqual(json.loads((package/'assets'/f'{kind}.json').read_text()),generator.demo(kind))

    def test_both_packages_run_without_repository_imports(self):
        with tempfile.TemporaryDirectory() as temp:
            for p,script,kind in [(LISTING,'audit.py','supported'),(COMPETITOR,'compare.py','normalized')]:
                dest=Path(temp)/p.name; shutil.copytree(p,dest); out=Path(temp)/(p.name+'-out')
                run=subprocess.run([sys.executable,str(dest/'scripts'/script),'--input',str(dest/'assets'/f'{kind}.json'),'--output-dir',str(out)],cwd=temp,capture_output=True,env={'PYTHONPATH':'','PYTHONIOENCODING':'utf-8'})
                self.assertEqual(run.returncode,0,run.stderr); self.assertTrue((out/'report.json').is_file())

    def test_existing_output_and_error_values_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'existing';out.mkdir();(out/'keep.txt').write_text('keep')
            for package,script,generator in [(LISTING,'audit.py',lg),(COMPETITOR,'compare.py',cg)]:
                source=Path(temp)/'input.json';d=generator.demo(generator.KINDS[0]);d['private_note']='DO-NOT-ECHO';source.write_text(json.dumps(d))
                run=subprocess.run([sys.executable,str(package/'scripts'/script),'--input',str(source),'--output-dir',str(out)],capture_output=True)
                self.assertEqual(run.returncode,2);self.assertNotIn(b'DO-NOT-ECHO',run.stdout+run.stderr)
                source.write_text(json.dumps(generator.demo(generator.KINDS[0])))
                run=subprocess.run([sys.executable,str(package/'scripts'/script),'--input',str(source),'--output-dir',str(out)],capture_output=True)
                self.assertEqual(run.returncode,2)
            self.assertEqual((out/'keep.txt').read_text(),'keep'); self.assertEqual(len(list(out.iterdir())),1)

    def test_duplicate_json_keys_and_nan_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.json'
            for text in ['{"a":1,"a":2}','{"a":NaN}']:
                p.write_text(text)
                with self.assertRaises(ValueError): core.load(p)

    def test_numeric_and_token_contracts(self):
        for val,unit in [(True,'cm'),(-1,'count'),(1.5,'count'),(float('inf'),'cm'),(0.0000000001,'cm'),('plain text','token')]:
            with self.subTest(value=val):
                with self.assertRaises(ValueError):core.value(val,unit)


if __name__ == '__main__':
    unittest.main()
