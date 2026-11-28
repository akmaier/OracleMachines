"""Post-hoc proof-support census; it does not guide the frozen acquisition policy."""
from collections import Counter
from pathlib import Path
import sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_reuse_expansion as s

out = Path('experiments/results/cnf-reuse-expansion'); started = time.perf_counter()
p = s.load(out / 'protocol.json'); records = []
for row in s.source_rows(p):
    if not row['expansion_case']: continue
    base = s.e.canonical(row['source'], Counter()); n = len(base)
    names = sorted({abs(v) for c in base for v in c}); parent = {v: v for v in names}
    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]; v = parent[v]
        return v
    for clause in base:
        if clause:
            for literal in clause[1:]: parent[find(abs(literal))] = find(abs(clause[0]))
    entry = dict(id=row['id'], variables=len(names), clauses=n,
                 connected_components=len({find(v) for v in names}), modes={})
    for mode in s.POLICIES:
        report = s.load(out / (mode + '-0') / 'report.json')
        case = next(c for c in report['cases'] if c['id'] == row['id'])
        proof = s.load(out / (mode + '-0') / (row['id'] + '.json'))
        got = s.check(row['source'], proof); imported = case['diagnostic']['expansion'].get('reused', 0)
        detail = dict(status=case['status'], imported_derivations=imported, derivations=len(proof['derivations']))
        if got['answer'] is False:
            pending = [proof['conclusion']]; seen = set()
            while pending:
                index = pending.pop()
                if index in seen: continue
                seen.add(index)
                if index >= n:
                    start, steps, clause = proof['derivations'][index - n]
                    parents = [start, *[j for _, j in steps]]
                    assert all(0 <= j < index for j in parents)
                    pending.extend(parents)
            premises = sorted(i for i in seen if i < n)
            used_imports = sorted(i - n for i in seen if n <= i < n + imported)
            new_records = sorted(i - n for i in seen if i >= n + imported)
            detail.update(original_premises=premises, original_premise_count=len(premises),
                          used_imported_indices=used_imports, used_imported_count=len(used_imports),
                          used_new_indices=new_records, used_new_count=len(new_records),
                          supported_variables=len({abs(v) for i in premises for v in base[i]}))
        entry['modes'][mode] = detail
    records.append(entry)
s.write(out / 'support-census.json', dict(passed=True, records=records,
    seconds=time.perf_counter() - started,
    scope='Separately charged post-hoc traversal of each checked empty-clause proof. Counts are syntactically reachable records in the stored derivation, including proof ancestors; they are not minimal supports or clauses necessarily required by every proof. All source components and variables are counted from canonical inputs. Unknown results have no refutation support. This census changes neither timed policy nor retained evidence.'))
print(s.encode(dict(passed=True, targets=len(records), connected=sum(r['connected_components'] == 1 for r in records))))
