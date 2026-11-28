"""Retain rejected near models without changing the frozen timed search.

An instrumented copy records strict improvements only. Counts and final output
must match the uninstrumented saved run. These rejected models carry no authority.
"""
from collections import Counter
from pathlib import Path
import hashlib,inspect,json
from experiments import cnf_partition_repair as e


def main(out):
    out=Path(out);panel=json.loads(Path('experiments/results/cnf-hamming-repair/constructed-inputs.json').read_text());report=json.loads((out/'partition-0/report.json').read_text())
    text=inspect.getsource(e.search)
    target="        maximum_kept = max(maximum_kept, kept.bit_count())"
    insert="""        if len(bad) < _trace_best[0]:
            _trace_best[0] = len(bad)
            _snapshots.append(dict(expanded=expanded, flipped=str(mask), kept=str(kept),
                                   values=[model[v] for v in names], false_canonical=sorted(bad)))
"""
    assert text.count(target)==1
    instrumented=text.replace(target,insert+target);(out/'instrumented_search.py.txt').write_text(instrumented)
    namespace={**vars(e),'_trace_best':[float('inf')],'_snapshots':[]};exec(compile(instrumented,'instrumented_search','exec'),namespace)
    records=[]
    for row,case in zip(panel,report['cases']):
        if case['status']!='unresolved':continue
        namespace['_trace_best']=[float('inf')];namespace['_snapshots']=[];counts=Counter();seed=e.proposal(row['source'],counts)
        result=namespace['search'](row['source'],seed,len(seed['names']),counts)
        assert result==case['diagnostic']['search'] and dict(counts)==case['discovery_counts']
        canonical=e.previous.capacity.canonical(row['source'],Counter())
        for snapshot in namespace['_snapshots']:
            model=dict(zip(seed['names'],snapshot['values']));mask=int(snapshot['flipped']);kept=int(snapshot['kept']);assert not mask&kept
            assert snapshot['values']==[v ^ bool(mask & (1<<j)) for j,v in enumerate(seed['values'])]
            assert snapshot['false_canonical']==[i for i,c in enumerate(canonical) if not any(model[abs(v)]==(v>0) for v in c)]
            snapshot['false_original']=[i for i,c in enumerate(row['source']) if not any(model[abs(v)]==(v>0) for v in c)]
            assert snapshot['false_original']
        records.append(dict(id=row['id'],source=row['source'],seed=seed,snapshots=namespace['_snapshots']))
    value=dict(passed=True,records=records,source_sha256=hashlib.sha256(Path(e.__file__).read_bytes()).hexdigest(),scope='Rejected near models from a trace-only copy; identical final outputs and counters verified against timed search. Canonical and original false-clause indices are checked independently. No SAT certificate or resumable frontier claim.')
    (out/'near-models.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(passed=True,remaining=[dict(id=r['id'],best_false=len(r['snapshots'][-1]['false_original'])) for r in records])))


if __name__=='__main__':
    import sys
    main(sys.argv[1])
