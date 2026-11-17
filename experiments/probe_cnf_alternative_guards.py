#!/usr/bin/env python3
"""Read-only diagnosis of alternative guards on the measured unresolved queries.

Use only the pre-query union and acquired banks. Ready subset proofs are checked;
pending matches are hints only. This is not a timed search-policy comparison.
"""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_causal as study
from experiments.cnf_clause_deletion_guard import ExtensionBank,check_guard,clause_set,lift
from experiments.validate_cnf_unsat_support import bound
base=study.base


def probe(out):
    start=time.perf_counter();report=base.load(out/'report.json');protocol=bound(report['protocol']);data=base.load(out/'extended-0/report.json')
    queries=bound(data['queries']);parent=bound(protocol['parent']);old=bound(protocol['support_index']);causal=bound(data['causal_index']);counts=Counter()
    cores=[(name,i,c,clause_set(c['source'],counts)) for name,bank in [('legacy',old),('causal',causal)] for i,c in enumerate(bank['cores'])]
    extension=ExtensionBank(bound(protocol['bank_catalog'])['bank'],counts);records=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'initial';base.restore_archive(parent['reference_union'],path);before=base.sha(path);s=study.ResidualSolver(path)
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Fresh diagnostic search')),patch.object(s,'_store',side_effect=AssertionError('Diagnostic publication')):
                for row in queries:
                    if row['visit'] or not row['child']['metrics'].get('expanded_nodes',0):continue
                    alternatives=[];current_guard=row['guard'];current_members=clause_set(row['target'],counts)
                    # An empty-clause core is distance one from every nonempty
                    # target. Require overlap so this diagnostic is not vacuous.
                    comparable=[item for item in cores if item[3]&current_members]
                    distance=min((len(wanted-current_members) for _,_,_,wanted in comparable),default=None)
                    nearest_ready=None
                    for name,i,c,wanted in sorted(comparable,key=lambda item:len(item[3]-current_members)):
                        small,_,root=s._canonical(c['source']);assert root==c['root'];proof=s._read(root,small,purpose='probe_nearest')
                        if proof is None:continue
                        assert proof['answer'] is False
                        nearest_ready=dict(bank=name,index=i,clauses=len(wanted),shared_clauses=len(wanted&current_members),missing_clauses=[list(c) for c in sorted(wanted-current_members)])
                        break
                    for guard in extension.candidates(row['source'],counts):
                        cnf,_,key=s._canonical(guard['stronger']);node=s._read(key,cnf,purpose='probe_guard')
                        if node is None or node['answer'] is not False:continue
                        fixed,target=check_guard(s,row['source'],guard,counts);cnf,_,key=s._canonical(target);node=s._read(key,cnf,purpose='probe_target')
                        ready=None;pending=[];members=clause_set(target,counts)
                        if node is None:
                            for name,i,c,wanted in cores:
                                counts['support_candidates']+=1;counts['support_containment_clauses']+=len(wanted)
                                if not wanted<=members:continue
                                small,_,root=s._canonical(c['source']);assert root==c['root'];proof=s._read(root,small,purpose='probe_support')
                                if proof is None:pending.append(dict(bank=name,index=i));continue
                                assert proof['answer'] is False;ready=dict(bank=name,index=i);break
                        elif node['answer']:
                            # _read returns a canonical witness; transport it to source coordinates.
                            _,names,_=s._canonical(target);model=dict(zip(names,node['model']));lift(row['source'],fixed,model)
                        available=node is not None or ready is not None
                        if available:assert (node['answer'] if node is not None else False)==row['answer']
                        alternatives.append(dict(guard=guard,same_guard=guard==current_guard,target_root_sha256=base.key_sha(key),known_answer=None if node is None else node['answer'],
                            checked_ready_support=ready,pending_hints=pending,available_without_search=available))
                    records.append(dict(case=row['case'],answer=row['answer'],baseline_expansions=row['child']['metrics']['expanded_nodes'],
                        minimum_missing_support_clauses=distance,nearest_checked_ready_support=nearest_ready,alternatives=alternatives))
        finally:s.close()
        assert base.sha(path)==before
    available=[r for r in records if any(a['available_without_search'] and not a['same_guard'] for a in r['alternatives'])]
    result=dict(protocol=report['protocol'],study_report=study.binding(out/'report.json'),probe=study.binding(__file__),initial_union=parent['reference_union'],causal_index=data['causal_index'],
        records=records,counts=dict(counts),seconds=time.perf_counter()-start,read_only=True,no_fresh_search=True,
        alternative_ready_cases=[r['case'] for r in available],potential_avoided_expansions=sum(r['baseline_expansions'] for r in available),
        limitations=['Only unresolved measured queries are probed after timing. All reads use the initial pre-query archive; the acquired causal bank derives only from earlier source records.',
            'Known roots and contained ready negative proofs are checked. Pending matches are unproved hints. Candidate search, extra checking and publication costs require a separate matched experiment.',
            'Distance diagnostics require at least one shared clause; otherwise an empty-clause core gives the vacuous distance one to every nonempty target. Missing clauses never justify UNSAT.',
            'No newly published target proof, optimal guard choice or universal expansion bound is claimed.'])
    base.write(out/'alternative-guards.json',result)
    print(base.encode(dict(alternative_ready_cases=result['alternative_ready_cases'],potential_avoided_expansions=result['potential_avoided_expansions'],
        cases=[dict(case=r['case'],answer=r['answer'],expansions=r['baseline_expansions'],guards=len(r['alternatives']),minimum_missing=r['minimum_missing_support_clauses']) for r in records],seconds=result['seconds'])))


if __name__=='__main__':probe(Path(sys.argv[1]))
