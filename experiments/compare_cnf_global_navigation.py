#!/usr/bin/env python3
"""Separate cold checking, retained inventory, and indexed original navigation.

Replay the exact archived six-pattern append; do not acquire new SAT states.
Every arm pays initial construction, selection, checked append and final query.
"""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_original_handoff import (
    restore_base, restore_checkpoint, routes_for, add_splits, full, select,
    BudgetedInventory, read_archive, archive_json, digests, sha, unpack,
    apply_delta, check_delta, FILES as INHERITED_FILES)
from experiments.compare_cnf_incremental_coverage import check_plans, size
from experiments.compare_cnf_probe_continuation import WithoutGrowth
from experiments.cnf_incremental_coverage import CoverageIndex
from experiments.cnf_indexed_navigation import select as indexed_select
from experiments.cnf_pattern_inventory import encode

AFTER=Path('experiments/results/cnf-original-handoff/report.json')
FILES=['experiments/compare_cnf_global_navigation.py','experiments/cnf_indexed_navigation.py',
       'solver/test_cnf_indexed_navigation.py','experiments/cnf_incremental_coverage.py',
       'experiments/compare_cnf_incremental_coverage.py','experiments/cnf_route_composition.py',
       'experiments/cnf_target_probe.py','experiments/cnf_split_frontier.py',*INHERITED_FILES]


def phase(h,evidence,bridges,roots,mode,indexes):
    started=time.perf_counter();tick=started;routes=routes_for(h,evidence,bridges)
    r=dict(route_seconds=time.perf_counter()-tick);tick=time.perf_counter()
    if mode=='indexed':
        counts=Counter();views=(routes,WithoutGrowth(routes))
        if indexes is None:indexes=[CoverageIndex(h,roots,v,counts) for v in views]
        else:
            for index,view in zip(indexes,views,strict=True):index.refresh(h,view,counts)
        closed=[i.closed() for i in indexes];plans=[i.certificate() for i in indexes]
        check_plans(h,roots,routes,closed,plans);cc=dict(counts)
        r['indexes']=list(map(size,indexes))
    else:closed,plans,cc=full(h,roots,routes)
    r.update(composition_seconds=time.perf_counter()-tick,composition_counts=cc,closed=closed)
    tick=time.perf_counter();counts=Counter()
    chosen=(indexed_select(h,routes,evidence,roots,closed[0],counts,indexes[0]) if mode=='indexed'
            else select(h,routes,evidence,roots,closed[0],counts))
    r.update(selection_seconds=time.perf_counter()-tick,selection_counts=dict(counts),
        checked_nodes=len(h.checked),prepared_checked_nodes=len(h.prepared.checked),
        query_seconds=time.perf_counter()-started)
    assert not h.admitted
    return r,indexes,chosen,plans,routes


def run(out):
    start=time.perf_counter();out.mkdir(exist_ok=False);target=json.loads(AFTER.read_text())
    before=Path(target['parent']['path']);assert sha(before)==target['parent']['sha256']
    for p,d in target['fingerprints'].items():assert sha(p)==d,p
    r=dict(format='global-navigation-comparison-v1',before=target['parent'],after=dict(path=str(AFTER),sha256=sha(AFTER)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={p:sha(p) for p in FILES},samples=[],limitations=[
        'Replay of the exact archived six-pattern append from 67/83 to 68/83; no newly acquired patterns, original coverage or holdout cases.',
        'Two reversed-order repetitions of cold_full, warm_full and indexed; all pay initial construction and initial/final original selection.',
        'cold_full reopens its inventory for the final query; warm_full retains checked nodes but fully recomposes; indexed retains nodes and coverage graphs and uses indexed closure queries in navigation.',
        'The same conflict-checked, hash-bound append preserves old rows; all methods rebuild the complete external route catalog. Index refresh compares that whole catalog.',
        'Indexed selection checks root/flag/catalog binding; immutable patterns, fixed policy, checked cache ownership and no concurrent changes remain caller obligations. Out-of-graph queries fall back to full composition.',
        'Persistent authority and archived results are unchanged. Derived indexes remain in memory and are reconstructed on restart, not serialized as a trusted negative cache.',
        'Phase timings include routes, composition, original proof checking and selection. Complete sequence also charges copying, delta checks, digests and output serialization.',
        'Graph/cache counts and logical key bytes are not peak RAM; two observations sharing OS caches do not establish a general speedup or unrestricted SAT bound.'])
    with tempfile.TemporaryDirectory() as td, patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh acquisition')):
        tmp=Path(td);seed=tmp/'seed';tick=time.perf_counter()
        parent,*evidence=restore_base(before,seed,tmp)
        r['restore_seconds']=time.perf_counter()-tick;r['options']=parent['options']
        assert digests(seed)==target['seed_table_digests'];seed_hash=sha(seed)
        d=target['delta'];assert sha(d['path'])==d['sha256'];delta=tmp/'update';unpack(d['path'],delta,d['database_sha256'])
        updated=add_splits(evidence,read_archive(target['splits']));bridges=read_archive(target['bridges'])
        assert bridges==read_archive(parent['bridges'])
        expected_selections=[read_archive(parent['next_selection']),read_archive(target['next_selection'])]
        expected_flags=[[parent['final_closed'],parent['without_growth_closed']],[target['final_closed'],target['without_growth_closed']]]
        for repeat,order in enumerate((('cold_full','warm_full','indexed'),('indexed','warm_full','cold_full'))):
            for mode in order:
                name=f'{repeat}-{mode}';dest=out/name;dest.mkdir();history=tmp/name;whole=time.perf_counter();shutil.copyfile(seed,history)
                h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
                roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in target['cases']]
                sample=dict(repeat=repeat,mode=mode,phases=[]);indexes=None
                try:
                    for stage,ev in enumerate((evidence,updated)):
                        if stage:
                            tick=time.perf_counter();apply_delta(history,delta);sample['merge_seconds']=time.perf_counter()-tick
                            tick=time.perf_counter();sample['delta_counts']=check_delta(history,delta,r['options']);sample['delta_check_seconds']=time.perf_counter()-tick
                            tick=time.perf_counter();assert digests(history)==target['logical_table_digests'];sample['digest_seconds']=time.perf_counter()-tick
                            if mode=='cold_full':h.close();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
                        print(json.dumps(dict(repeat=repeat,mode=mode,stage=stage,phase='query')),flush=True)
                        result,indexes,chosen,plans,routes=phase(h,ev,bridges,roots,mode,indexes)
                        assert result['closed']==expected_flags[stage] and chosen==expected_selections[stage]
                        tick=time.perf_counter()
                        result['selection']=archive_json(dest/f'selection-{stage}.json.gz',chosen)
                        result['certificate']=archive_json(dest/f'coverage-{stage}.json.gz',plans[0])
                        result['serialization_seconds']=time.perf_counter()-tick
                        sample['phases'].append(result)
                    sample['seconds']=time.perf_counter()-whole
                    # Complete audit is an independent diagnostic, outside the measured sequence.
                    if indexes is not None:
                        counts=Counter();tick=time.perf_counter()
                        for index,view in zip(indexes,(routes,WithoutGrowth(routes)),strict=True):index.audit(h,view,counts)
                        sample['full_catalog_audit']=dict(seconds=time.perf_counter()-tick,counts=dict(counts))
                    assert not h.admitted and digests(history)==target['logical_table_digests']
                finally:h.close()
                r['samples'].append(sample);print(json.dumps(dict(repeat=repeat,mode=mode,seconds=sample['seconds'],final_query_seconds=sample['phases'][1]['query_seconds'])),flush=True)
        assert sha(seed)==seed_hash;r['seed_unchanged']=True
        r['database_bytes']=seed.stat().st_size;r['expanded_database_bytes']=target['expanded_database_bytes']
        r['final_closed']=target['final_closed'];r['without_growth_closed']=target['without_growth_closed']
        r['means']={mode:dict(sequence_seconds=sum(s['seconds'] for s in r['samples'] if s['mode']==mode)/2,
            final_query_seconds=sum(s['phases'][1]['query_seconds'] for s in r['samples'] if s['mode']==mode)/2) for mode in order}
    r['pipeline_seconds']=time.perf_counter()-start;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(means=r['means'],pipeline_seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
