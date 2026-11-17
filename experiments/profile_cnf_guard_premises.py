#!/usr/bin/env python3
"""Read-only check-cost probe: known strengthened premise before support proof.

Candidates are supplied by the completed historical study. This prices checking
only, not recognition, a deployed selector, or an end-to-end runtime comparison.
"""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_chain as study
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
base=study.base


def profile(out):
    tick=time.perf_counter();r=base.load(out/'report.json');p=bound(r['protocol']);hp=bound(p['historical_protocol']);authority=bound(hp['parent']);trial=bound(p['historical_trial']);records=bound(trial['queries'])
    indices={n:bound(hp[f]) for n,f in [('legacy','support_index'),('causal','causal_index')]};cores=indices['legacy']['cores']+indices['causal']['cores'];results=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final')
        for entry in r['samples']:
            data=bound(entry)
            if data['mode']!='chain' or data['choice'] is None:continue
            cid=data['case'];row=next(x for x in records if x['case']==cid and not x['visit']);chain=bound(data['chains'])[0]
            before=study.prefix_tools.prefix(initial,final,records,cid);pair={}
            for mode in ('core_then_premise','premise_only'):
                path=tmp/'arm';shutil.copyfile(tmp/'initial',path);s=AccountedResidualSolver(path)
                try:
                    study.prefix_tools.install(s,[(k,v) for k,v in before.items() if k not in initial])
                    _,_,target,_,_,_,_=study.prefix_tools.prepare(s,row['source'],hp,indices)
                    s.db.execute('PRAGMA query_only=ON');old=Counter(s.counts)
                    with patch.object(s,'_expand',side_effect=AssertionError('Fresh profile search')),patch.object(s,'_store',side_effect=AssertionError('Profile publication')):
                        if mode=='core_then_premise':
                            core=cores[data['choice']['core']];cnf,_,key=s._canonical(core['source']);assert key==core['root']
                            assert s._read(key,cnf)['answer'] is False
                        _,child=check_guard(s,target,chain['guards'][1])
                        assert s._canonical(child)[2]==chain['child']['root']
                    pair[mode]=dict(s.counts-old);assert study.rows(s)==before
                finally:s.close()
            results.append(dict(case=cid,counts=pair))
    totals={mode:{k:sum(x['counts'][mode].get(k,0) for x in results) for k in ('verified_nodes','verification_literal_payload','read_bytes')} for mode in ('core_then_premise','premise_only')}
    report=dict(report=study.binding(out/'report.json'),profiler=study.binding(__file__),cases=results,totals=totals,seconds=time.perf_counter()-tick,
        limitations=['Six already selected historical candidates. Both arms restore identical persistent prefixes and perform identical preparation; no proof publication or SAT search.',
            'Counts measure additional checking of core then strengthened premise versus the already-known strengthened premise alone. They do not measure candidate discovery, a new selector or end-to-end runtime.',
            'A checked UNSAT strengthened premise alone justifies the guard. An unverified core may suggest a clause but can never justify a verdict. Missing strengthened premises still require the ordinary checked-core/subset fallback.'])
    base.write(out/'premise-profile.json',report);print(base.encode(totals))


if __name__=='__main__':profile(Path(sys.argv[1]))
