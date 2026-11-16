"""Retain checked clause supports from guarded UNSAT cofactors.

The bank recognizes restricted subproblems, not complete source queries. Source,
guard and child certificate must still be replayed together. No fresh solving
is permitted during preparation; derived nodes use the frozen proof format.
"""
from collections import Counter
from experiments.cnf_clause_deletion_guard import check_guard,clause_set
from experiments.cnf_unsat_support import SupportExtractor


def prepare(solver,catalogs):
    extractor=SupportExtractor(solver);counts=Counter();cores=[];identities={};origins=[]
    for catalog,records in catalogs:
        for record in records:
            if record['answer'] is not False or record['guard'] is None:continue
            cnf,_,query=solver._canonical(record['source'])
            if record['query_root']!=query:raise ValueError('Unbound complete query identity')
            assignment,target=check_guard(solver,record['source'],record['guard'],counts)
            normalized,_,child=solver._canonical(target)
            if (record['child']['root']!=child or record['child']['answer'] is not False
                    or record['child']['model'] is not None or record['model'] is not None):
                raise ValueError('Unbound negative cofactor')
            node=solver._read(child,normalized,purpose='cofactor_support')
            if node is None or node['answer'] is not False:raise ValueError('Missing checked negative cofactor')
            core=extractor.source_core(target);members=tuple(sorted(clause_set(core['source'],counts)))
            if members not in identities:
                identities[members]=len(cores);cores.append(dict(label=f'cofactor:{catalog}:{record["case"]}',**core))
            origins.append(dict(catalog=catalog,case=record['case'],query_root=query,child_root=child,core=identities[members]))
            counts['cofactor_sources']+=1
    members=[clause_set(c['source'],counts) for c in cores];retained=[];dominance={}
    for index in sorted(range(len(cores)),key=lambda i:(len(members[i]),sorted(members[i]))):
        witness=next((i for i in retained if members[i]<=members[index]),None)
        if witness is None:retained.append(index);witness=index
        dominance[index]=witness
    return dict(cores=[cores[i] for i in retained],all_cores=cores,retained_indices=retained,
        dominance=[dict(core=i,retained=dominance[i]) for i in range(len(cores))],origins=origins,
        counts=dict(counts),extraction_counts=dict(extractor.counts),
        limitation='Exact containment in common raw coordinates. Supports need not be minimal; no arbitrary variable-renaming search. A cofactor hit is not a complete-query certificate.')
