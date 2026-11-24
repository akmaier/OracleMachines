#!/usr/bin/env python3
"""Follow the frozen census with all discovered contradictory local contexts."""
from collections import Counter
from pathlib import Path
import json,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_guard_interactions as study
from experiments.cnf_guard_interactions import binary_paths,compile_path
from experiments.cnf_guard_probe_census import decode_key
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_archive_parts import restore_archive
from experiments import cnf_residual_dag as native
base=study.base;old=study.old


def run(out):
    study_report=base.load(out/'report.json');p=base.load(out/'protocol.json');chosen=[]
    for binding in study_report['targets']:
        r=old.bound(binding)
        for row in old.bound(r['records']):
            if row['analysis']['profiles']['combined']['contradictory']:
                chosen.append(dict(target=r['target'],event=row['event']))
    protocol=dict(study=old.binding(out/'report.json'),source=old.binding(Path(__file__)),chosen=chosen,
        selection='All contradictory combined binary graphs found in the completed census, without further filtering; adaptive diagnostic on exposed contexts.',
        path_limit=p['path_limit'],node_limit=p['baseline_node_limit'],
        limitations=['One cold pair per local CNF, with empty native stores and provisioned checked guard supports. Earlier discovery/transport and all persistence costs are additional.',
            'Compare original binary plus unit guards with the full width-two consequence fragment. A guard-only contradiction need not require a binary guard.',
            'Compile both polarities of the smallest contradictory variable, then use the existing native split rule. This is a local CNF refutation, not an automatic verdict on its originating whole query.'])
    base.write(out/'closure-protocol.json',protocol);began=time.perf_counter();rows=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);bankpath=temp/'bank';bank=native.ResidualSolver(bankpath)
        try:
            for binding in study_report['targets']:
                r=old.bound(binding);parent=old.bound(r['input']);path=temp/'parent'
                restore_archive(parent['archives']['native'],path);reference=native.ResidualSolver(path)
                try:
                    for row in old.bound(r['records']):
                        combined=row['analysis']['profiles']['combined'];contradictory=combined['contradictory']
                        if not contradictory:continue
                        local=decode_key(row['root']);hints=row['hints'];v=min(contradictory)
                        profile={**combined,'paths':{int(k):p for k,p in combined['paths'].items()}}
                        units=binary_paths(list(row['analysis']['profiles']['original']['clauses'])+[h['clause'] for h in hints if len(h['clause'])<=1],Counter())
                        oldnode=reference._read(row['root']);assert oldnode is None or oldnode['answer'] is False
                        pair={}
                        for mode in ('compile','fresh') if len(rows)%2==0 else ('fresh','compile'):
                            tick=time.perf_counter();s=native.ResidualSolver() if mode=='compile' else LazyBinaryClosureSolver(node_limit=protocol['node_limit']);c=Counter()
                            try:
                                if mode=='compile':
                                    low=compile_path(s,local,hints,profile,v,c,path_limit=protocol['path_limit'])
                                    high=compile_path(s,local,hints,profile,-v,c,path_limit=protocol['path_limit'])
                                    s._store(row['root'],dict(format=native.FORMAT,cnf=[list(cl) for cl in local],answer=False,
                                        proof=dict(kind='split',variable=v,low=low,high=high)))
                                    root=row['root'];status='unsat'
                                else:
                                    result=attempt(s,local);assert result['status'] in ('unsat','unresolved')
                                    status=result['status'];root=None if result['result'] is None else result['result']['root']
                                elapsed=time.perf_counter()-tick
                                saved=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY rowid'))
                                pair[mode]=dict(status=status,root=root,seconds=elapsed,nodes=len(saved),
                                    native_counts=dict(s.counts),composition_counts=dict(c),
                                    payload_bytes=sum(len(k.encode())+len(payload.encode()) for k,payload in saved))
                                for key,payload in saved:bank._store(key,json.loads(payload))
                            finally:s.close()
                        if pair['fresh']['root'] is not None:assert pair['fresh']['root']==row['root']
                        rows.append(dict(target=r['target'],event=row['event'],root=row['root'],variable=v,
                            needs_binary_guard=not (units['contradictory'] or units['empty']),
                            present_after_native_query=oldnode is not None,comparison=pair))
                finally:reference.close();path.unlink()
                print('closed target',r['target'],flush=True)
        finally:bank.close()
        (out/'closures').mkdir();archive=base.archive(bankpath,out/'closures')
    base.write(out/'closures.json',dict(protocol=old.binding(out/'closure-protocol.json'),records=rows,archive=archive,
        complete_seconds=time.perf_counter()-began))


if __name__=='__main__':run(Path(sys.argv[1]))
