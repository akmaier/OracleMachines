#!/usr/bin/env python3
"""Matched fresh streams with native binary-subset refutation enabled or disabled."""
from pathlib import Path
from unittest.mock import patch
import copy,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_session as prior
from experiments.cnf_binary_subset import AccountedBinarySubsetSolver
base=prior.base;bound=prior.bound;binding=prior.binding;native=prior.native;prep=prior.prep
PARENT=Path('experiments/results/cnf-affine-session')
MODES=('session','binary')
FILES=('experiments/cnf_binary_subset.py','experiments/compare_cnf_binary_subset.py','solver/test_cnf_binary_subset.py')
inherited=prior.inherited
exclusions=prior.exclusions
audit_records=prior.audit_records
summarize=prior.summarize


def worker(out,p,catalog,mode):
    if mode not in MODES:raise ValueError('Invalid binary-subset policy')
    if mode=='binary':
        with patch.object(prep.ordinary,'AccountedResidualSolver',AccountedBinarySubsetSolver):
            prior.worker(out,p,catalog,'session')
    else:prior.worker(out,p,catalog,'session')
    report=base.load(out/'report.json');report['summary']['mode']=mode
    base.write(out/'report.json',report)


def prepare(out):
    out.mkdir(exist_ok=False);parent=base.load(PARENT/'checkpoint.json')
    sources=dict(parent['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    base.write(out/'previous-decisions.json',exclusions(parent))
    p=copy.deepcopy(base.load(PARENT/'protocol.json'))
    p.update(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,
        previous_decisions=binding(out/'previous-decisions.json'),orders=[list(MODES),list(MODES[::-1])],
        limitations=[
            'Both arms use checked affine sessions and identical target-local discovery; only native residual expansion adds a sufficient binary-subset refutation test.',
            'No unit or pure-binary duplicate SCC work; uniform binary models filter impossible refutations. Satisfiable binary subsets are inconclusive. Failure preserves complete fallback.',
            'Native implication paths bind original clause indices; no new checker, proof format or authority. Every previous payload remains intact.',
            'Fresh sixty-query catalog excludes all inherited query/native roots. Family metadata never enters the solver. All lookup, misses, source scanning, checking, persistence, warm and full cold replay costs remain charged.',
            'Finite generated workloads do not establish broad runtime dominance, new tractability or a polynomial bound for unrestricted SAT.'])
    base.write(out/'protocol.json',p);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'initial';base.restore_archive(parent['reference_union'],path);s=native.ResidualSolver(path)
        try:catalog=prior.prior.inputs(s,p)
        finally:s.close()
    assert len(catalog['cases'])==60
    base.write(out/'cases.json',catalog);base.write(out/'generation.json',dict(seconds=time.perf_counter()-tick,selection=catalog['selection']))
    return p,catalog


def run(out):
    p=base.load(out/'protocol.json');catalog=base.load(out/'cases.json');samples=[]
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True)
            samples.append(dict(repeat=repeat,mode=mode,**binding(dest/'report.json')));print('fresh',repeat,mode,flush=True)
    summary={}
    for mode in MODES:
        data=[bound(e)['summary'] for e in samples if e['mode']==mode];first=data[0]
        timed=[k for k in first if k.endswith('_seconds') or k=='peak_rss_bytes']
        fixed=[k for k in first if k not in timed and k not in ('mode','sidecar_bytes')]
        for other in data[1:]:
            for k in fixed:assert first[k]==other[k],k
        summary[mode]={**{k:first[k] for k in fixed},**{'mean_'+k:sum(r[k] for r in data)/len(data) for k in timed},'sidecar_bytes':[r['sidecar_bytes'] for r in data]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    elif sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    else:run(Path(sys.argv[1]))
