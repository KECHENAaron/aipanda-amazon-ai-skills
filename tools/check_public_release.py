#!/usr/bin/env python3
"""Pre-publication pattern checks. Reports locations and rule IDs, never matched values. MIT."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ASINS={'B0DEMO0001','B0DEMO0002','B0PUBLIC01','B0XXXXXXXX'}
RULES={
 'absolute_private_path':re.compile('/'+r'(?:Users|Volumes|home|root)/'),
 'credential_pattern':re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16})\b'),
 'private_network':re.compile(r'https?://(?:localhost|127\.0\.0\.1|192\.168\.|10\.\d+\.)'),
 'private_key':re.compile('-----BEGIN '+r'(?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}
FORBIDDEN_SUFFIX={'.db','.sqlite','.sqlite3','.jsonl','.pem','.p12','.har'}


def scan_text(text):
 issues=[name for name,rx in RULES.items() if rx.search(text)]
 if set(re.findall(r'\bB0[A-Z0-9]{8}\b',text))-ASINS:issues.append('unreviewed_product_identifier')
 return issues


def check(root=ROOT,history=False):
 raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode()
 names=sorted(set(p for p in raw.split('\0') if p));findings=[];binary=0
 for name in names:
  p=root/name
  findings.extend({"path":name,"rule":rule} for rule in scan_text(name))
  if not p.is_file():continue
  if p.name.startswith('.env') or p.suffix.lower() in FORBIDDEN_SUFFIX:findings.append({'path':name,'rule':'forbidden_artifact'})
  b=p.read_bytes()
  try:t=b.decode()
  except UnicodeDecodeError:
   binary+=1
   if name not in {'assets/avatar.jpg','docs/assets/avatar.jpg'}:findings.append({'path':name,'rule':'unreviewed_binary'})
   continue
  findings.extend({'path':name,'rule':rule} for rule in scan_text(t))
 # Public new demonstrations must reproduce exact generator inputs, not merely claim synthetic.
 demo_path=root/'skills/aipanda-ads-period-review/scripts/make_demo.py'
 if demo_path.exists():
  import importlib.util
  spec=importlib.util.spec_from_file_location('public_demo_generator',demo_path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  for kind in ['unequal-days','immature','mix-shift']:
   if json.loads((demo_path.parents[1]/'assets'/f'{kind}.json').read_text()) != m.demo(kind):findings.append({'path':kind,'rule':'synthetic_fixture_mismatch'})
 historic=0;commits=0
 if history:
  objects=subprocess.check_output(['git','rev-list','--all','--objects'],cwd=root,text=True).splitlines()
  for entry in objects:
   sha,_,name=entry.partition(' ')
   kind=subprocess.check_output(['git','cat-file','-t',sha],cwd=root,text=True).strip()
   if kind not in ('blob','commit','tag'):continue
   findings.extend({"object":sha,"rule":rule} for rule in scan_text(name))
   b=subprocess.check_output(['git','cat-file',kind,sha],cwd=root)
   try:t=b.decode()
   except UnicodeDecodeError:continue
   if kind=='blob':historic+=1
   if kind=='commit':commits+=1
   findings.extend({'object':sha,'rule':rule} for rule in scan_text(t))
 return {'status':'PASS' if not findings else 'FAIL','current_files_checked':len(names),'approved_binary_paths':binary,'historical_text_blobs_checked':historic,'commit_messages_checked':commits,'findings':findings,'limit':'Pattern and fixture checks assist human review; they cannot certify every possible disclosure.'}


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--history',action='store_true');a=p.parse_args()
 r=check(history=a.history);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(bool(r['findings']))
