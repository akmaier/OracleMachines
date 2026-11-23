#!/usr/bin/env python3
"""Prespecified posthoc timing repeats after a zero-hit control showed variation."""
from contextlib import nullcontext
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_preimage_fusion as study
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_preimage_fusion import fused_preimages
base=study.base


def run(out):
    protocol=out/'repeat-protocol.json';assert not protocol.exists()
    p=base.load(out/'protocol.json');cases=study.bound(p['cases'])
    plan=dict(parent=study.binding(out/'protocol.json'),groups=['controls','novel','branch-original'],repeats=6,
        orders=[list(study.MODES),list(reversed(study.MODES))],script_sha256=base.sha(__file__),reason='Original isolated branch has no preimage calls but a large apparent timing gain in the first order; check query variability without altering frozen kernels or samples.',limitations=[
        'Posthoc repeated timings on the same exposed/nearby inputs, not new held-out cases. Every case stream restores its exact prefix; no answer-bearing final union is seeded.',
        'Serial balanced query-only samples in one interpreter. Full historical cold audit is not repeated. Restoration, solver opening and scoped-mode overhead are recorded separately; this does not replace complete-worker accounting.',
        'Each repeated stream must reproduce every frozen native byte and partition, so no new proof needs merging. All repetitions and both order signs are retained.'])
    base.write(protocol,plan);samples=[]
    for group in plan['groups']:
        for repeat in range(plan['repeats']):
            for mode in plan['orders'][repeat%2]:
                streams=[]
                for index in ((31,) if study.native_split(group) else (25,31,61)):
                    cs=[c for c in cases if (c['split'],c['case'])==(group,index)];ref=out/f'{group}-{index}-{mode}-0/report.json';trial=base.load(ref);expected=study.bound(trial['queries'])
                    prefix=study.read_zip(p['prefixes'][group if study.native_split(group) else str(index)]['archive']);queries=[]
                    with tempfile.TemporaryDirectory() as td:
                        path=Path(td)/'db';tick=time.perf_counter();study.restore(prefix,path);restoration=time.perf_counter()-tick
                        tick=time.perf_counter();s=ConsequencePrioritySolver(path);opening=time.perf_counter()-tick
                        try:
                            tick=time.perf_counter()
                            with fused_preimages() if mode=='fused' else nullcontext():
                                setup=time.perf_counter()-tick
                                for c,e in zip(cs,expected):
                                    r=(study.harness.query(s,c,'native',p['branch_limit']) if study.native_split(group)
                                       else study.prepared_run(s,c['candidate'],'probe6',p['node_limit']))
                                    for f in ('status','expanded_nodes','partition'):assert r[f]==e[f]
                                    queries.append(dict(variant=c['variant'],seconds=r['seconds'],expanded_nodes=r['expanded_nodes'],status=r['status']))
                                tick=time.perf_counter()
                            setup+=time.perf_counter()-tick
                            final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES};assert delta==study.read_zip(trial['delta'])
                        finally:s.close()
                    streams.append(dict(case=index,reference=study.binding(ref),queries=queries,restoration_seconds=restoration,opening_seconds=opening,mode_setup_seconds=setup,output_matches_trial=True))
                sample=dict(group=group,repeat=repeat,mode=mode,streams=streams,query_seconds=sum(q['seconds'] for st in streams for q in st['queries']),mode_setup_seconds=sum(st['mode_setup_seconds'] for st in streams))
                sample['query_with_mode_setup_seconds']=sample['query_seconds']+sample['mode_setup_seconds'];samples.append(sample)
            print('finished',group,repeat,flush=True)
    summary={}
    for group in plan['groups']:
        paired=[]
        for repeat in range(plan['repeats']):
            arms={s['mode']:s for s in samples if (s['group'],s['repeat'])==(group,repeat)}
            paired.append(dict(repeat=repeat,**{m:arms[m]['query_seconds'] for m in study.MODES},change=arms['fused']['query_seconds']-arms['priority']['query_seconds']))
        means={m:sum(x[m] for x in paired)/len(paired) for m in study.MODES}
        charged={m:sum(s['query_with_mode_setup_seconds'] for s in samples if (s['group'],s['mode'])==(group,m))/plan['repeats'] for m in study.MODES}
        summary[group]=dict(means=means,percent_change=100*(means['fused']/means['priority']-1),paired=paired,with_mode_setup_means=charged,with_mode_setup_percent_change=100*(charged['fused']/charged['priority']-1))
    base.write(out/'repeat-report.json',dict(protocol=study.binding(protocol),samples=samples,summary=summary));print(base.encode({k:{f:v[f] for f in ('means','percent_change','with_mode_setup_percent_change')} for k,v in summary.items()}),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
