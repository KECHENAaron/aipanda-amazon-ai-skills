"""Validated metadata for the public skill chooser and synthetic demos. MIT."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SCRIPTS = {
    'skills/aipanda-search-term-audit/scripts/audit.py',
    'skills/aipanda-ads-period-review/scripts/review.py',
    'skills/aipanda-ads-period-review/scripts/diagnose.py',
    'skills/aipanda-ads-period-review/scripts/control_scenarios.py',
}


def public_file(root, value):
    """Require a tracked-style relative path contained in this source tree."""
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('catalog path must be relative')
    p = Path(value)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('catalog path escapes the source tree')
    resolved = (root / p).resolve()
    if root.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError('catalog file missing or outside source tree')
    return resolved


def validate_catalog(data, root=ROOT):
    if set(data) != {'schema_version', 'project_version', 'skills', 'demos'}:
        raise ValueError('unexpected catalog fields')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('unsupported catalog schema')
    if not re.fullmatch(r'\d+\.\d+\.\d+', data['project_version']):
        raise ValueError('invalid project version')
    if not isinstance(data['skills'], list) or not data['skills']:
        raise ValueError('skills must be a nonempty list')
    if not isinstance(data['demos'], list):
        raise ValueError('demos must be a list')
    skill_ids = set()
    paths = set()
    skill_keys = {'id', 'title', 'category', 'kind', 'runtime', 'license',
                  'license_path', 'path', 'summary', 'dependencies', 'case_page'}
    for s in data['skills']:
        if set(s) != skill_keys or any(not isinstance(s[k], str) or not s[k].strip()
                                     for k in skill_keys - {'case_page'}):
            raise ValueError('invalid skill fields')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', s['id']) or s['id'] in skill_ids:
            raise ValueError('duplicate or invalid skill id')
        skill_ids.add(s['id'])
        if s['path'] in paths:
            raise ValueError('duplicate skill path')
        paths.add(s['path'])
        if s['category'] not in {'ads', 'listing', 'research', 'images'}:
            raise ValueError('unknown skill category')
        if s['kind'] not in {'script', 'workflow'} or s['runtime'] not in {'stdlib', 'third_party', 'optional', 'instructions'}:
            raise ValueError('unknown runtime')
        if (s['kind'] == 'workflow') != (s['runtime'] == 'instructions'):
            raise ValueError('workflow/runtime mismatch')
        if s['path'].startswith('skills/'):
            if s['license'] != 'MIT' or s['license_path'] != 'LICENSE':
                raise ValueError('MIT license scope mismatch')
        elif s['path'].startswith('community/ivyeaops/'):
            if s['license'] != 'AGPL-3.0' or s['license_path'] != s['path'] + '/LICENSE':
                raise ValueError('community license scope mismatch')
        else:
            raise ValueError('unknown skill root')
        skill_text = public_file(root, s['path'] + '/SKILL.md').read_text(encoding='utf-8')
        if not re.search(r'^name: ' + re.escape(s['id']) + r'\s*$', skill_text, re.M):
            raise ValueError('skill name mismatch')
        public_file(root, s['license_path'])
        if s['case_page'] is not None:
            public_file(root, 'docs/' + s['case_page'])
    actual = {p.parent.relative_to(root).as_posix()
              for folder in ['skills', 'community/ivyeaops']
              for p in (root / folder).rglob('SKILL.md')}
    if paths != actual:
        raise ValueError('catalog does not cover the published skills')
    demo_ids = set()
    for d in data['demos']:
        if set(d) != {'id', 'title', 'skill_id', 'script', 'input', 'scope', 'preview'}:
            raise ValueError('unexpected demo fields')
        if not isinstance(d['id'], str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', d['id']) or d['id'] in demo_ids:
            raise ValueError('duplicate or invalid demo id')
        demo_ids.add(d['id'])
        s = next((s for s in data['skills'] if s['id'] == d['skill_id']), None)
        if not s or s['license'] != 'MIT' or s['kind'] != 'script':
            raise ValueError('unified demos must belong to original runnable skills')
        if d['script'] not in ALLOWED_SCRIPTS or not d['script'].startswith(s['path'] + '/'):
            raise ValueError('unapproved demo script')
        public_file(root, d['script'])
        if not isinstance(d['input'], str) or not d['input'].startswith(s['path'] + '/assets/'):
            raise ValueError('demo input must be the packaged public fixture')
        public_file(root, d['input'])
        if not isinstance(d['preview'], str) or not d['preview'].startswith('docs/'):
            raise ValueError('demo preview must be a public page')
        public_file(root, d['preview'])
        if d['scope'] is not None:
            if d['script'] != 'skills/aipanda-search-term-audit/scripts/audit.py' or not d['scope'].startswith(s['path'] + '/assets/'):
                raise ValueError('unexpected demo scope')
            public_file(root, d['scope'])
        if not isinstance(d['title'], str) or not d['title'].strip():
            raise ValueError('demo title missing')
    return data


def load_catalog(root=ROOT):
    return validate_catalog(json.loads((root / 'docs/catalog.json').read_text(encoding='utf-8')), root)
