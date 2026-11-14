"""Public constants only. Does not read reports, private files, or the network. MIT."""
import copy
import json
from pathlib import Path

KINDS = ('supported', 'conflicts', 'boundaries')


def fact(i, attr, val, unit='count', variant='VAR-A', source='SRC-001'):
    return dict(id='EV-' + i, source_id=source, unit='UNIT-A', variant=variant,
                batch='BATCH-A', component='PART-ALL', attribute=attr,
                condition='COND-A', value=val, measure_unit=unit)


def claim(i, attr, val, refs, unit='count'):
    r = fact(i, attr, val, unit)
    del r['source_id']; r['id'] = 'CLAIM-' + i; r['evidence_ids'] = refs
    return r


def demo(kind):
    if kind not in KINDS:
        raise ValueError('unknown_demo')
    data = dict(schema_version=1, data_kind='synthetic', snapshot_date='2026-03-02', max_age_days=30,
                sources=[dict(id='SRC-001', observed_date='2026-03-01', access='provided')])
    if kind == 'supported':
        data['facts'] = [fact('001', 'ATTR-001', 10, 'cm'), fact('002', 'ATTR-002', 1), fact('003', 'ATTR-003', True, 'bool')]
        data['claims'] = [claim('001', 'ATTR-001', 10, ['EV-001'], 'cm'), claim('002', 'ATTR-002', 1, ['EV-002']), claim('003', 'ATTR-003', True, ['EV-003'], 'bool')]
    elif kind == 'conflicts':
        data['facts'] = [fact('001', 'ATTR-001', 10, 'cm'), fact('002', 'ATTR-001', 20, 'cm'), fact('003', 'ATTR-002', 1)]
        data['claims'] = [claim('001', 'ATTR-001', 10, ['EV-001'], 'cm'), claim('002', 'ATTR-002', 2, ['EV-003']), claim('003', 'ATTR-003', True, [], 'bool')]
    else:
        data['sources'].append(dict(id='SRC-002', observed_date='2026-01-01', access='unavailable'))
        data['facts'] = [fact('001', 'ATTR-001', 10, variant='VAR-B'), fact('002', 'ATTR-002', 10, 'mm'), fact('003', 'ATTR-003', None, source='SRC-002')]
        data['claims'] = [claim('001', 'ATTR-001', 10, ['EV-001']), claim('002', 'ATTR-002', 10, ['EV-002'], 'cm'), claim('003', 'ATTR-003', 0, ['EV-003'])]
    return copy.deepcopy(data)


if __name__ == '__main__':
    paths = [Path(__file__).resolve().parents[1] / 'assets' / (k + '.json') for k in KINDS]
    if any(p.exists() for p in paths):
        raise SystemExit('Refusing to overwrite existing fixtures.')
    for kind, path in zip(KINDS, paths):
        path.write_text(json.dumps(demo(kind), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
