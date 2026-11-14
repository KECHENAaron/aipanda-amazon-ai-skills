"""Regressions for catalog scope, safe launch behavior and generated page. MIT."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from project_catalog import load_catalog, validate_catalog, public_file
from build_start_page import render
from run_demo import run_demo


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.data = load_catalog()

    def rejects(self, change):
        data = copy.deepcopy(self.data)
        change(data)
        with self.assertRaises(ValueError):
            validate_catalog(data)

    def test_all_published_skills_and_demos_are_listed(self):
        self.assertEqual(len(self.data['skills']), 7)
        self.assertEqual(len(self.data['demos']), 11)
        self.assertEqual(sum(s['kind'] == 'script' for s in self.data['skills']), 5)

    def test_missing_skill_is_detected(self):
        self.rejects(lambda d: d['skills'].pop())

    def test_duplicate_skill_is_rejected(self):
        self.rejects(lambda d: d['skills'].append(d['skills'][0]))

    def test_community_cannot_be_relicensed_mit(self):
        self.rejects(lambda d: d['skills'][-1].update(license='MIT', license_path='LICENSE'))

    def test_workflow_cannot_claim_script_runtime(self):
        self.rejects(lambda d: d['skills'][2].update(runtime='stdlib'))

    def test_duplicate_demo_is_rejected(self):
        self.rejects(lambda d: d['demos'].append(d['demos'][0]))

    def test_arbitrary_script_cannot_be_launched(self):
        self.rejects(lambda d: d['demos'][0].update(script='tools/check_project.py'))

    def test_input_cannot_escape_packaged_fixture(self):
        self.rejects(lambda d: d['demos'][0].update(input='skills/aipanda-search-term-audit/assets/../../README.md'))

    def test_control_demo_cannot_use_search_scope(self):
        self.rejects(lambda d: d['demos'][-1].update(scope=d['demos'][0]['scope']))

    def test_unknown_fields_are_rejected(self):
        self.rejects(lambda d: d.update(command='arbitrary shell text'))

    def test_path_symlink_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'; root.mkdir()
            source = Path(tmp) / 'outside.txt'; source.write_text('outside')
            (root / 'link.txt').symlink_to(source)
            with self.assertRaises(ValueError):
                public_file(root, 'link.txt')

    def test_generated_page_matches_and_escapes_metadata(self):
        self.assertEqual((ROOT / 'docs/start.html').read_text(), render(self.data))
        altered = copy.deepcopy(self.data)
        altered['skills'][0]['title'] = '<b>title</b>'
        self.assertIn('&lt;b&gt;title&lt;/b&gt;', render(altered))


class LauncherTests(unittest.TestCase):
    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'existing'; out.mkdir()
            sentinel = out / 'sentinel.txt'; sentinel.write_text('keep')
            with self.assertRaises(ValueError):
                run_demo(load_catalog()['demos'][0], out)
            self.assertEqual(sentinel.read_text(), 'keep')
            self.assertEqual(list(out.iterdir()), [sentinel])

    def test_unknown_demo_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'not-created'
            p = subprocess.run([sys.executable, str(ROOT / 'tools/run_demo.py'), '--demo', 'unknown', '--output-dir', str(out)], capture_output=True)
            self.assertEqual(p.returncode, 2)
            self.assertFalse(out.exists())

    def test_list_has_no_execution_side_effect(self):
        p = subprocess.run([sys.executable, str(ROOT / 'tools/run_demo.py'), '--list'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(p.stdout.splitlines()), 11)

    def test_default_output_is_unique_and_complete(self):
        # Supply an isolated system temporary base; runner must choose fresh children.
        import os
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, TMPDIR=tmp, TEMP=tmp, TMP=tmp)
            for _ in range(2):
                p = subprocess.run([sys.executable, str(ROOT / 'tools/run_demo.py'), '--demo', 'ads-bid'], capture_output=True, text=True, env=env)
                self.assertEqual(p.returncode, 0, p.stderr)
            outputs = list(Path(tmp).glob('aipanda-demo-*/report'))
            self.assertEqual(len(outputs), 2)
            self.assertTrue(all((p / 'report.html').is_file() and (p / 'report.json').is_file() for p in outputs))


if __name__ == '__main__':
    unittest.main()
