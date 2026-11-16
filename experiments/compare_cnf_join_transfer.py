#!/usr/bin/env python3
"""Matched-history test of exact saved joins on distinct, unlabelled CNFs."""
from collections import Counter
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap as base
from experiments.cnf_join_workloads import parent_case, check_image
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_query_checkpoint import check_query
from experiments.cnf_canonical_audit import audit
from experiments.cnf_coupled_pivots import AdmissionExhausted

PARENT = Path('experiments/results/cnf-progress-transfer')
CONTROL = Path('experiments/results/cnf-progress-pilot')
MODES = ('base', 'joins')


def binding(path):
    return dict(path=str(path), sha256=base.sha(path))


def pairs(h):
    return dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'))


def prepare(out, protocol):
    started = time.perf_counter(); old = base.load(protocol['control']['path'])
    current = base.load(protocol['checkpoint']['path']); catalog = base.load(protocol['join_anchors']['path'])
    proof = base.load(protocol['join_proof']['path']); keys = {s['source'] for s in proof['steps']}
    identities = {s['rule']['id'] for s in proof['steps'] if s['rule']['kind'] == base.split.KIND}
    seeds = {}; cases = []; seen = set()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); base.restore_archive(current['archive'], tmp/'current')
        h = base.CompleteAdmissionInventory(tmp/'current', **protocol['options']); h.set_admission_budget(0)
        try:
            selected = {k:h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0] for k in keys}
            selected_pairs = {k:pairs(h)[k] for k in identities}
            with base.no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('prepare acquisition')):
                for anchor_index, anchor in enumerate(sorted(catalog, key=lambda a:a['shape']['variables'])):
                    cnf = base.load_json(anchor['source'])[-1]
                    eligible = [i for i,c in enumerate(cnf) if len(c)>=2][:3]
                    assert len(eligible)==3
                    for variant, cid in enumerate(eligible):
                        for edited in (False, True):
                            case = parent_case(cnf, cid, variant, edited=edited)
                            root = h._canonical(case['source'],0)[2]
                            assert root not in seen and h._load(root) is None
                            seen.add(root)
                            image = h._canonical(case['expected_image'],0)[2]
                            check_image(h, case['source'],case['witness_variable'],image)
                            assert (image==anchor['source']) is (not edited)
                            cases.append(dict(case=len(cases),source=case['source'],root=root,
                                anchor=anchor['source'],anchor_variables=anchor['shape']['variables'],variant=variant,
                                edited=edited,witness_variable=case['witness_variable'],image=image,
                                split_clause=case['split_clause'],removed_clause=case['removed_clause']))
        finally:
            h.close(); assert base.sha(tmp/'current')==current['archive']['database_sha256']
        base.write(out/'cases.json', cases)
        for mode in MODES:
            dest=out/f'seed-{mode}';dest.mkdir();path=tmp/mode;base.restore_archive(old['archive'],path)
            h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
            try:
                initial=base.rows(h);initial_pairs=pairs(h)
                if mode=='joins':
                    with h.db:
                        for k,v in selected.items():
                            if k in initial:assert initial[k]==v
                            else:h.db.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)',(k,v))
                        for k,v in selected_pairs.items():
                            if k in initial_pairs:assert initial_pairs[k]==v
                            else:h.db.execute(f'INSERT INTO {base.split.TABLE} VALUES (?,?)',(k,v))
                assert initial.items()<=base.rows(h).items() and initial_pairs.items()<=pairs(h).items()
                for case in cases:assert h._load(case['root']) is None
                delta=dict(patterns=len(base.rows(h))-len(initial),pairs=len(pairs(h))-len(initial_pairs))
            finally:h.close()
            cold=audit(path,protocol,canonical=True);entry=base.archive(path,dest)
            seeds[mode]=dict(archive=entry,cold=cold,added=delta)
    result=dict(seeds=seeds,cases=binding(out/'cases.json'),seconds=time.perf_counter()-started,
        note='Controlled copies of the pre-case-10 history. Joins adds only the selected proof dependencies; current authority remains untouched.')
    base.write(out/'seeds.json',result);return result


def worker(out, protocol, seed, mode):
    out.mkdir(exist_ok=False);start=time.perf_counter();records=[]
    cases=base.load(seed['cases']['path']);join_proof=base.load(protocol['join_proof']['path'])
    join_keys={s['source'] for s in join_proof['steps']};anchors={a['source'] for a in base.load(protocol['join_anchors']['path'])}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'h';base.restore_archive(seed['seeds'][mode]['archive'],path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        initial=base.rows(h);initial_pairs=pairs(h);decisions={};startup=time.perf_counter()-start
        try:
            for visit in range(protocol['visits']):
                for case in cases:
                    tick=time.perf_counter();before=base.rows(h);before_pairs=pairs(h)
                    h.set_admission_budget(protocol['prefix_limit']);h.counts=Counter()
                    root=h._canonical(case['source'],0)[2];present_before=h._load(root) is not None
                    capped=False
                    try:h._edge(case['source'],0)
                    except AdmissionExhausted:capped=True
                    prefix=dict(entered=len(h.admitted),probes=h.counts['probe_attempts'],counts=dict(h.counts),
                        admitted_ids=sorted(map(base.key_sha,h.admitted)),seconds=time.perf_counter()-tick)
                    batches=[];session=None;closed=False
                    if h._load(root) is not None:
                        session=ScopedNestedRefinement(h,root,decisions.get(root))
                        for _ in range(protocol['max_batches']):
                            if session.coverage.closed()[0]:break
                            batches.append(session.batch(state_limit=protocol['state_limit'],pair_limit=protocol['pair_limit']))
                        decisions[root]=dict(session.decisions);closed=session.coverage.closed()[0]
                        flags,plan=base.compose(h,[root],session.registry,Counter())
                        proof=base.expand(h,plan,[root],session.registry,Counter());assert flags==[closed]
                        base.split.verify_positive(h,proof,proof['roots'],list(session.records.values()),Counter())
                    else:
                        proof=dict(format='expanded-positive-coverage-v1',roots=[],steps=[])
                    after=base.rows(h);after_pairs=pairs(h);new=set(after)-set(before)
                    admitted=set(prefix['admitted_ids'])|{k for b in batches for k in b['admitted_ids']}
                    assert before.items()<=after.items() and before_pairs.items()<=after_pairs.items()
                    assert set(map(base.key_sha,new))<=admitted
                    elapsed=time.perf_counter()-tick
                    checked=check_query(path,protocol['options'],case['source'],root,proof,closed) if h._load(root) is not None else None
                    keys={s['source'] for s in proof['steps']}
                    records.append(dict(case=case['case'],visit=visit,root=root,present_before=present_before,
                        prefix_capped=capped,prefix=prefix,batches=batches,closed=closed,proof=proof,query_check=checked,
                        entered=prefix['entered']+sum(b['entered'] for b in batches),
                        probes=prefix['probes']+sum(b['probes'] for b in batches),stored=len(new),
                        assumptions=sum(b['selection_counts'].get('bootstrap_fresh_assumptions',0) for b in batches),
                        added_pairs=len(after_pairs)-len(before_pairs),stored_ids=sorted(map(base.key_sha,new)),
                        join_steps=len(keys&join_keys),join_entries=sorted(map(base.key_sha,keys&anchors)),
                        solve_and_bookkeeping_seconds=elapsed))
            final=base.rows(h);final_pairs=pairs(h)
            assert initial.items()<=final.items() and initial_pairs.items()<=final_pairs.items()
        finally:h.close()
        cold=audit(path,protocol,canonical=True);entry=base.archive(path,out)
    summary=dict(mode=mode,queries=len(cases),visits=protocol['visits'],covered=sum(r['closed'] for r in records if r['visit']==0),
        entered=sum(r['entered'] for r in records),probes=sum(r['probes'] for r in records),stored=len(final)-len(initial),
        added_pairs=len(final_pairs)-len(initial_pairs),assumptions=sum(r['assumptions'] for r in records),
        repeat_entered=sum(r['entered'] for r in records if r['visit']>0),repeat_stored=sum(r['stored'] for r in records if r['visit']>0),
        patterns=len(final),pairs=len(final_pairs),pattern_digest=base.key_sha(base.encode(sorted(final.items()))),
        pair_digest=base.key_sha(base.encode(sorted(final_pairs.items()))),startup_seconds=startup,
        solve_and_bookkeeping_seconds=sum(r['solve_and_bookkeeping_seconds'] for r in records),
        query_check_seconds=sum(r['query_check']['seconds'] for r in records if r['query_check']),
        cold_seconds=cold['seconds'],compression_seconds=entry['seconds'],stream_wall_seconds=time.perf_counter()-start,
        peak_rss_raw=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,platform=sys.platform,
        peak_rss_unit='bytes' if sys.platform=='darwin' else 'KiB',database_bytes=entry['database_bytes'],compressed_bytes=entry['compressed_bytes'])
    base.write(out/'report.json',dict(mode=mode,summary=summary,records=records,archive=entry,cold=cold))
    print(base.encode({k:summary[k] for k in ('mode','covered','entered','probes','stored','repeat_entered','stream_wall_seconds')}),flush=True)


def run(out):
    out.mkdir(exist_ok=False);previous=base.load(PARENT/'validation.json');sources=dict(previous['source_fingerprints'])
    for p,d in sources.items():assert base.sha(p)==d,p
    for p in ('experiments/cnf_join_workloads.py','solver/test_cnf_join_workloads.py','experiments/compare_cnf_join_transfer.py','experiments/validate_cnf_join_transfer.py'):
        sources[p]=base.sha(p)
    control=base.load(CONTROL/'checkpoint.json')
    protocol=dict(checkpoint=binding(PARENT/'checkpoint.json'),control=binding(CONTROL/'checkpoint.json'),
        join_anchors=binding(PARENT/'joins/anchors.json'),join_proof=binding(PARENT/'joins/proof.json'),
        options=base.OPTIONS,queries=control['queries'],source_fingerprints=sources,
        prefix_limit=128,state_limit=128,pair_limit=16,max_batches=2,visits=2,orders=[MODES,tuple(reversed(MODES))],
        limitations=['Synthetic controlled clause-splitting preimages and paired clause-deletion edits; not held-out or arbitrary-SAT coverage.',
            'Runtime receives only CNFs and uses the unchanged ordinary depth-zero acquisition and committed scoped continuation. No construction witness, anchor label or gate guides solving.',
            'Two matched histories: pre-case-10 authority, or that history plus exact join proof dependencies. Both are isolated copies; latest authority is preserved and will be included in final union.',
            'Prefix budget128 plus at most two continuation batches of128 admissions/16 operations each. These are separate charged stages, at most384 admissions per query visit; repeated admissions count again.',
            'Queries share their growing history. The second visit measures repeated reuse. Cold query checks occur per result and full archive checking once at stream end.',
            'Clock includes restore, input normalization, lookup, solving, bookkeeping, query checks, final audit and compression; imports and final report write excluded. Peak RSS includes all phases. Preparation and historical acquisition are charged separately.',
            'Edits break the specified one-step image, not necessarily satisfiability or all possible reuse. Unknown remains unknown.'])
    base.write(out/'protocol.json',protocol);seed=prepare(out,protocol);samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'seeds.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_raw'];fixed=[k for k in a if k not in timed and k!='mode']
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed}}
    base.write(out/'report.json',dict(protocol_sha256=base.sha(out/'protocol.json'),seed=binding(out/'seeds.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
