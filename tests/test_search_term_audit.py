import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/aipanda-search-term-audit'
spec = importlib.util.spec_from_file_location('audit', SKILL / 'scripts/audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SearchTermAuditTests(unittest.TestCase):
    def setUp(self):
        self.scope = json.loads((SKILL / 'assets/demo-scope.json').read_text())
        with (SKILL / 'assets/demo.csv').open() as f:
            reader = csv.DictReader(f)
            self.fields = reader.fieldnames
            self.rows = list(reader)

    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'data.csv'
            with file.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fields)
                writer.writeheader()
                writer.writerows(rows)
            return audit.analyze(file, self.scope)

    def test_demo_decisions_and_unknown_totals(self):
        r = self.run_rows(self.rows)
        terms = {x['search_term']: x for x in r['items']}
        self.assertEqual(r['totals']['spend'], 38)
        self.assertIsNone(r['totals']['clicks'])
        self.assertEqual(r['totals']['orders'], 3)
        self.assertEqual(terms['pool cover']['state'], '控费复核候选')
        self.assertAlmostEqual(terms['pool drain adapter']['derived']['acos'], 12/90, places=6)
        self.assertEqual(terms['fountain toy']['state'], '继续观察')
        self.assertIsNone(terms['outdoor pool accessory']['derived']['cpc'])
        self.assertEqual(terms['outdoor pool accessory']['source_lines'], [7])

    def test_duplicate_blocks(self):
        with self.assertRaisesRegex(ValueError, '重复'):
            self.run_rows(self.rows + [self.rows[0]])

    def test_scope_conflict_blocks(self):
        self.rows[0]['currency'] = 'EUR'
        with self.assertRaisesRegex(ValueError, '不一致'):
            self.run_rows(self.rows)

    def test_immature_is_not_stop_loss(self):
        self.scope['as_of'] = '2026-11-07'
        r = self.run_rows(self.rows)
        self.assertEqual(r['items'][0]['state'], '等待归因成熟')

    def test_zero_denominators_are_unknown(self):
        row = self.rows[0]
        for k in audit.METRICS: row[k] = '0'
        item = self.run_rows([row])['items'][0]
        self.assertTrue(all(v is None for v in item['derived'].values()))

    def test_nonfinite_negative_and_fractional_counts_rejected(self):
        for key, value in [('spend', 'NaN'), ('sales', 'Infinity'), ('spend', '-1'), ('clicks', '1.5')]:
            row = dict(self.rows[0], **{key: value})
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.run_rows([row])

    def test_contradictions_stay_in_review(self):
        row = dict(self.rows[0], clicks='0')
        item = self.run_rows([row])['items'][0]
        self.assertEqual(item['state'], '数据待核验')
        self.assertIn('零点击却有花费', item['issues'])

    def test_html_escapes_input(self):
        row = dict(self.rows[0], search_term='<script>alert(1)</script>')
        html = audit.render(self.run_rows([row]))
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_existing_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'output'; out.mkdir()
            marker = out / 'report.json'; marker.write_text('preserve')
            r = subprocess.run([sys.executable, str(SKILL / 'scripts/audit.py'), '--input', str(SKILL / 'assets/demo.csv'), '--scope', str(SKILL / 'assets/demo-scope.json'), '--output-dir', str(out)], capture_output=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(marker.read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()
