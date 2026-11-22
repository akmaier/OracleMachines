#!/usr/bin/env python3
"""Freeze the six-clause boundary and native-probe overhead ablations."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import random,sqlite3,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_transported_partition as previous
from experiments.cnf_probed_partition import run as probed
from experiments.cnf_residual_dag import normalize,token
base=previous.base;binding=previous.binding;bound=previous.bound
TABLES=previous.TABLES;read_zip=previous.read_zip;write_zip=previous.write_zip;restore=previous.restore;tables=previous.tables
PARENT=Path('experiments/results/cnf-transported-partition')
CASES=(25,31,61);MODES=('affine','native','probe-native','reverse6','probe6');SPLITS=('boundary','fresh')
FILES=('experiments/cnf_probed_partition.py','experiments/compare_cnf_probed_partition.py','solver/test_cnf_probed_partition.py')


def prepare(out):
    out.mkdir(exist_ok=True);assert not (out/'protocol.json').exists();began=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');old_cases=bound(old['cases']);cases=[];prefixes={}
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={key for t in TABLES for key, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    for index in CASES:
        rpt=base.load(PARENT/f'edits-{index}-reverse-0/report.json');queries=bound(rpt['queries']);delta=read_zip(rpt['delta'])
        prefix=read_zip(old['prefixes'][str(index)]['archive'])
        addition={t:[[k,v] for k,v in delta[t] if k in set(queries[0]['new_ids'][t])] for t in TABLES}
        merged={t:prefix[t]+addition[t] for t in TABLES}
        assert all(len(dict(v))==len(v) for v in merged.values())
        seed=write_zip(out/f'prefix-{index}.json.gz',merged)
        prefixes[str(index)]=dict(archive=seed,parent_prefix=old['prefixes'][str(index)]['archive'],
            addition_report=binding(PARENT/f'edits-{index}-reverse-0/report.json'),addition_ids=queries[0]['new_ids'],counts={t:len(v) for t,v in merged.items()})
        original=next(c for c in old_cases if c['case']==index and c['split']=='historical')
        boundary=deepcopy(next(c for c in old_cases if c['case']==index and c['variant']=='delete'))
        boundary.update(split='boundary',variant='delete',known_in_prior_union=boundary['root'] in known);cases.append(boundary)
        descriptor=base.load(PARENT/f'historical-{index}-reverse-0/queries.json')[0]['descriptor']
        common=sorted(set(map(tuple,original['source']))&set(map(tuple,descriptor['source']))-{tuple(boundary['edit_clause'])})
        rng=random.Random(202611190746+index);removed=rng.sample(common,2)
        for i,clause in enumerate(removed):
            source=[c for c in original['source'] if tuple(c)!=clause]
            added=None
            if i:
                added=sorted(v*(1 if rng.randrange(2) else -1) for v in rng.sample(original['candidate']['target_names'],3))
                assert added not in source;source.append(added)
            cnf,names=normalize(source);root=token(cnf,Counter());assert root not in known
            c=deepcopy(original['candidate']);c.update(target=[list(cl) for cl in cnf],target_names=list(names))
            cases.append(dict(case=index,split='fresh',variant='delete' if i==0 else 'replace',candidate=c,
                source=previous.target_source(c),root=root,known_in_prior_union=False,deleted_clause=list(clause),added_clause=added))
        for c in cases:
            if c['case']==index:assert all(c['root'] not in dict(merged[t]) for t in TABLES)
    assert len({c['root'] for c in cases})==9;base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),cases=binding(out/'cases.json'),prefixes=prefixes,
        node_limit=256,probe_limit=8,max_missing=6,orders=[list(MODES),list(reversed(MODES))],preparation_seconds=time.perf_counter()-began,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
        'Three cold starts restore exactly the historical prefix plus the preceding reverse arm\'s first addition. Deletion answers and later work are excluded; all nine query roots are absent from their seeds.',
        'The three boundary targets were previously exposed; the six fresh roots delete a different core clause, optionally adding one fixed signed ternary clause. All six are absent from the prior cumulative union. Candidate origins/maps remain supplied.',
        'Five separate serial worker arms in two opposite orders: affine baseline; native-only baseline; eight-expansion probe then native fallback; reverse first-false with two-to-six missing clauses; probe then that partition. No outcome-based tuning.',
        'Probe plus fallback or all partition branches share one 256-expansion budget. A successful probe avoids support preparation. A stopped probe commits already-checked, dependency-closed pending proof rows; its incomplete root remains unknown.',
        'Only the initial probe preserves its final checked batch on an ordinary budget stop. Unexpected exceptions and commit failures retain the existing rollback/invalidation semantics. Later acquisition uses the original stop behavior.',
        'The probe is restarted search with retained proof reuse, not a continuation stack. Its eight-expansion bound does not bound input scanning, proof verification, database work, time or RAM. Some repeated work is possible.',
        'Support plans retain the earlier32-node/8192-literal/128KiB caps. First-false composition uses unchanged native and sidecar checkers; every UNSAT branch is required and SAT witnesses lift to the target residual, not its original source.',
        'Complete measured worker time includes prefix reconstruction, full cold proof checking, warm-bank setup, measurements, serialization and persistence. Shared prior acquisition and supplied-candidate discovery remain separately preserved sunk costs.',
        'Sidecars remain raw JSON, with their duplication charged. No automatic broad-family discovery, efficient arbitrary-SAT closure, or Lean refinement proof is claimed.']))


def query(s,c,mode,budget):
    if mode in ('affine','native'):return previous.query(s,c,mode,budget)
    return probed(s,c['candidate'],mode,budget)


def worker(out,p,split,index,mode):
    # Reuse the frozen measurement/replay harness, changing only query policy.
    baseline=previous.query
    def dispatch(s,c,m,budget):
        if m in ('affine','native'):return baseline(s,c,m,budget)
        return probed(s,c['candidate'],m,budget)
    with patch.object(previous,'query',dispatch):previous.worker(out,p,split,index,mode)


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for split in SPLITS:
        for index in CASES:
            for repeat,order in enumerate(p['orders']):
                for mode in order:
                    dest=out/f'{split}-{index}-{mode}-{repeat}'
                    subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),split,str(index),mode],check=True)
                    samples.append(dict(split=split,case=index,mode=mode,repeat=repeat,**binding(dest/'report.json')))
                print('finished',split,index,repeat,flush=True)
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples))

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4],int(sys.argv[5]),sys.argv[6])
    else:run(Path(sys.argv[1]))
