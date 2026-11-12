#!/usr/bin/env python3
"""Explain reconvergence of bounded pivot trials using their preserved exact graphs."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pivot_alternatives import selected_pivot
from experiments.compare_cnf_pivot_alternatives import apply_delta,TABLES
from experiments.compare_cnf_retained_plans import sha
from experiments.compare_cnf_clause_mask import table_digest


def main(directory):
    started=time.perf_counter();report_path=directory/'report.json';report=json.loads(report_path.read_text())
    output=directory/'frontier-analysis.json'
    if output.exists():raise FileExistsError(output)
    counts=Counter();rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);base=tmp/'base';history=tmp/'history';delta=tmp/'delta'
        assert sha(report['base_archive'])==report['base_archive_sha256']
        with gzip.open(report['base_archive'],'rb') as src,base.open('wb') as dst:shutil.copyfileobj(src,dst)
        assert sha(base)==report['base_database_sha256'];shutil.copyfile(base,history)
        assert sha(report['delta']['path'])==report['delta']['sha256']
        with gzip.open(report['delta']['path'],'rb') as src,delta.open('wb') as dst:shutil.copyfileobj(src,dst)
        assert sha(delta)==report['delta']['database_sha256'];apply_delta(history,delta)
        db=sqlite3.connect(history);old=sqlite3.connect(base)
        for table in TABLES:assert table_digest(db,table)==report['logical_table_digests'][table]
        cache={};frontiers={}
        def node(key):
            if key not in cache:
                row=db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(key,)).fetchone()
                if row is None:raise ValueError('Missing preserved plan')
                cache[key]=json.loads(row[0])
            return cache[key]
        def frontier(key):
            if key in frontiers:return frontiers[key]
            n=node(key);result=Counter()
            if n['summary']['closed']:pass
            elif n['kind']=='unresolved':result[key]=1
            elif n['kind']=='and':
                for e in n['edges']:result.update(frontier(e['key']))
            elif n['kind']=='or':
                for e in n['alternatives'][n['selected']]['edges']:result.update(frontier(e['key']))
            elif 'edge' in n:result.update(frontier(n['edge']['key']))
            else:raise ValueError('Unknown open node kind')
            frontiers[key]=result;return result
        h=AnchoredAdditiveInventory(history,**report['options']);global_old=Counter()
        for case in report['cases']:
            _,_,key=h._canonical(case['source'],h.config['max_depth']);global_old.update(frontier(key))
        h.close();target_roots=Counter();all_new=set();improvements=[]
        for key,payload in db.execute('SELECT id,payload FROM cnf_pivot_trials_v1 ORDER BY rowid'):
            r=json.loads(payload);source=r['source'];target=r['edge']['key'];a,b=frontier(source),frontier(target)
            target_roots[target]+=1; novel=set(b)-set(global_old);all_new.update(novel)
            before=sum(node(k)['profile']['shape']['literals']*n for k,n in a.items())
            after=sum(node(k)['profile']['shape']['literals']*n for k,n in b.items())
            exists=old.execute('SELECT 1 FROM cnf_patterns_v1 WHERE id=?',(target,)).fetchone() is not None
            same=a==b;known=not novel
            pivot=selected_pivot(node(source))
            joint=sum(pivot in set(map(abs,c)) and r['variable'] in set(map(abs,c)) for c in node(source)['cnf'])
            counts['unique_trials']+=1;counts['direct_targets_already_in_base']+=exists
            counts['noninteracting_pivot_pairs']+=joint==0
            counts['noninteracting_same_frontier']+=joint==0 and same
            counts['same_selected_frontier_as_source']+=same;counts['target_frontier_only_old_leaves']+=known
            counts['target_frontier_has_novel_leaves']+=bool(novel)
            counts['fewer_selected_open_literals']+=after<before;counts['more_selected_open_literals']+=after>before
            counts['closed_targets']+=r['summary']['closed']
            row=dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),variable=r['variable'],
                target_sha256=hashlib.sha256(target.encode()).hexdigest(),target_already_in_base=exists,
                selected_pivot=pivot,joint_pivot_clauses=joint,
                same_selected_frontier=same,only_old_leaves=known,novel_leaf_count=len(novel),
                source_open_literals=before,target_open_literals=after,
                target_frontier=[dict(key_sha256=hashlib.sha256(k.encode()).hexdigest(),multiplicity=n) for k,n in sorted(b.items())])
            rows.append(row)
            if after<before:improvements.append(row)
        counts['distinct_target_roots']=len(target_roots);counts['duplicate_target_references']=sum(target_roots.values())-len(target_roots)
        kinds=Counter(json.loads(p)['kind'] for p, in sqlite3.connect(delta).execute('SELECT payload FROM cnf_patterns_v1'))
        db.close();old.close()
    result=dict(script_sha256=sha(Path(__file__)),report_sha256=sha(report_path),seconds=time.perf_counter()-started,
        statistics=dict(counts),old_distinct_selected_leaves=len(global_old),novel_distinct_selected_leaves=len(all_new),
        new_node_kinds=dict(kinds),trials=rows,limitations=[
        'Read-only analysis after timed runs; canonical frontier multisets retain multiplicity, but different paths still have their own checked variable maps.',
        'Equal selected frontiers show exact represented reconvergence, not semantic equivalence of all possible orders or exclusion of SAT classes.',
        'The old-leaf reference is the selected original-source frontier; existing base nodes can also contain other unselected leaves.',
        'Direct base-target reuse is a lower bound on recognition work reused: descendants and new within-run hits also reuse stored nodes.'])
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('trials','limitations')}))


if __name__=='__main__':main(Path(sys.argv[1]))
