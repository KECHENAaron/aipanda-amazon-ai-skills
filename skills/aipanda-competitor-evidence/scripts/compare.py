#!/usr/bin/env python3
"""Original MIT comparability matrix. Exact fractions; no market winner or score."""
from fractions import Fraction
from evidence_core import fields, header, unique_rows, token, value, quality, require, day, integer, cli


def analyze(data):
    snapshot, age, sources = header(data, 'schema_version data_kind snapshot_date max_age_days sources baseline entities observations')
    unique_rows(data['entities'], 'ITEM', 20)
    entities = {}
    for e in data['entities']:
        fields(e, 'id variant comparison_group pack_count')
        token(e['variant'], 'VAR'); token(e['comparison_group'], 'GROUP')
        if e['pack_count'] is not None:
            integer(e['pack_count'], 1, 10000)
        entities[e['id']] = e
    require(data['baseline'] in entities and len(entities) >= 2, 'invalid_baseline_or_pool')
    unique_rows(data['observations'], 'OBS')
    observations = []
    for o in data['observations']:
        fields(o, 'id source_id entity_id variant attribute value measure_unit kind method coverage window_start window_end basis aggregation')
        require(o['entity_id'] in entities and o['source_id'] in sources, 'unknown_entity_or_source')
        require(o['variant'] == entities[o['entity_id']]['variant'], 'variant_binding_mismatch')
        token(o['attribute'], 'ATTR'); token(o['method'], 'METHOD'); token(o['coverage'], 'COVER')
        require(o['kind'] in {'observed', 'estimated'}, 'invalid_observation_kind')
        require(o['basis'] in {'per_item', 'per_pack'} and o['aggregation'] in {'additive', 'non_additive'}, 'invalid_basis')
        start, end = day(o['window_start']), day(o['window_end'])
        require(start <= end <= day(sources[o['source_id']]['observed_date']), 'invalid_window')
        observations.append(dict(o, value=value(o['value'], o['measure_unit'])))
    attributes = sorted({o['attribute'] for o in observations})
    baseline = entities[data['baseline']]
    comparisons = []
    for peer in entities.values():
        if peer['id'] == baseline['id']:
            continue
        for attr in attributes:
            left = [o for o in observations if o['entity_id'] == baseline['id'] and o['attribute'] == attr]
            right = [o for o in observations if o['entity_id'] == peer['id'] and o['attribute'] == attr]
            reasons = []
            if baseline['comparison_group'] != peer['comparison_group']:
                reasons.append('comparison_group_mismatch')
            if not left or not right:
                reasons.append('missing_observation')
            elif len(left) != 1 or len(right) != 1:
                reasons.append('multiple_observations_no_selection')
            normalized = []
            comparable = None
            delta = relative = None
            if len(left) == len(right) == 1:
                a, b = left[0], right[0]
                for key in ['measure_unit', 'kind', 'method', 'coverage', 'window_start', 'window_end', 'aggregation']:
                    if a[key] != b[key]:
                        reasons.append(key + '_mismatch')
                for o, entity in [(a, baseline), (b, peer)]:
                    reasons.extend(quality(sources[o['source_id']], snapshot, age))
                    if o['value'] is None:
                        reasons.append('unknown_value')
                        normalized.append(None)
                    elif o['measure_unit'] in {'bool', 'token'}:
                        if o['basis'] != 'per_item':
                            reasons.append('non_numeric_pack_normalization')
                        normalized.append(o['value'])
                    else:
                        n = Fraction(o['value'])
                        if o['basis'] == 'per_pack':
                            if o['aggregation'] != 'additive':
                                reasons.append('non_additive_pack_value')
                            if entity['pack_count'] is None:
                                reasons.append('unknown_pack_count')
                            else:
                                n /= entity['pack_count']
                        normalized.append(n)
                if not reasons:
                    comparable = normalized[0] == normalized[1]
                    if a['measure_unit'] not in {'bool', 'token'}:
                        delta = str(normalized[1] - normalized[0])
                        if normalized[0] != 0:
                            relative = str((normalized[1] - normalized[0]) / normalized[0])
            comparisons.append({'baseline': baseline['id'], 'peer': peer['id'], 'attribute': attr,
                                'status': 'COMPARABLE_BY_INPUT' if not reasons else 'NOT_COMPARABLE',
                                'reasons': sorted(set(reasons)),
                                'baseline_observation_ids': [o['id'] for o in left],
                                'peer_observation_ids': [o['id'] for o in right],
                                'normalized_per_item_values': [str(v) if isinstance(v, Fraction) else v for v in normalized] if not reasons else None,
                                'equal_by_input': comparable, 'delta_exact': delta,
                                'relative_change_exact': relative,
                                'relative_unavailable_reason': 'zero_baseline' if not reasons and len(normalized) == 2 and isinstance(normalized[0], Fraction) and normalized[0] == 0 else None,
                                'executable': False})
    return {'schema_version': 1, 'skill_version': '1.0.0', 'data_kind': data['data_kind'],
            'snapshot_date': data['snapshot_date'], 'max_age_days': age, 'baseline': baseline['id'],
            'entities': data['entities'], 'sources': data['sources'], 'observations': observations,
            'comparisons': comparisons, 'source_authenticity_verified': False,
            'comparison_group_independently_verified': False,
            'scope': 'Declared pool and attributes only; no market coverage, causal effect, winner or profit conclusion.',
            'executable': False}


if __name__ == '__main__':
    cli(analyze, '竞品对标，先核对可比条件。', 'comparisons',
        [('peer', '比较对象'), ('attribute', '维度'), ('status', '可比性'),
         ('reasons', '阻断理由'), ('normalized_per_item_values', '每件值 / 均值'), ('delta_exact', '差值（精确分数）')])
