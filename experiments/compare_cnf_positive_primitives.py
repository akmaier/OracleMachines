#!/usr/bin/env python3
"""Compare historical and hybrid primitive replay of the same expanded graph."""
from collections import Counter
from contextlib import ExitStack
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_reused_branch import restore_checkpoint
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_expanded_coverage import verify_expanded, checked_inventory
from experiments.cnf_positive_primitives import verify_positive

PARENT = Path('experiments/results/cnf-reused-branch/report.json')
EXPANDED = Path('experiments/results/cnf-expanded-coverage/report.json')
FILES = ['experiments/cnf_positive_primitives.py', 'experiments/compare_cnf_positive_primitives.py',
         'solver/test_cnf_positive_primitives.py']


def run(out):
    started=time.perf_counter(); out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td, ExitStack() as stack:
        tmp=Path(td); path=tmp/'history'; restore_started=time.perf_counter()
        parent,*evidence=restore_checkpoint(PARENT,path,tmp)
        previous=json.loads(EXPANDED.read_text()); proof=read_archive(previous['expanded_certificate'])
        r=dict(format='positive-primitive-replay-study-v1',
            parent=dict(path=str(PARENT),sha256=sha(PARENT)),
            expanded_study=dict(path=str(EXPANDED),sha256=sha(EXPANDED)),
            certificate=previous['expanded_certificate'],
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in FILES},restore_seconds=time.perf_counter()-restore_started,
            evidence_counts=[len(x) for x in evidence],inventory_bytes=path.stat().st_size,
            inventory_sha256=sha(path),logical_table_digests=digests(path),
            limitations=[
                'Same positive graph for 58/83 reused development inputs, with no new structural coverage or decision result.',
                'Direct rules validate semantic premises, not historical profile completeness, proposal ranking or losing alternatives.',
                'External rules and subsumption still use full original validators. Their historical dependencies are not pruned.',
                'Positive results never enter the historical checked-node maps; this is not a replacement for archive audit or negative coverage.',
                'Two repetitions with reversed orders and fresh verifier objects, shared OS caches; no confidence interval.',
                'Warm replay creates fresh positive/route objects but retains inventory/probe caches; no persistent positive-validation cache.',
                'Logical node and key payloads exclude Python objects, peak RAM and all other caches.',
                'Restoration, all five sidecar indexes, validation and reading full historical row payloads remain required.',
                'No new standalone certificate, discovery integration, Lean refinement or unrestricted polynomial bound.'])
        assert r['logical_table_digests']==parent['logical_table_digests']
        h=BudgetedInventory(path,**parent['options']); h.set_admission_budget(0)
        roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in parent['cases']]
        claimed=[k for k,closed in zip(roots,parent['final_closed'],strict=True) if closed]
        assert proof['roots']==claimed; h.close()
        proof_keys={s['source'] for s in proof['steps']}
        r.update(roots=len(claimed),steps=len(proof['steps']),samples=[])
        stack.enter_context(patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('new recognition')))
        for name in ('experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes',
                     'experiments.cnf_learning_continuation.discover_equivalence_probes',
                     'experiments.cnf_affine_clause.discover'):
            stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
        profiles={}
        for repeat,order in enumerate((('historical','primitive'),('primitive','historical'))):
            for mode in order:
                print(json.dumps(dict(repeat=repeat,mode=mode,phase='cold replay')),flush=True)
                tick=time.perf_counter()
                h=BudgetedInventory(path,**parent['options']); h.set_admission_budget(0)
                h.db.execute('PRAGMA query_only=ON'); counts=Counter()
                verify=verify_positive if mode=='primitive' else verify_expanded
                result=verify(h,proof,claimed,evidence,counts)
                elapsed=time.perf_counter()-tick
                routes=result.routes if mode=='primitive' else result
                rows,accounting=checked_inventory(h)
                keys=set(rows)
                profile=dict(historical=accounting,
                    historical_key_sha256=sorted(map(sha_key,keys)),
                    historical_nodes_outside_graph=len(keys-proof_keys),
                    unique_nodes_read=len(keys|proof_keys),
                    raw_graph_nodes_outside_historical=len(proof_keys-keys),
                    external_routes=sum(len(x) for x in routes.by_source.values()),
                    ordinary_prefixes=len(routes.verified),learned_prefixes=len(routes.learned_blocks.verified),
                    learned_bases=len(routes.learned_blocks.contexts))
                if mode in profiles: assert profiles[mode]==profile
                else:
                    profiles[mode]=profile
                    r[mode+'_dependencies']=archive_json(out/f'{mode}-dependencies.json.gz',profile)
                sample=dict(mode=mode,repeat=repeat,cold_seconds=elapsed,counts=dict(counts),
                    current_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),route_counts=dict(routes.counts),
                    historical_nodes=accounting['unique_nodes'],historical_node_json_bytes=accounting['unique_node_json_bytes'])
                assert not h.admitted
                warm=time.perf_counter();warm_counts=Counter()
                verify(h,proof,claimed,evidence,warm_counts)
                sample.update(warm_seconds=time.perf_counter()-warm,warm_counts=dict(warm_counts))
                assert checked_inventory(h)[1]==accounting and not h.admitted
                h.close();r['samples'].append(sample)
                print(json.dumps({k:sample[k] for k in ('mode','cold_seconds','warm_seconds','historical_nodes')}),flush=True)
        full=set(profiles['historical']['historical_key_sha256']); selected=set(profiles['primitive']['historical_key_sha256'])
        assert selected<=full
        r['omitted_historical_nodes']=len(full-selected)
        r['omitted_historical_key_sha256']=archive_json(out/'omitted-historical-keys.json.gz',sorted(full-selected))
        r['summary']={mode:dict(mean_cold_seconds=sum(s['cold_seconds'] for s in r['samples'] if s['mode']==mode)/2,
            mean_warm_seconds=sum(s['warm_seconds'] for s in r['samples'] if s['mode']==mode)/2,
            historical_nodes=profiles[mode]['historical']['unique_nodes'],
            historical_node_json_bytes=profiles[mode]['historical']['unique_node_json_bytes'],
            unique_nodes_read=profiles[mode]['unique_nodes_read']) for mode in profiles}
        r['cold_reduction_fraction']=1-r['summary']['primitive']['mean_cold_seconds']/r['summary']['historical']['mean_cold_seconds']
        assert sha(path)==r['inventory_sha256'] and digests(path)==r['logical_table_digests']
        r.update(history_bytes_unchanged=True,no_fresh_discovery=True)
    r['pipeline_seconds']=time.perf_counter()-started
    (out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(summary=r['summary'],pipeline_seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path)
    run(p.parse_args().output)
