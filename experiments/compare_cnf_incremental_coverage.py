#!/usr/bin/env python3
"""Replay the saved forced expansion with full versus incremental composition.

No discovery records are changed. Warm matched arms share a verified parent and
complete refreshed external catalog. First construction, cold rebuilding,
serialization and whole-history authority costs are separately reported.
"""
from collections import Counter
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.cnf_incremental_coverage import CoverageIndex
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expanded_coverage import checked_inventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import compose, verify_plan
from experiments.continue_cnf_source_local import restore_checkpoint
from experiments.continue_cnf_reused_branch import routes_for
from experiments.cnf_source_local import check_delta
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, digests, apply_delta, unpack, WithoutGrowth

BEFORE = Path('experiments/results/cnf-source-local-checked/report.json')
AFTER = Path('experiments/results/cnf-local-forcing/report.json')
FILES = ['experiments/cnf_incremental_coverage.py', 'experiments/compare_cnf_incremental_coverage.py',
         'solver/test_cnf_incremental_coverage.py', 'experiments/cnf_route_composition.py']


def check_plans(h, roots, routes, closed, plans):
    for route_view, flags, plan in zip((routes,WithoutGrowth(routes)),closed,plans,strict=True):
        claimed = [r for r,c in zip(roots,flags,strict=True) if c]
        verify_plan(h,plan,claimed,route_view,Counter())


def full(h, roots, routes):
    counts=Counter(); results=[compose(h,roots,v,counts) for v in (routes,WithoutGrowth(routes))]
    closed,plans=map(list,zip(*results));check_plans(h,roots,routes,closed,plans)
    return closed,plans,dict(counts)


def size(index):
    return dict(nodes=len(index.keys),rules=len(index.rules),premises=sum(len(cs) for _,_,cs in index.rules),
        justified=len(index.justified),waiting_entries=sum(map(len,index.waiting.values())),
        unique_node_key_bytes=sum(len(k.encode()) for k in index.keys))


def run(out):
    started=time.perf_counter();out.mkdir(exist_ok=False)
    r=dict(format='incremental-coverage-comparison-v1',
        before=dict(path=str(BEFORE),sha256=sha(BEFORE)),after=dict(path=str(AFTER),sha256=sha(AFTER)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={name:sha(name) for name in FILES},limitations=[
            'One archived forced update on 83 adaptively reused development cases; no new coverage or holdout.',
            'Warm matched arms start with the same verified parent and complete refreshed route catalog; reset copies are untimed.',
            'Global external-route verification and catalog comparison are still required; this is not fully delta-local discovery.',
            'Immutable historical patterns, unchanged policy and append-only complete external routes are required.',
            'Cold index replay rechecks the entire reachable catalog, including negative obligations; it is not a trusted hash-only load.',
            'Index artifacts add storage to preserved history; logical bytes and graph counts are not peak RAM.',
            'Two reversed warm repetitions share process and OS caches; no confidence intervals or unrestricted SAT bound.'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);history=tmp/'history';tick=time.perf_counter()
        parent,*evidence=restore_checkpoint(BEFORE,history,tmp)
        r['restore_seconds']=time.perf_counter()-tick
        target=json.loads(AFTER.read_text())
        if target['parent']!=r['before']:raise ValueError('Unexpected forced-update parent')
        for path,digest in target['fingerprints'].items():
            if sha(path)!=digest:raise ValueError('Changed saved forcing implementation')
        r['options']=parent['options'];r['evidence_counts']=list(map(len,evidence))
        if digests(history)!=target['seed_table_digests']:raise ValueError('Incorrect parent authority')
        tick=time.perf_counter();h=BudgetedInventory(history,**parent['options']);h.set_admission_budget(0)
        routes=routes_for(h,evidence)
        roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in parent['cases']]
        r['parent_route_preparation_seconds']=time.perf_counter()-tick
        print('build complete parent indexes',flush=True);tick=time.perf_counter();counts=Counter()
        original=[CoverageIndex(h,roots,v,counts) for v in (routes,WithoutGrowth(routes))]
        r['first_index_build_seconds']=time.perf_counter()-tick;r['first_index_counts']=dict(counts)
        assert original[0].closed()==parent['final_closed']
        check_plans(h,roots,routes,[i.closed() for i in original],[i.certificate() for i in original])
        r['parent_indexes']=list(map(size,original));r['parent_historical_cache']=checked_inventory(h)[1]
        # The only transition is the hash-bound saved append; conflict checking
        # rejects changed old payloads. All five sidecar lists are unchanged.
        d=target['delta'];delta=tmp/'delta'
        if sha(d['path'])!=d['sha256']:raise ValueError('Changed saved delta')
        unpack(d['path'],delta,d['database_sha256']);tick=time.perf_counter();apply_delta(history,delta)
        r['merge_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();r['delta_check']=check_delta(history,delta,parent['options'])
        r['delta_check_seconds']=time.perf_counter()-tick
        if digests(history)!=target['logical_table_digests']:raise ValueError('Incorrect updated authority')
        tick=time.perf_counter();newroutes=routes_for(h,evidence)
        r['warm_complete_route_refresh_seconds']=time.perf_counter()-tick
        expected=[target['final_closed'],target['without_growth_closed']]
        r['samples']=[];updated=None
        for repeat,order in enumerate((('full','incremental'),('incremental','full'))):
            for mode in order:
                # Repeated experiment reset, not a production update operation.
                indexes=copy.deepcopy(original) if mode=='incremental' else None
                print(json.dumps(dict(phase='matched warm update',mode=mode,repeat=repeat)),flush=True)
                tick=time.perf_counter()
                if mode=='full':closed,plans,cc=full(h,roots,newroutes)
                else:
                    counts=Counter()
                    closed=[i.refresh(h,v,counts) for i,v in zip(indexes,(newroutes,WithoutGrowth(newroutes)),strict=True)]
                    plans=[i.certificate() for i in indexes]
                    check_plans(h,roots,newroutes,closed,plans);cc=dict(counts);updated=indexes
                elapsed=time.perf_counter()-tick
                if closed!=expected:raise ValueError('Coverage disagrees with checked archive')
                r['samples'].append(dict(mode=mode,repeat=repeat,seconds=elapsed,counts=cc,closed=list(map(sum,closed))))
        r['means']={mode:sum(x['seconds'] for x in r['samples'] if x['mode']==mode)/2 for mode in ('full','incremental')}
        # A complete audit after the update checks that source selection omitted
        # no newly reachable rule; this diagnostic is outside matched timings.
        tick=time.perf_counter();counts=Counter()
        for i,v in zip(updated,(newroutes,WithoutGrowth(newroutes)),strict=True):i.audit(h,v,counts)
        r['post_update_full_catalog_audit_seconds']=time.perf_counter()-tick
        r['post_update_full_catalog_audit_counts']=dict(counts)
        r['final_indexes']=list(map(size,updated));r['final_closed']=expected[0]
        r['without_growth_closed']=expected[1];r['database_bytes']=history.stat().st_size
        tick=time.perf_counter();r['index']=archive_json(out/'coverage-index.json.gz',[i.payload() for i in updated])
        r['serialization_seconds']=time.perf_counter()-tick
        r['certificate']=archive_json(out/'coverage.json.gz',updated[0].certificate())
        r['warm_historical_cache']=checked_inventory(h)[1];assert not h.admitted;h.close()
        # Cold reference and cold index reconstruction each start with fresh
        # verifier caches. Include the full semantic route-preparation cost.
        r['cold']={}
        for mode in ('full','index'):
            print(json.dumps(dict(phase='cold replay',mode=mode)),flush=True);whole=time.perf_counter()
            h=BudgetedInventory(history,**parent['options']);h.set_admission_budget(0)
            tick=time.perf_counter();fresh=routes_for(h,evidence);prep=time.perf_counter()-tick
            tick=time.perf_counter()
            if mode=='full':closed,plans,cc=full(h,roots,fresh)
            else:
                data=read_archive(r['index']);counts=Counter()
                loaded=[CoverageIndex.load(d,h,roots,v,counts) for d,v in zip(data,(fresh,WithoutGrowth(fresh)),strict=True)]
                closed=[i.closed() for i in loaded];plans=[i.certificate() for i in loaded]
                check_plans(h,roots,fresh,closed,plans);cc=dict(counts)
            operation=time.perf_counter()-tick
            assert closed==expected and not h.admitted
            r['cold'][mode]=dict(preparation_seconds=prep,operation_seconds=operation,
                total_seconds=time.perf_counter()-whole,counts=cc,historical_cache=checked_inventory(h)[1])
            h.close()
        if digests(history)!=target['logical_table_digests']:raise ValueError('Composition mutated history')
    r['pipeline_seconds']=time.perf_counter()-started
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(warm_means=r['means'],cold={k:v['total_seconds'] for k,v in r['cold'].items()},
        index_bytes=r['index']['compressed_bytes'],closed=sum(r['final_closed']))),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
