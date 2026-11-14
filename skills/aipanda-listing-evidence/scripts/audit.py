#!/usr/bin/env python3
"""Original MIT atomic assertion consistency checker; not a semantic verifier."""
from evidence_core import fields, header, unique_rows, token, value, quality, require, cli

BINDING = ('unit', 'variant', 'batch', 'component', 'attribute', 'condition')


def binding(row):
    for key, prefix in [('unit', 'UNIT'), ('variant', 'VAR'), ('batch', 'BATCH'),
                        ('component', 'PART'), ('attribute', 'ATTR'), ('condition', 'COND')]:
        token(row[key], prefix)
    return tuple(row[key] for key in BINDING)


def analyze(data):
    snapshot, age, sources = header(data, 'schema_version data_kind snapshot_date max_age_days sources facts claims')
    unique_rows(data['facts'], 'EV', minimum=0)
    unique_rows(data['claims'], 'CLAIM')
    facts = {}
    for row in data['facts']:
        fields(row, 'id source_id unit variant batch component attribute condition value measure_unit')
        binding(row)
        require(row['source_id'] in sources, 'unknown_source')
        facts[row['id']] = dict(row, value=value(row['value'], row['measure_unit']))
    rows = []
    for claim in data['claims']:
        fields(claim, 'id unit variant batch component attribute condition value measure_unit evidence_ids')
        key = binding(claim)
        target = value(claim['value'], claim['measure_unit'], nullable=False)
        refs = claim['evidence_ids']
        require(isinstance(refs, list) and len(refs) <= 200 and all(isinstance(x, str) and x in facts for x in refs), 'unknown_evidence')
        require(len(refs) == len(set(refs)), 'duplicate_citation')
        # Consider every matching fact, including uncited contradictions.
        matching = [f for f in facts.values() if binding(f) == key]
        wrong = [r for r in refs if binding(facts[r]) != key]
        usable = []
        unresolved = []
        details = []
        for f in matching:
            reasons = quality(sources[f['source_id']], snapshot, age)
            if f['measure_unit'] != claim['measure_unit']:
                reasons.append('measure_unit_mismatch')
            if f['value'] is None:
                reasons.append('unknown_value')
            details.append({'evidence_id': f['id'], 'cited': f['id'] in refs, 'reasons': reasons})
            if reasons:
                unresolved.extend(reasons)
            else:
                usable.append(f)
        values = {f['value'] for f in usable}
        reasons = []
        if wrong:
            reasons.append('citation_binding_mismatch')
        if len(values) > 1:
            status = 'CONFLICT'
            reasons.append('matching_sources_disagree')
        elif values and target not in values:
            status = 'CONTRADICTED'
            reasons.append('claim_differs_from_input_evidence')
        elif not matching and not wrong:
            status = 'MISSING_EVIDENCE'
            reasons.append('no_matching_fact')
        elif not refs:
            status = 'MISSING_CITATION'
            reasons.append('no_citation')
        elif wrong:
            status = 'NOT_APPLICABLE'
        elif not matching:
            status = 'MISSING_EVIDENCE'
        elif unresolved:
            status = 'REVIEW_REQUIRED'
            reasons.extend(sorted(set(unresolved)))
        elif any(f['id'] in refs for f in usable):
            status = 'SUPPORTED_BY_INPUT'
        else:
            status = 'REVIEW_REQUIRED'
            reasons.append('no_usable_cited_evidence')
        rows.append({'claim_id': claim['id'], 'binding': dict(zip(BINDING, key)),
                     'claim_value': target, 'measure_unit': claim['measure_unit'],
                     'status': status, 'reasons': reasons, 'cited_evidence_ids': refs,
                     'matching_evidence': details, 'wrong_binding_citations': wrong,
                     'draft_value': target if status == 'SUPPORTED_BY_INPUT' else None,
                     'copy_semantics_verified': False, 'executable': False})
    return {'schema_version': 1, 'skill_version': '1.0.0', 'data_kind': data['data_kind'],
            'snapshot_date': data['snapshot_date'], 'max_age_days': age, 'claims': rows,
            'sources': data['sources'], 'facts': list(facts.values()),
            'source_authenticity_verified': False, 'binding_independently_verified': False,
            'scope': 'Only supplied facts; omitted evidence and natural-language semantics are not verified.',
            'executable': False}


if __name__ == '__main__':
    cli(analyze, 'Listing 声明与证据，逐项核对。', 'claims',
        [('claim_id', '声明'), ('claim_value', '声明值'), ('status', '输入证据状态'),
         ('reasons', '理由'), ('cited_evidence_ids', '引用')])
