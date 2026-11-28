"""Describe every unresolved interaction without assigning a structural label."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_boundary_transfer as s


def main(out):
    diagnostics={r['id']:r for r in s.load(out/'gap-diagnostics.json')['records']};records=[]
    for row in s.load(out/'remaining.json')['records']:
        source=row['source'];names=sorted({abs(v) for c in source for v in c});graph={v:set() for v in names}
        for c in source:
            support={abs(v) for v in c}
            for v in support:graph[v].update(support-{v})
        seen=set();components=[]
        for v in names:
            if v in seen:continue
            pending=[v];group=set()
            while pending:
                w=pending.pop()
                if w in seen:continue
                seen.add(w);group.add(w);pending.extend(graph[w]-seen)
            components.append(len(group))
        diag=diagnostics[row['id']];model=dict(zip(diag['near_model']['names'],diag['near_model']['values']))
        bad=[i for i,c in enumerate(source) if not any(model[abs(v)]==(v>0) for v in c)]
        assert len(bad)==diag['diagnostic']['prefix']['best_failed']
        records.append(dict(id=row['id'],variables=len(names),clauses=len(source),clause_widths=dict(Counter(map(len,source))),component_sizes=components,near_false_indices=bad,final_free_variables=diag['diagnostic']['rounds'][-1]['selected_variables'],reference_answer=row['reference_answer']))
    s.write(out/'interaction-audit.json',dict(records=records,remaining=len(records),scope='Primal connected components and observed free-set width only; not minimum width, semantic irreducibility or efficient structural classification. Rejected near models remain non-certificates.'))
    print(s.encode(records))


if __name__=='__main__':main(Path(sys.argv[1]))
