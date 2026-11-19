#!/usr/bin/env python3
"""Descriptive paired costs; no policy selection or tuning after results."""
from collections import Counter
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_transported_partition as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');groups={};paired={};per_case={};phases={}
    for split in study.SPLITS:
        groups[split]={};paired[split]={};per_case[split]={};phases[split]={}
        for mode in study.MODES:
            summaries=[study.bound(s)['summary'] for s in report['samples'] if s['split']==split and s['mode']==mode]
            groups[split][mode]={}
            for k in ('query_seconds','complete_worker_seconds','checked_python_bytes','database_bytes','cold_seconds','warm_setup_seconds','warm_seconds',
                      'new_payload_bytes','proof_delta_compressed_bytes','partition_bytes','expanded_nodes','persistence_seconds','reconstruction_seconds'):
                groups[split][mode][k]=sum(a[k] for a in summaries)/2
            groups[split][mode]['persisted_delta_and_partition_bytes']=sum(a['proof_delta_compressed_bytes']+a['partition_bytes'] for a in summaries)/2
            groups[split][mode]['new_native_records']=sum(a['new_records'][study.TABLES[0]] for a in summaries)//2
            totals=Counter()
            for sample in report['samples']:
                if sample['split']==split and sample['mode']==mode and sample['repeat']==0:
                    for row in study.bound(study.bound(sample)['queries']):totals.update(row.get('phases',{}))
            phases[split][mode]=dict(totals)
        for mode in study.MODES:
            paired[split][mode]=[]
            for rep in (0,1):
                arms={m:[study.bound(s)['summary'] for s in report['samples'] if s['split']==split and s['mode']==m and s['repeat']==rep] for m in ('affine',mode)}
                paired[split][mode].append({k:sum(x[k] for x in arms[mode])-sum(x[k] for x in arms['affine']) for k in ('query_seconds','complete_worker_seconds','cold_seconds','warm_seconds')})
        for case in study.CASES:
            per_case[split][case]={}
            for mode in study.MODES:
                samples=[study.bound(s) for s in report['samples'] if s['split']==split and s['case']==case and s['mode']==mode]
                rs=study.bound(samples[0]['queries'])
                kinds=Counter(json.loads(payload).get('proof',{}).get('kind','sat-witness') for _,payload in study.read_zip(samples[0]['delta'])[study.TABLES[0]])
                per_case[split][case][mode]=dict(query_seconds=sum(s['summary']['query_seconds'] for s in samples)/2,
                    complete_worker_seconds=sum(s['summary']['complete_worker_seconds'] for s in samples)/2,
                    new_records=samples[0]['summary']['new_records'],new_payload_bytes=samples[0]['summary']['new_payload_bytes'],
                    checked_python_bytes=samples[0]['summary']['checked_python_bytes'],expanded_nodes=samples[0]['summary']['expanded_nodes'],
                    native_proof_kinds=dict(kinds),
                    attempts=[dict(variant=r['variant'],route=r['route'],status=r['status'],expanded_nodes=r['expanded_nodes'],missing=len((r.get('descriptor') or {}).get('missing',[]))) for r in rs],
                    branch_structural_counters=[[{k:v for k,v in b.get('result',{}).get('metrics',{}).items() if k.startswith(('binary_backbone_','horn_','implication_'))} for b in r.get('branches',[])] for r in rs],
                    routes=[r['route'] for r in rs],statuses=[r['status'] for r in rs],
                    branch_expansions=[[b.get('result',{}).get('metrics',b.get('metrics',{})).get('expanded_nodes',0) for b in r.get('branches',[])] for r in rs],
                    screens=[[dict(order=x['order'],admitted=x['admitted'],terminal=sum(b['conflict'] is not None for b in x['branches'])) for x in r.get('screens',[])] for r in rs])
    reductions={split:{mode:{k:1-v/groups[split]['affine'][k] for k,v in arm.items() if groups[split]['affine'].get(k)} for mode,arm in modes.items()} for split,modes in groups.items()}
    result=dict(groups=groups,per_case=per_case,paired_difference_from_affine=paired,reductions_from_affine=reductions,first_order_phase_seconds=phases,
        limitations=['Paired totals sum the three independent case streams. Object/SQLite byte totals are sums of endpoints, not one combined live archive; RSS is not a live retained-space bound.',
        'Complete worker time includes full prefix restoration, two independent cold checks, diagnostic table scans, Python object measurement, serialization and persistence. Query timing excludes these separately reported costs.',
        'Prior precomputation and posthoc candidate selection are sunk historical work, not included in query-time speedups. Prefix construction and this audit remain separate. No automated discovery speedup is established.',
        'Two repeats characterize this constructed pilot only. No confidence interval or representative arbitrary-SAT claim is made.'])
    base.write(out/'analysis.json',result)
    print(base.encode(dict(per_case=per_case,reductions=reductions)),flush=True)

def boundary(out):
    from collections import Counter
    from tempfile import TemporaryDirectory
    from unittest.mock import patch
    import time
    from experiments.cnf_transported_partition import prepare_support
    from experiments.cnf_clause_partition import branch_sources
    from experiments.cnf_partition_screen import screen_branch
    from experiments.cnf_residual_dag import restrict
    from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
    began=time.perf_counter();p=base.load(out/'protocol.json');cases=study.bound(p['cases'])
    case=next(c for c in cases if (c['case'],c['split'],c['variant'])==(31,'edits','delete'))
    report=base.load(out/'edits-31-reverse-0/report.json');rows=study.bound(report['queries'])
    prefix=study.read_zip(p['prefixes']['31']['archive']);delta=study.read_zip(report['delta'])
    before={t:[[k,v] for k,v in delta[t] if k in set(rows[0]['new_ids'][t])] for t in study.TABLES}
    assert all(case['root'] not in dict(prefix[t]+before[t]) for t in study.TABLES)
    attempts=[];counts=Counter()
    with TemporaryDirectory() as td:
        path=Path(td)/'db';study.restore(prefix,path,before);digest=base.sha(path);solver=CanonicalVerifySnapshot(path)
        try:
            with patch.object(solver,'_expand',side_effect=AssertionError('Diagnostic acquisition')),patch.object(solver,'_store',side_effect=AssertionError('Diagnostic publication')):
                plan,desc=prepare_support(solver,case['candidate']);assert len(desc['missing'])==6
                for order in ('forward','reverse'):
                    missing=desc['missing'] if order=='forward' else list(reversed(desc['missing']));branches=branch_sources(case['source'],missing,counts)[1];screens=[]
                    for _,_,child in branches:
                        screen=screen_branch(solver,child,counts);cnf,_,key=solver._canonical(child)
                        node=solver._read(key,cnf);fixed={abs(lit):lit>0 for lit,_ in screen['trace']};residual=restrict(cnf,fixed,counts)
                        residual_cnf,_,residual_key=solver._canonical(residual);known_residual=solver._read(residual_key,residual_cnf)
                        screens.append(dict(screen=screen,known_branch=None if node is None else node['answer'],
                            known_residual=None if known_residual is None else known_residual['answer'],
                            residual_widths=dict(Counter(map(len,residual_cnf))),
                            binary=all(len(c)<=2 for c in residual_cnf),horn=all(sum(l>0 for l in c)<=1 for c in residual_cnf),
                            dual_horn=all(sum(l<0 for l in c)<=1 for c in residual_cnf)))
                    attempts.append(dict(order=order,branches=screens,terminal=sum(s['screen']['conflict'] is not None for s in screens)))
            solver_counts=dict(solver.counts)
        finally:solver.close()
        assert digest==base.sha(path)
    result=dict(case=case,starting_prefix=p['prefixes']['31'],source_report=study.binding(out/'edits-31-reverse-0/report.json'),
        allowed_addition_ids=rows[0]['new_ids'],support=desc,plan_counts=dict(plan.counts),attempts=attempts,counts=dict(counts),solver_counts=solver_counts,
        seconds=time.perf_counter()-began,limitations=['Read-only posthoc description. The state includes only the historical prefix and first addition; no deletion results or later proofs.',
            'No search or publication occurs. Unit-conflict screening, exact cached authority and syntactic width/Horn summaries are described; they do not prove cheap search for a nonterminal mixture.',
            'The timed five-clause policy is unchanged. This is a candidate for a future frozen experiment, not an extra completed target or measured speedup.'])
    base.write(out/'next-boundary.json',result)
    print(base.encode(dict(terminal={a['order']:a['terminal'] for a in attempts},seconds=result['seconds'])),flush=True)

if __name__=='__main__':
    if len(sys.argv)>2 and sys.argv[2]=='boundary':boundary(Path(sys.argv[1]))
    else:analyze(Path(sys.argv[1]))
