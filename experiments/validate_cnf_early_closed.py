#!/usr/bin/env python3
"""Cold-check both policy arms and the combined resumable discovery checkpoint."""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_early_closed import (restore_checkpoint,restore_base,restore_control,
    BASE,CONTROL,routes_for,add_splits,select,BudgetedInventory,full,verify_split,
    verify_positive,read_archive,sha,sha_key,unpack,apply_delta,check_delta,digests)


def validate(out):
    tick=time.perf_counter();expected=json.loads((out/'report.json').read_text());result=dict(arms=[])
    for path,digest in expected['fingerprints'].items():assert sha(path)==digest
    for arm in expected['arms']:assert sha(arm['path'])==arm['sha256']
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('new recognition')):
        tmp=Path(td);started=time.perf_counter()
        r,*evidence=restore_checkpoint(out/'report.json',tmp/'final',tmp)
        assert r==expected
        result['reconstruction']=dict(seconds=time.perf_counter()-started,covered=sum(r['final_closed']),
            evidence_counts=list(map(len,evidence)),report_sha256=sha(out/'report.json'))
        print('Combined checkpoint independently restored',flush=True)
        for case,base,restore in ((1445,BASE,restore_base),(1189,CONTROL,restore_control)):
            ct=tmp/str(case);ct.mkdir();seed=ct/'seed';parent,*original=restore(base,seed,ct)
            before=sha(seed);target=read_archive(parent['frontier'])['leaves'][0]['source']
            for bound in (a for a in r['arms'] if a['case']==case):
                ar=json.loads(Path(bound['path']).read_text());assert ar['root_sha256']==sha_key(target)
                history=ct/bound['mode'];shutil.copyfile(seed,history)
                d=ar['delta'];assert sha(d['path'])==d['sha256'];delta=ct/(bound['mode']+'-delta')
                unpack(d['path'],delta,d['database_sha256']);apply_delta(history,delta);check_delta(history,delta,r['options'])
                old=sha(history);apply_delta(history,delta);assert sha(history)==old
                splits=read_archive(ar['splits']);ev=add_splits(original,splits)
                h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
                try:
                    routes=routes_for(h,ev);closed,_,_=full(h,[target],routes)
                    assert closed==[[ar['target_closed']],[ar['without_growth_closed']]]
                    for record in splits:verify_split(h,record,Counter())
                    verify_positive(h,read_archive(ar['expanded_certificate']),[target] if closed[0][0] else [],ev,Counter())
                    next_selection=None if closed[0][0] else select(h,routes,[*ev[:3],splits,ev[4]],[target],[False],Counter())
                    assert next_selection==read_archive(ar['next_selection'])
                    admitted=set(ar['admitted_state_sha256'])
                    assert len(admitted)<=32 and sum(x['admitted_now'] for x in ar['steps'])==len(admitted)
                    added=set()
                    for row in ar['steps']:
                        operation=read_archive(row['operation']);ids=set(map(sha_key,operation['added']))
                        assert not added&ids;added.update(ids)
                        if operation.get('record') is not None:
                            verify_split(h,operation['record'],Counter())
                            assert len(operation['acquisition']['branches'])==2
                    assert added==admitted and not h.admitted
                finally:h.close()
                result['arms'].append(dict(case=case,mode=bound['mode'],closed=closed[0][0],
                    admitted=len(admitted),cold_frontier_matches=True,idempotent=True))
                print(json.dumps(result['arms'][-1]),flush=True)
            assert sha(seed)==before
        assert digests(tmp/'final')==r['logical_table_digests']
    result.update(seconds=time.perf_counter()-tick,report_sha256=sha(out/'report.json'),passed=True)
    (out/'reconstruction.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True,seconds=result['seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);validate(p.parse_args().output)
