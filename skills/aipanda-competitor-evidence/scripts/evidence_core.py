"""Original shared mechanics, copied into each standalone MIT skill. No network."""
import argparse
from datetime import date
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import re

UNITS = {'cm', 'mm', 'g', 'kg', 'L', 'mL', 'count', 'bool', 'token'}


def require(ok, code):
    if not ok:
        raise ValueError(code)


def fields(obj, keys):
    require(isinstance(obj, dict) and set(obj) == set(keys.split()), 'invalid_fields')


def token(value, prefix):
    require(isinstance(value, str) and re.fullmatch(re.escape(prefix) + r'-[A-Z0-9]{1,12}', value) is not None, 'invalid_token')
    return value


def day(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) is not None, 'invalid_date')
    return date.fromisoformat(value)


def integer(value, low, high):
    require(type(value) is int and low <= value <= high, 'invalid_integer')
    return value


def value(obj, unit, nullable=True):
    require(isinstance(unit, str) and unit in UNITS, 'unsupported_measure_unit')
    if obj is None:
        require(nullable, 'claim_value_required')
        return None
    if unit == 'bool':
        require(type(obj) is bool, 'invalid_boolean')
        return obj
    if unit == 'token':
        return token(obj, 'TOKEN')
    require(type(obj) in {int, float, Decimal}, 'invalid_number')
    n = Decimal(str(obj))
    require(n.is_finite() and 0 <= n <= Decimal('1000000000000'), 'invalid_number')
    require(n == n.quantize(Decimal('0.000001')), 'excess_input_precision')
    if unit == 'count':
        require(n == n.to_integral_value(), 'fractional_count')
    return n


def unique_rows(rows, prefix, maximum=200, minimum=1):
    require(isinstance(rows, list) and minimum <= len(rows) <= maximum, 'invalid_rows')
    ids = set()
    for row in rows:
        require(isinstance(row, dict) and 'id' in row, 'row_id_required')
        token(row['id'], prefix)
        require(row['id'] not in ids, 'duplicate_id')
        ids.add(row['id'])


def header(data, keys):
    fields(data, keys)
    require(type(data['schema_version']) is int and data['schema_version'] == 1, 'unsupported_schema')
    require(data['data_kind'] in {'synthetic', 'anonymized_local'}, 'invalid_data_kind')
    snapshot = day(data['snapshot_date'])
    age = integer(data['max_age_days'], 0, 3650)
    unique_rows(data['sources'], 'SRC', 64, minimum=0)
    sources = {}
    for s in data['sources']:
        fields(s, 'id observed_date access')
        require(s['access'] in {'provided', 'unavailable'}, 'invalid_access')
        observed = day(s['observed_date'])
        require(observed <= snapshot, 'future_source')
        sources[s['id']] = s
    return snapshot, age, sources


def quality(source, snapshot, max_age):
    reasons = []
    if source['access'] != 'provided':
        reasons.append('source_unavailable')
    if (snapshot - day(source['observed_date'])).days > max_age:
        reasons.append('source_stale')
    return reasons


def serial(obj):
    if isinstance(obj, Decimal):
        return format(obj, 'f')
    if isinstance(obj, dict):
        return {k: serial(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serial(v) for v in obj]
    return obj


def no_duplicate_keys(pairs):
    result = {}
    for key, val in pairs:
        require(key not in result, 'duplicate_json_key')
        result[key] = val
    return result


def load(path):
    data = Path(path).read_bytes()
    require(len(data) <= 2_000_000, 'input_too_large')
    def bad_constant(_):
        raise ValueError('nonfinite_json_number')
    return json.loads(data.decode('utf-8'), parse_float=Decimal,
                      parse_constant=bad_constant, object_pairs_hook=no_duplicate_keys)


def html_report(result, title, row_key, columns):
    safe = serial(result)
    label = '声明合成练习 · 发布前仍须核对生成器' if safe['data_kind'] == 'synthetic' else '本地匿名输入 · 不供公开'
    head = ''.join('<th>' + escape(label) + '</th>' for _, label in columns)
    rows = []
    for row in safe[row_key]:
        cells = []
        for key, _ in columns:
            item = row.get(key)
            text = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (list, dict)) else str(item)
            cells.append('<td>' + escape(text) + '</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    return '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>''' + escape(title) + '''</title><style>*{box-sizing:border-box}body{margin:0;background:#fbfbfd;color:#17233b;font:16px/1.8 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px 22px}h1{font-size:34px;line-height:1.3}.note{padding:18px;background:#f0edf8;border-left:4px solid #a695df}.scroll{overflow:auto}table{width:100%;min-width:760px;border-collapse:collapse}td,th{text-align:left;padding:13px;border-bottom:1px solid #dfe4ee;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef0f6;padding:18px}a{color:#6950c7}details{margin-top:24px}summary{cursor:pointer}</style><main><p>🐼 AIPANDA · MIT · ''' + escape(label) + '''</p><h1>''' + escape(title) + '''</h1><p class="note">只验证结构化输入间的一致性和可比性。来源、对象绑定和语义未独立核实，不代表事实真实、文案可直接提交或市场机会已经成立。全部结果 executable=false。</p><div class="scroll"><table><thead><tr>''' + head + '</tr></thead><tbody>' + ''.join(rows) + '''</tbody></table></div><details><summary>完整证据与审计 JSON</summary><pre>''' + escape(json.dumps(safe, ensure_ascii=False, indent=2, allow_nan=False)) + '''</pre></details><p>不接卖家账户，不上传资料，不做利润核对。真实输入与本地匿名报告不要公开。</p></main></html>'''


def cli(analyze, title, row_key, columns):
    parser = argparse.ArgumentParser(description=title + ' — offline structured evidence checks')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    try:
        result = serial(analyze(load(args.input)))
        output_json = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        output_html = html_report(result, title, row_key, columns)
        out = Path(args.output_dir)
        require(not out.exists() and not out.is_symlink(), 'output_exists')
        out.mkdir(parents=True, exist_ok=False)
        (out / 'report.json').write_text(output_json, encoding='utf-8')
        (out / 'report.html').write_text(output_html, encoding='utf-8')
        print('Offline report ready: ' + str(out / 'report.html'))
    except (ValueError, TypeError, KeyError, OSError, ArithmeticError):
        parser.exit(2, 'Input or output rejected; check the schema and use a new directory. Input values are not echoed.\n')
