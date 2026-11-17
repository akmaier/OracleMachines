#!/usr/bin/env python3
"""Untimed parity check against the frozen ordinary query worker."""
from pathlib import Path
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_premise_guard as study
from experiments.validate_cnf_unsat_support import bound
base=study.base


def check(out):
    started=time.perf_counter();p=base.load(out/'protocol.json');catalog=base.load(out/'cases.json');target=base.load(out/'plain-0/report.json');rows=bound(target['queries'])
    settings=copy.deepcopy(p);settings['visits']=2;dest=out/'frozen-control'
    study.ordinary.worker(dest,settings,catalog,'alternative');frozen=base.load(dest/'report.json');queries=bound(frozen['queries'])
    assert len(queries)==2*len(rows)
    for current,old in zip(rows,queries[:len(rows)]):
        normal=current['ordinary'];assert current['case']==old['case'] and current['chain']['source']==old['source']
        for field in ('guard','core','witness','guard_choice','cofactor','target_known'):assert normal[field]==old[field],(old['case'],field)
        assert current['chain']['answer']==old['answer'];assert current['chain']['model']==old['model']
        assert current['chain']['child']=={k:old['child'][k] for k in ('root','answer','model')}
        assert current['new_ids']==old['new_ids'] and current['child_metrics'].get('expanded_nodes',0)==old['child']['metrics'].get('expanded_nodes',0)
    with tempfile.TemporaryDirectory() as td:
        results=[]
        for name,archive in [('new',target['archive']),('old',frozen['archive'])]:
            path=Path(td)/name;base.restore_archive(archive,path);s=study.ResidualSolver(path)
            try:results.append(study.rows(s))
            finally:s.close()
        assert results[0]==results[1]
    result=dict(passed=True,checker=study.binding(__file__),frozen_report=study.binding(dest/'report.json'),plain_report=study.binding(out/'plain-0/report.json'),
        first_queries=len(rows),repeat_queries=len(rows),identical_native_payloads=len(results[0]),seconds=time.perf_counter()-started,
        limitations=['Untimed independent frozen-worker execution. Same first-query guards, witnesses, cofactors, answers, children, expansion counts and new roots; final native payloads identical.',
            'The symmetric new worker persists checked chains and uses a checked conclusion bank for repeats. Frozen worker repeats its original query pipeline. Timings are not compared between these interfaces.'])
    base.write(out/'parity-check.json',result);print(base.encode({k:result[k] for k in ('passed','first_queries','identical_native_payloads','seconds')}),flush=True)


if __name__=='__main__':check(Path(sys.argv[1]))
