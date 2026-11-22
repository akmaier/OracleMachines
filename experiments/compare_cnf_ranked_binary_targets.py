#!/usr/bin/env python3
"""Freeze bounded binary target policies before serial, prefix-controlled trials."""
from collections import Counter
from copy import deepcopy
from functools import partial
from pathlib import Path
from unittest.mock import patch
import random, sqlite3, subprocess, sys, tempfile, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probed_partition as previous
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_probed_partition import run as probed
from experiments.cnf_residual_dag import normalize,token,two_cnf
from experiments.probe_cnf_binary_structure import inspect

base=previous.base;binding=previous.binding;bound=previous.bound
TABLES=previous.TABLES;read_zip=previous.read_zip;write_zip=previous.write_zip
restore=previous.restore;tables=previous.tables
PARENT=Path('experiments/results/cnf-probed-partition')
MODES=('baseline','total4','binary1')
FILES=('experiments/cnf_ranked_binary_targets.py','experiments/compare_cnf_ranked_binary_targets.py','solver/test_cnf_ranked_binary_targets.py')


def prepare(out):
    out.mkdir();began=time.perf_counter();parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=deepcopy(bound(old['cases']));prefixes=deepcopy(old['prefixes']);branch=base.load(PARENT/'next-branch.json')
    data=bound(branch['trial_report']);delta=read_zip(data['delta']);seed=read_zip(branch['prefix'])
    selected=set(branch['extra_ids']);extra={t:[[k,v] for k,v in delta[t] if t==TABLES[0] and k in selected] for t in TABLES}
    assert len(extra[TABLES[0]])==5
    prefix={t:seed[t]+extra[t] for t in TABLES}
    assert all(branch['root'] not in dict(prefix[t]) for t in TABLES)
    prefixes['branch']=dict(archive=write_zip(out/'branch-prefix.json.gz',prefix),parent_prefix=branch['prefix'],extra_ids=branch['extra_ids'])
    cases.append(dict(case=31,split='branch',variant='isolated',source=branch['source'],root=branch['root']))
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'union';base.restore_archive(parent['reference_union'],path);con=sqlite3.connect(path)
        try:known={k for t in TABLES for k, in con.execute(f'SELECT id FROM {t}')}
        finally:con.close()
    # Two unselected neighbouring edits per supplied residual. Fixed seed,
    # no solver outcomes consulted; all roots must be absent from the old union.
    for index in previous.CASES:
        original=next(c for c in cases if (c['case'],c['split'],c['variant'])==(index,'fresh','delete'))
        rng=random.Random(202611222023+index)
        remove=rng.sample(range(len(original['source'])),2)
        for i,cid in enumerate(remove):
            source=[c for j,c in enumerate(original['source']) if j!=cid]
            added=None
            if i:
                added=sorted(v*(1 if rng.randrange(2) else -1) for v in rng.sample(original['candidate']['target_names'],3))
                assert added not in source;source.append(added)
            cnf,names=normalize(source);root=token(cnf,Counter());assert root not in known
            candidate=deepcopy(original['candidate']);candidate.update(target=[list(c) for c in cnf],target_names=list(names))
            cases.append(dict(case=index,split='novel',variant='delete' if i==0 else 'replace',source=previous.previous.target_source(candidate),
                root=root,candidate=candidate,deleted_clause=original['source'][cid],added_clause=added))
    assert len(cases)==16 and len({c['root'] for c in cases})==16
    for c in cases:
        key='branch' if c['split']=='branch' else str(c['case'])
        assert all(c['root'] not in dict(read_zip(prefixes[key]['archive'])[t]) for t in TABLES)
    cnf,_=normalize(branch['source']);diagnosis=inspect(cnf);checks=[]
    for lit in diagnosis['forced_literals']:
        model,proof=two_cnf([c for c in cnf if len(c)==2]+[(-lit,)],Counter())
        assert model is None;checks.append(dict(forced=lit,refutation=proof))
    base.write(out/'inspection.json',dict(branch=binding(PARENT/'next-branch.json'),binary=diagnosis,counterchecks=checks,
        original_target=targeted.inspect_targeted_backbone(cnf,Counter()),
        candidates={mode:discover(cnf,Counter(),policy=mode) for mode in MODES[1:]},
        limitations=['Unbounded read-only posthoc census; excluded from comparative query timing. Candidate policies chosen after this exposed branch.']))
    base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),
        cases=binding(out/'cases.json'),prefixes=prefixes,node_limit=256,orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},preparation_seconds=time.perf_counter()-began,
        limitations=[
        'Target ranking is selected using the exposed 61-expansion branch. Whole-cover discovery and native proof checking/compilation are unchanged. total4 checks four total-frequency variables; binary1 checks one binary-frequency variable. No outcome-based tuning after this protocol.',
        'Isolated branch seeds only the bound historical prefix and five publications before that branch. All other arms restore the preceding cold prefix. The final archive is used only to exclude fresh roots, never to seed trials.',
        'Nine earlier targets and one isolated branch are exposed controls. Six new edits are generated before solving and excluded from the earlier cumulative union. They remain local residual edits with supplied candidates/maps, not representative external or whole-source coverage.',
        'Except the native-only isolated-branch diagnostic, every arm uses the same probe6 partition wrapper and shared256 expansion limit. The general affine baseline remains unchanged; this comparison isolates the native discovery policy within that wrapper.',
        'The recognizer replacement is scoped with unittest.mock.patch inside one serial worker process. This is an experiment adapter, not a thread-safe solver API or a default-policy change.',
        'The inherited worker charges preparation, checking, serialization, persistence, complete prefix replay, reconstruction and warm lookup; query time excludes some of those costs. Complete time includes measurement/audit overhead. Prior acquisition remains sunk.',
        'More binary consequences do not guarantee cheaper branching; retain individual regressions. These existing implication rules prove no new SAT class, polynomial expansion guarantee or Lean refinement theorem.']))


def worker(out,p,split,index,mode):
    harness=previous.previous;query=harness.query
    def dispatch(s,c,unused,budget):
        return query(s,c,'native',budget) if split=='branch' else probed(s,c['candidate'],'probe6',budget)
    p=deepcopy(p)
    if split=='branch':p['prefixes'][str(index)]=p['prefixes']['branch']
    with patch.object(harness,'query',dispatch):
        if mode=='baseline':harness.worker(out,p,split,index,mode)
        else:
            with patch.object(targeted,'inspect_targeted_backbone',partial(discover,policy=mode)):
                harness.worker(out,p,split,index,mode)


def run(out):
    p=base.load(out/'protocol.json');cases=bound(p['cases']);samples=[]
    groups=list(dict.fromkeys((c['split'],c['case']) for c in cases))
    for split,index in groups:
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
