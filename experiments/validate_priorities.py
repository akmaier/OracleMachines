#!/usr/bin/env python3
"""Validate priority-study records and preserve raw preallocation telemetry.

The recorded harness kept the preceding query's ledger when a new input was
rejected before solve(). Redact only that inapplicable field in a derived log;
retain the original bytes, outcomes and elapsed times. Future workers clear the
ledger at the request boundary and do not need this correction.
"""
import argparse,gzip,hashlib,json,shutil,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory
 metadata=json.loads((d/'metadata.json').read_text());source=d/'runs.jsonl.gz';raw=d/'runs-original.jsonl.gz'
 if not raw.exists():shutil.copyfile(source,raw)
 rows=[json.loads(line) for line in gzip.open(raw,'rt')];corrected=0;rss_missing=0
 for r in rows:
  if r['samples']==0 and r['sampling_misses']>0:
   r['sampled_peak_rss_bytes']=None;r['rss_observation_available']=False;rss_missing+=1
  for q in r['records']:
   if q.get('error','').endswith('Encoded source exceeds input cap before allocation'):
    if q.get('failure_metrics'):
     q['failure_metrics']={};q['omitted_previous_request_ledger']=True;corrected+=1
 with gzip.open(source,'wt') as f:
  for r in rows:f.write(json.dumps(r)+'\n')
 planned=sum(r['planned'] for r in rows);qs=[q for r in rows for q in r['records'] if q['event']=='query']
 for r in rows:
  assert [q['stage'] for q in r['records'] if q['event']=='query']==list(range(r['planned']))
  assert r['exit']==0 and r['stop'] is None
 for q in qs:
  if q['status']=='ok':
   assert q['result']['answer']==q['expected']
   if 'phase_ns' in q['result']:assert sum(q['result']['phase_ns'].values())==q['result']['wall_ns']
 assert not any(q['status']=='wrong' for q in qs)
 current=[];historical=[]
 for name,expected in metadata['fingerprints'].items():
  path=ROOT/name
  if sha(path)==expected:current.append(name);continue
  # Only the harness and its regression changed after recording: clear stale
  # telemetry before input conversion. Recorded versions remain reconstructible.
  assert name in ['experiments/run_priorities.py','solver/test_priorities.py'],name
  data=subprocess.check_output(['git','show',metadata['source_commit']+':'+name],cwd=ROOT)
  assert hashlib.sha256(data).hexdigest()==expected,name
  historical.append(name)
 diagnostics=json.load(gzip.open(d/'diagnostics.json.gz','rt'))
 for r in diagnostics:
  if r['kind']=='distinct_layers':
   assert r['initial']['layered']['native_definitions']==2*r['size']-1
   assert r['edit']['layered']['native_definitions']==r['size'].bit_length()
   assert r['repeat_query']['layered']['native_definitions']==0
  elif r['kind']=='semantic_provenance':
   m=r['equal_edit']['interfaces'];assert m['semantic_stops']==1 and m['provenance_rebinds']==r['size']
   assert m['combination_rows']==2 and m['affected_buckets']==r['size']+1
   assert not r['negative']['answer'] and r['deletion']['answer']
 report=dict(runs=len(rows),planned=planned,observed=len(qs),outcomes=dict(Counter(q['status'] for q in qs)),
  completed_unsat=sum(q['status']=='ok' and not q['result']['answer'] for q in qs),
  errors=dict(Counter(q['error'] for q in qs if q['status']=='error')),
  current_fingerprints_verified=len(current),historical_fingerprints_verified=historical,
  raw_sha256=sha(raw),derived_sha256=sha(source),preallocation_ledgers_redacted=corrected,
  diagnostic_records=len(diagnostics),diagnostic_assertions_passed=True,
  rss_unavailable_runs=rss_missing,rss_valid_samples=sum(r['samples'] for r in rows),
  rss_sampling_misses=sum(r['sampling_misses'] for r in rows),
  max_sample_interval_ms=max(r['max_sample_interval_ms'] for r in rows),
  peak_sampled_scratch_bytes=max(r['sampled_peak_scratch_bytes'] for r in rows))
 summary=d/'summary.json';original_summary=d/'summary-original.json'
 if not original_summary.exists():shutil.copyfile(summary,original_summary)
 table=json.loads(original_summary.read_text())
 for row in table:
  values=[r['sampled_peak_rss_bytes'] for r in rows if r['mode']==row['mode'] and r['stream']==row['stream'] and r['sampled_peak_rss_bytes'] is not None]
  row['peak_sampled_rss']=max(values) if values else None
 summary.write_text(json.dumps(table,indent=2)+'\n')
 (d/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
