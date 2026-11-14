#!/usr/bin/env python3
"""Run only bundled synthetic MIT demos. No account, network, or private input. MIT."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

from project_catalog import ROOT, load_catalog, public_file


def run_demo(demo, output, root=ROOT):
    """Use the current interpreter; never invoke a shell or accept arbitrary input."""
    destination = Path(output).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('output directory already exists; choose a new directory')
    command = [sys.executable, str(public_file(root, demo['script'])),
               '--input', str(public_file(root, demo['input']))]
    if demo['scope'] is not None:
        command.extend(['--scope', str(public_file(root, demo['scope']))])
    command.extend(['--output-dir', str(destination)])
    try:
        subprocess.run(command, check=True, cwd=root, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        raise RuntimeError('bundled synthetic demo failed') from None
    for name in ['report.html', 'report.json']:
        if not (destination / name).is_file():
            raise RuntimeError('demo did not produce both report files')
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--list', action='store_true', help='list bundled synthetic demos')
    mode.add_argument('--demo', help='demo id from --list')
    parser.add_argument('--output-dir', help='new output directory; default is a unique system temporary directory')
    args = parser.parse_args(argv)
    try:
        data = load_catalog()
        if args.list:
            if args.output_dir is not None:
                parser.error('--output-dir requires --demo')
            for d in data['demos']:
                print(d['id'] + '\t' + d['title'])
            return 0
        demo = next((d for d in data['demos'] if d['id'] == args.demo), None)
        if demo is None:
            parser.error('unknown demo; use --list')
        output = args.output_dir
        if output is None:
            output = Path(tempfile.mkdtemp(prefix='aipanda-demo-')) / 'report'
        destination = run_demo(demo, output)
        print('Synthetic demo complete. Open: ' + str(destination / 'report.html'))
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        # No user-supplied datasets are accepted by this launcher.
        print('Demo failed: ' + type(exc).__name__ + '; check the source fixture and choose a new output directory.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
