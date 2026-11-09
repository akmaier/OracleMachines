#!/usr/bin/env python3
"""Replay the complete old signed archive with an identical indexed policy."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_implied_subsumption import ImpliedSubsumptionInventory


def main(directory):
    target=directory/'index-control.json'
    if target.exists():raise FileExistsError(target)
    previous=Path('experiments/results/cnf-signed-subsumption')
    report_path=previous/'report.json';report=json.loads(report_path.read_text())
    entry=next(a for a in report['archives'] if a['mode']=='subsumption')
    pairs=json.loads((previous/'pair-costs.json').read_text())
    raw=gzip.decompress((previous/entry['path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==entry['database_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'archive.db';path.write_bytes(raw)
        started=time.perf_counter()
        h=ImpliedSubsumptionInventory(path,max_depth=2,probe_limit=4,learn_limit=4,reuse_implications=False)
        nodes=0
        for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
            h._load(key);nodes+=1
        node_seconds=time.perf_counter()-started;counts=dict(h.counts);sources=0
        for key,payload in h.db.execute('SELECT id,payload FROM cnf_pattern_sources_v1'):
            saved=json.loads(payload);result=h.inspect(saved['source'])
            assert result['source_id']==key and result['root']==saved['root']
            assert result['metrics'].get('inserted_nodes',0)==0 and result['metrics']['inserted_sources']==0
            sources+=1
        h.close();assert path.read_bytes()==raw
    assert counts['subsumption_check_subset_tests']==pairs['counts']['strictly_shorter_tests']
    assert counts['subsumption_check_calls']==3753
    result=dict(prior_report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        prior_pair_costs_sha256=hashlib.sha256((previous/'pair-costs.json').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        implementation_sha256=hashlib.sha256(Path('experiments/cnf_implied_subsumption.py').read_bytes()).hexdigest(),
        database_sha256=entry['database_sha256'],nodes=nodes,sources=sources,node_check_seconds=node_seconds,
        counts=counts,bytes_unchanged=True,
        limitations=['Complete old pattern graph, alternatives and source bindings checked; ordinary solver certificates are covered by separate archive audits',
          'Indexed mode uses the same policy identity and exact old certificates, not a rekeyed copy',
          'Cold check seconds are one standalone sample and exclude file preparation and source binding replay',
          'Noncanonical repeated-literal helpers retain the old fallback; the inventory uses canonical distinct clauses',
          'This control establishes removed comparisons and archive compatibility, not a general runtime speedup'])
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
