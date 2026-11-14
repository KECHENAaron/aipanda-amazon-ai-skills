"""Public constants only; no actual item, price, seller, or business data. MIT."""
import copy
import json
from pathlib import Path

KINDS = ('normalized', 'scope-mismatch', 'missing')


def observation(i, entity, attr, val, basis='per_item', aggregation='additive'):
    return dict(id='OBS-' + i, source_id='SRC-001', entity_id=entity, variant='VAR-A',
                attribute=attr, value=val, measure_unit='count', kind='observed',
                method='METHOD-A', coverage='COVER-A', window_start='2026-02-01',
                window_end='2026-02-07', basis=basis, aggregation=aggregation)


def demo(kind):
    if kind not in KINDS:
        raise ValueError('unknown_demo')
    data = dict(schema_version=1, data_kind='synthetic', snapshot_date='2026-03-02', max_age_days=30,
                sources=[dict(id='SRC-001', observed_date='2026-03-01', access='provided')],
                baseline='ITEM-A', entities=[dict(id='ITEM-A', variant='VAR-A', comparison_group='GROUP-A', pack_count=1), dict(id='ITEM-B', variant='VAR-A', comparison_group='GROUP-A', pack_count=2)])
    if kind == 'normalized':
        data['observations'] = [observation('001', 'ITEM-A', 'ATTR-001', 10), observation('002', 'ITEM-B', 'ATTR-001', 20, 'per_pack'), observation('003', 'ITEM-A', 'ATTR-002', 3), observation('004', 'ITEM-B', 'ATTR-002', 4)]
    elif kind == 'scope-mismatch':
        data['observations'] = []
        for j, attr in enumerate(['ATTR-001', 'ATTR-002', 'ATTR-003']):
            a = observation(str(j * 2 + 1).zfill(3), 'ITEM-A', attr, 10)
            b = observation(str(j * 2 + 2).zfill(3), 'ITEM-B', attr, 20)
            if j == 0: b['window_start'] = '2026-02-02'
            elif j == 1: b.update(kind='estimated', method='METHOD-B')
            else: b['coverage'] = 'COVER-B'
            data['observations'].extend([a, b])
    else:
        data['entities'][1]['pack_count'] = None
        data['observations'] = [observation('001', 'ITEM-A', 'ATTR-001', 10, aggregation='non_additive'), observation('002', 'ITEM-B', 'ATTR-001', 20, 'per_pack', 'non_additive'), observation('003', 'ITEM-A', 'ATTR-002', None), observation('004', 'ITEM-B', 'ATTR-002', 0), observation('005', 'ITEM-A', 'ATTR-003', 1), observation('006', 'ITEM-B', 'ATTR-003', 3, 'per_pack'), observation('007', 'ITEM-A', 'ATTR-004', 1), observation('008', 'ITEM-B', 'ATTR-004', 2), observation('009', 'ITEM-B', 'ATTR-004', 3)]
    return copy.deepcopy(data)


if __name__ == '__main__':
    paths = [Path(__file__).resolve().parents[1] / 'assets' / (k + '.json') for k in KINDS]
    if any(p.exists() for p in paths):
        raise SystemExit('Refusing to overwrite existing fixtures.')
    for kind, path in zip(KINDS, paths):
        path.write_text(json.dumps(demo(kind), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
