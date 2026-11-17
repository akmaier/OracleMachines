#!/usr/bin/env python3
"""Historical admission/rejection controls using the exact earlier prefixes."""
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import probe_cnf_pending_guards as old
from experiments.cnf_terminal_guard import TerminalGuardSelector
from experiments.cnf_proof_choice import ProofChoiceBank,compose,audit_portfolio
from experiments.cnf_clause_deletion_guard import ExtensionBank,check_guard
from experiments.validate_cnf_unsat_support import bound
study=old.study;base=study.base


def check(out):
    tick=time.perf_counter();p=base.load(old.PARENT/'protocol.json');authority=bound(p['parent'])
    trial=base.load(old.PARENT/'alternative-0/report.json');records=bound(trial['queries'])
    bindings=dict(legacy=p['support_index'],causal=p['causal_index']);indices={n:bound(e) for n,e in bindings.items()}
    prepared=compose(indices,bindings);catalogs=[(n,bound(e)) for n,e in zip(study.OLD_FIELDS,p['prior_decision_catalogs'])];controls=[]
    parent=base.load(out/'protocol.json');latest=bound(parent['parent'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');retained=read(latest['reference_union'],'latest')
        for cid in (23,85,103):
            before=old.prefix(initial,final,records,cid);row=next(r for r in records if r['case']==cid and not r['visit'])
            path=tmp/f'case-{cid}';shutil.copyfile(tmp/'initial',path);s=study.AccountedResidualSolver(path)
            try:
                old.install(s,[(k,v) for k,v in before.items() if k not in initial]);assert study.rows(s)==before
                bank=ProofChoiceBank(s,indices['legacy'],indices['causal']);extensions=ExtensionBank(bound(p['bank_catalog'])['bank'])
                selector=TerminalGuardSelector();query=[]
                with patch.object(s,'_expand',side_effect=AssertionError('Fresh control search')):
                    chosen,trace=selector.select(s,extensions,row['source'],row['guard'],bank)
                    if cid==85:
                        assert chosen==row['guard_choice']['attempts'][0]['guard'] and trace['attempts'][0]['status']=='terminal'
                        assert len(study.rows(s))-len(before)==1
                        _,target=check_guard(s,row['source'],chosen);hit=bank.reuse(target);assert hit['choice']=='ready'
                        child=s.solve(target);assert not child['answer'] and not child['metrics'].get('expanded_nodes',0)
                        query=[dict(case=cid,source=row['source'],guard=chosen,witness=None,child=child,answer=False,model=None)]
                        assert len(study.rows(s))-len(before)==2
                    else:assert chosen is None and study.rows(s)==before
                saved=study.rows(s);delta=[(k,v) for k,v in saved.items() if k not in before]
                assert all(retained[k]==v for k,v in delta)
            finally:s.close()
            dest=out/f'control-{cid}';dest.mkdir();base.write(dest/'delta.json',delta);base.write(dest/'queries.json',query)
            cold=audit_portfolio(path,query,prepared,catalogs,indices)
            controls.append(dict(case=cid,selected=chosen is not None,new_nodes=len(delta),trace=trace,counts=dict(selector.counts),
                delta=study.binding(dest/'delta.json'),queries=study.binding(dest/'queries.json'),cold=cold,already_retained=True))
    result=dict(passed=True,checker=study.binding(__file__),original_protocol=study.binding(old.PARENT/'protocol.json'),original_queries=trial['queries'],
        source_archive=authority['reference_union'],prefix_rule='Only original appended rows strictly before the selected first visit',controls=controls,seconds=time.perf_counter()-tick,
        limitation='Historical admission/rejection controls with fresh search disabled. Case 85 proves the integrated selector is exercised; cases 23/103 reject recursive origins. All resulting payloads were already retained by the preceding diagnostic union; no new coverage or matched speedup claim.')
    base.write(out/'controls.json',result);print(base.encode(dict(passed=True,cases=[(r['case'],r['selected'],r['new_nodes']) for r in controls])))


if __name__=='__main__':check(Path(sys.argv[1]))
