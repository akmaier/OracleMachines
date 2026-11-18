#!/usr/bin/env python3
"""Compare cover-only, first partial backbone and frequency-gated reuse."""
from pathlib import Path
from unittest.mock import patch
import copy,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_clause_cover as prior
from experiments.cnf_binary_backbone import AccountedBinaryBackboneSolver,AccountedFrequencyBinaryBackboneSolver
base=prior.base;bound=prior.bound;binding=prior.binding;native=prior.native;prep=prior.prep
PARENT=Path('experiments/results/cnf-binary-clause-cover')
MODES=('cover','first','frequency')
FILES=('experiments/cnf_binary_backbone.py','experiments/compare_cnf_binary_backbone.py','solver/test_cnf_binary_backbone.py')
inputs=prior.inputs
OLD_FIELDS=prior.OLD_FIELDS
inherited=prior.inherited
exclusions=prior.exclusions
audit_records=prior.audit_records
summarize=prior.summarize


def worker(out,p,catalog,mode):
    if mode not in MODES:raise ValueError('Invalid backbone policy')
    if mode=='cover':prior.worker(out,p,catalog,'cover')
    else:
        cls=AccountedBinaryBackboneSolver if mode=='first' else AccountedFrequencyBinaryBackboneSolver
        with patch.object(prior,'AccountedBinaryClauseCoverSolver',cls):prior.worker(out,p,catalog,'cover')
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
            'Three policies share affine sessions and binary clause covers. First reuses the first successful path from an unresolved cover. Frequency admits it only when its variable matches the greatest-frequency/smallest-index split variable; this is a gate, not a guarantee of identical native control flow.',
            'No extra reachability queries beyond eight roots per residual. Whole covers keep priority. Reused evidence is source checked, only the surviving cofactor is searched, and a SAT lift avoids excluded-branch publication.',
            'A negative surviving cofactor causes direct path-to-unit compilation of the excluded branch, with no propagation search. Existing native split/unit proofs certify the parent. Compiled children remain charged separately from expansions.',
            'Both first-path and gated policies are retained, including regressions. Six workers run serially in opposite orders; family metadata never enters selection.',
            'All previous payloads survive; alternative models/proofs remain in trial archives. Discovery, ranking, transport, checking, storage, warm and full cold replay are included. No unrestricted-SAT resource bound.'])
    base.write(out/'protocol.json',p);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'initial';base.restore_archive(parent['reference_union'],path);s=native.ResidualSolver(path)
        try:catalog=inputs(s,p)
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
