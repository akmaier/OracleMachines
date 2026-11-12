#!/usr/bin/env python3
"""Distinguish coupled-route novelty from the already retained first route."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_coupled_pivots import restore_seed,apply_coupled_delta,digests
from experiments.compare_cnf_frontier_pivots import unpack
from experiments.compare_cnf_retained_plans import sha
from experiments.cnf_coupled_pivots import FrontierIndex,coupled_key
from experiments.cnf_pattern_inventory import encode


def main(directory):
    output=directory/'continuation-analysis.json'
    if output.exists():raise FileExistsError(output)
    report_path=directory/'report.json';r=json.loads(report_path.read_text());started=time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);history=tmp/'history';restore_seed(r['suite'],history,tmp)
        assert digests(history)==r['seed_table_digests']
        old=sqlite3.connect(':memory:');old.execute('CREATE TABLE keys (id TEXT PRIMARY KEY)')
        db=sqlite3.connect(history)
        old.executemany('INSERT INTO keys VALUES (?)',db.execute('SELECT id FROM cnf_patterns_v1'));old.commit();db.close()
        delta=tmp/'delta';d=r['delta'];assert sha(d['path'])==d['sha256']
        unpack(d['path'],delta,d['database_sha256']);apply_coupled_delta(history,delta)
        assert digests(history)==r['logical_table_digests'];db=sqlite3.connect(history);cache={}
        class Reader:
            def _load(self,key):
                if key not in cache:
                    row=db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(key,)).fetchone()
                    if row is None:raise ValueError('Missing archived node')
                    cache[key]=json.loads(row[0])
                return cache[key]
        index=FrontierIndex(Reader());counts=Counter();rows=[];new_leaves=set()
        for key,payload in db.execute('SELECT id,payload FROM cnf_coupled_trials_v1'):
            record=json.loads(payload);assert key==coupled_key(record)
            first=json.loads(db.execute('SELECT payload FROM cnf_pivot_trials_v1 WHERE id=?',
                (encode([record['source'],record['variables'][0]]),)).fetchone()[0])
            a=index.frontier(first['edge']['key']);b=index.frontier(record['edge']['key'])
            novel={k for k in b if old.execute('SELECT 1 FROM keys WHERE id=?',(k,)).fetchone() is None};new_leaves.update(novel)
            before=index.literals(a);after=index.literals(b)
            counts['trials']+=1;counts['same_frontier_as_retained_first_route']+=a==b
            counts['changed_frontier_from_retained_first_route']+=a!=b
            counts['fewer_open_literals_than_first_route']+=after<before
            counts['more_open_literals_than_first_route']+=after>before
            counts['only_seed_leaves']+=not novel
            counts['immediate_target_already_in_seed']+=old.execute('SELECT 1 FROM keys WHERE id=?',(record['edge']['key'],)).fetchone() is not None
            rows.append(dict(trial_sha256=hashlib.sha256(key.encode()).hexdigest(),same_first_route_frontier=a==b,
                first_route_open_literals=before,coupled_open_literals=after,novel_seed_leaf_count=len(novel)))
        dd=sqlite3.connect(delta);kinds=Counter(json.loads(p)['kind'] for p, in dd.execute('SELECT payload FROM cnf_patterns_v1'));dd.close();old.close();db.close()
    result=dict(script_sha256=sha(Path(__file__)),report_sha256=sha(report_path),seconds=time.perf_counter()-started,
        counts=dict(counts),new_node_kinds=dict(kinds),distinct_leaves_absent_from_seed=len(new_leaves),rows=rows,
        limitations=['Post-run read-only analysis of archive-bound, previously cold-checked histories; no fresh timing or semantic-equivalence claim.',
            'Equal selected canonical leaf multisets retain multiplicity; distinct path bindings are still checked separately.',
            'A leaf novel relative to the original-source frontier can already exist in the paid seed. This analysis tests that exact distinction.'])
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('rows','limitations')}))


if __name__=='__main__':main(Path(sys.argv[1]))
