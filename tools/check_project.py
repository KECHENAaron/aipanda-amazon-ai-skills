#!/usr/bin/env python3
"""Offline metadata, generated-page, syntax, links and optional demo checks. MIT."""
import argparse
import ast
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urlsplit

from build_start_page import render
from project_catalog import ROOT, load_catalog
from run_demo import run_demo


class HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src'} and value:
                self.links.append(value)
            if key == 'id' and value:
                self.ids.add(value)


def source_files(root):
    excluded = {'__pycache__', '.venv', '.git', 'outputs', 'runtime', 'private-data'}
    files = list(root.glob('*.md'))
    files.extend(p for folder in ['docs', 'skills', 'community', 'tools', 'tests', 'cases']
                 for p in (root / folder).rglob('*')
                 if p.is_file() and not excluded.intersection(p.relative_to(root).parts))
    return sorted(set(files))


def check(root=ROOT, replay=False):
    data = load_catalog(root)
    version = data['project_version']
    if ('当前版本：' + version not in (root / 'README.md').read_text(encoding='utf-8')
            or 'v' + version not in (root / 'docs/index.html').read_text(encoding='utf-8')
            or '## ' + version + ' ' not in (root / 'CHANGELOG.md').read_text(encoding='utf-8')):
        raise ValueError('project version differs between catalog and public entrypoints')
    if (root / 'docs/start.html').read_text(encoding='utf-8') != render(data):
        raise ValueError('generated beginner page differs from catalog')
    links_checked = 0
    for p in source_files(root):
        if p.suffix not in {'.py', '.json', '.md', '.html'}:
            continue
        text = p.read_text(encoding='utf-8')
        if p.suffix == '.py':
            ast.parse(text, filename=p.name)
        elif p.suffix == '.json':
            json.loads(text)
        links = []
        if p.suffix == '.html':
            parsed = HTML(); parsed.feed(text); links = parsed.links
        elif p.suffix == '.md':
            links = re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)', text)
        for href in links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = p.parent / unquote(url.path) if url.path else p
            if not target.exists():
                raise ValueError('broken relative link in ' + p.relative_to(root).as_posix())
            if target.suffix == '.html' and url.fragment:
                dest = HTML(); dest.feed(target.read_text(encoding='utf-8'))
                if unquote(url.fragment) not in dest.ids:
                    raise ValueError('broken HTML anchor in ' + p.relative_to(root).as_posix())
            links_checked += 1
    outputs = 0
    if replay:
        with tempfile.TemporaryDirectory(prefix='aipanda-replay-') as temp:
            for d in data['demos']:
                out = run_demo(d, Path(temp) / d['id'], root)
                for suffix in ['html', 'json']:
                    name = 'report.' + suffix
                    preview = (root / d['preview']).with_suffix('.' + suffix)
                    if (out / name).read_bytes() != preview.read_bytes():
                        raise ValueError('published report differs from replay: ' + d['id'])
                    outputs += 1
    return {'status': 'PASS', 'skills': len(data['skills']), 'demos': len(data['demos']),
            'relative_links_checked': links_checked, 'generated_page_matches': True,
            'replay_outputs_byte_identical': outputs, 'network_requests': 0,
            'limit': 'Static checks and synthetic replays do not verify live accounts or business outcomes.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-demos', action='store_true', help='run all bundled demos and compare both reports with public previews')
    args = parser.parse_args()
    try:
        print(json.dumps(check(replay=args.replay_demos), ensure_ascii=False, indent=2))
    except (ValueError, OSError, SyntaxError, RuntimeError) as exc:
        parser.exit(1, type(exc).__name__ + ': ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
