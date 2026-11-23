#!/usr/bin/env python3
"""Acquire the exposed donor, then census guarded supports against causal cores."""
from collections import Counter
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_prefix as prior
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_preimage_fusion import fused_preimages
from experiments.cnf_joint_prefix import reused_joint_prefix
from experiments.cnf_conditional_unit_support import extract,match
from experiments.cnf_support_plan import CausalPlan
from experiments.cnf_probed_partition import acquire
base=prior.base;PARENT=Path('experiments/results/cnf-joint-prefix')


def run(out):
    p=base.load(PARENT/'protocol.json');seed=prior.read_zip(p['prefixes']['branch-original']['archive']);source=p['branch_spec']['source']
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';prior.restore(seed,path);s=ConsequencePrioritySolver(path)
        try:
            with fused_preimages(),reused_joint_prefix():
                result=acquire(s,source,p['branch_limit']);assert result['status']=='unsat'
                s.counts=Counter();tick=time.perf_counter();bundle,counts=extract(s,source);extract_seconds=time.perf_counter()-tick;reader_counts=dict(s.counts)
                plan=CausalPlan(s);tick=time.perf_counter();core=plan.prepare(bundle['origin']);core_seconds=time.perf_counter()-tick
                cnf,names,_=s._canonical(source);core_source=[[(1 if l>0 else -1)*names[abs(l)-1] for l in cnf[i]] for i in core['indices']]
            final=prior.tables(s);delta={t:[[k,v] for k,v in final[t][len(seed[t]):]] for t in prior.TABLES}
        finally:s.close()
    archive=prior.write_zip(out/'donor-delta.json.gz',delta);base.write(out/'templates.json',bundle)
    members=set(map(tuple,core_source));samples=[]
    other=next(o for o in base.load(PARENT/'next-target.json')['observations'] if o['split']=='novel')['acquisitions'][2]['source']
    sources=[('donor',source),('nearby',other)]
    for i,entry in enumerate(bundle['entries']):
        chosen=entry['template']['clauses'][0];sources.append((f'delete-reason-{i}',[cl for cl in source if tuple(cl)!=tuple(chosen)]))
    for label,target in sources:
        c=Counter();tick=time.perf_counter();matched=[i for i,e in enumerate(bundle['entries']) if match(target,e['template'],c)];elapsed=time.perf_counter()-tick
        samples.append(dict(label=label,source=target,matched=matched,whole_causal_core_contained=members<=set(map(tuple,target)),counts=dict(c),seconds=elapsed))
    base.write(out/'exploration.json',dict(parent=prior.binding(PARENT/'checkpoint.json'),prefix=p['prefixes']['branch-original']['archive'],source=source,donor=result,
        donor_delta=archive,bundle=prior.binding(out/'templates.json'),extract_seconds=extract_seconds,extract_counts=counts,reader_counts=reader_counts,
        whole_core=dict(source=core_source,root=core['root'],seconds=core_seconds,counts=dict(plan.counts)),samples=samples,
        script_sha256=base.sha(__file__),limitations=['Exposed donor and targeted support deletions. Donor acquisition and both extraction costs are charged separately; no final union seeds this experiment.','Matching gives conditional coverage only. A missing whole causal core and a matched leaf are not a whole-query decision. Supplied identity/sign maps are not an automatic correspondence algorithm.']))
    print(base.encode(dict(donor_expansions=result['metrics'].get('expanded_nodes',0),templates=len(bundle['entries']),extract_seconds=extract_seconds,core_seconds=core_seconds,core_clauses=len(core_source),
        entries=[dict(clauses=len(e['template']['clauses']),literals=sum(map(len,e['template']['clauses'])),assumptions=e['template']['assumptions'],path=e['path_assignment'],trace=len(e['template']['trace'])) for e in bundle['entries']],
        samples=[dict(label=x['label'],matched=x['matched'],whole_core=x['whole_causal_core_contained']) for x in samples])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
