#!/usr/bin/env python3
"""Check current-context rejection, counts and source history on general chains.

This is a mechanism diagnostic, not an elapsed-time comparison with the old code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from solver.persistent import PersistentSolver,DEFAULT_ENGINE
from solver.test_interfaces import chain,var,neg


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Choose a new diagnostic output')
    rows=[]
    for length in (16,64,128):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',interfaces=True,query_timeout=60) as service:
            result=service.expand(add={'chain':chain(length),'start':var(0),'end':neg(var(length))})
            assert result['answer'] is False and result['fallback_reason'] is None
            evidence_id=service.db.execute('SELECT evidence FROM expansion_states WHERE id=?',(result['state'],)).fetchone()[0]
            evidence=service.interfaces.store.get(evidence_id,'expansion_result')
            leaves=[x['id'] for x in evidence['certificate']['definitions'] if x['definition']['kind']=='leaf']
            assert len(set(leaves))==len(leaves)
            probes=[]
            for repeats,deleted in ((1,False),(3,False),(3,True)):
                active=(leaves[1:] if deleted else leaves)*repeats
                random.Random(1832+length).shuffle(active)
                checked=service._request(dict(mode='factor_query',answer=False,root=evidence['root'],active=active))
                assert checked['valid']==(not deleted)
                assert checked['context_index_entries']==len(active)
                assert checked['context_membership_probes']<=len(leaves)
                if not deleted:assert checked['context_membership_probes']==len(leaves)
                probes.append(dict(repeats=repeats,deleted_assumption=deleted,**checked))
            removed=service.expand(result['state'],remove=['end'])
            assert removed['answer'] is True
            branch=service.expand(result['state'])
            assert branch['answer'] is False
            rows.append(dict(edges=length,proof_leaves=len(leaves),
                old_unique_list_comparisons_calculated=len(leaves)*(len(leaves)+1)//2,
                initial_metrics=result['interfaces'],context_checks=probes,
                after_deletion=removed['answer'],old_branch=branch['answer']))
    paths=[Path(__file__),ROOT/'experiments/preserve_source_results.py',DEFAULT_ENGINE,
        ROOT/'formal/OracleMachines/InterfaceProtocol.lean',ROOT/'formal/Solver.lean',
        ROOT/'solver/interfaces.py',ROOT/'solver/persistent.py',ROOT/'solver/source_updates.py']
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},rows=rows,
        scope='Indexed context request counts; full DAG traversal and hash operation costs remain separate.')
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([dict(edges=r['edges'],proof_leaves=r['proof_leaves'],checks=r['context_checks']) for r in rows]))


if __name__=='__main__':main()
