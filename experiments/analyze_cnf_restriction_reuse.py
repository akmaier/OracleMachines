#!/usr/bin/env python3
"""Observe exact source reuse and affected clauses; diagnostic timings excluded."""
from collections import Counter, OrderedDict
import hashlib
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_ordered_propagation_inventory import OrderedPropagationInventory
from experiments.cnf_residual_dag import restrict


def main(output):
    output.mkdir(parents=True,exist_ok=False)
    input_path=Path('experiments/results/cnf-ordered-propagation/report.json')
    report=json.loads(input_path.read_text())
    indices=[858,875,907,970,1042,1061,1194,977,1044,1185,1289,1368]
    rows=[]
    for i in indices:
        totals=Counter();callers=Counter();sources={};objects={};results=set();cache=OrderedDict()
        used=0;limit=32768
        def profile(frame,event,arg):
            nonlocal used
            if event!='call' or frame.f_code is not restrict.__code__:return
            cnf=frame.f_locals['cnf'];assignment=frame.f_locals['assignment']
            key=tuple(tuple(c) for c in cnf);fixed=tuple(sorted(assignment.items()))
            totals['calls']+=1;callers[frame.f_back.f_code.co_name]+=1
            literals=sum(map(len,key));totals['input_literals']+=literals
            totals['input_clauses']+=len(key);totals['assignment_entries']+=len(fixed)
            totals['empty_assignment_calls']+=not fixed
            immutable=type(cnf) is tuple and all(type(c) is tuple for c in cnf)
            totals['immutable_calls' if immutable else 'mutable_calls']+=1
            if id(cnf) in objects:totals['same_object_calls']+=1
            else:objects[id(cnf)]=cnf
            if (key,fixed) in results:totals['repeated_exact_restrictions']+=1
            results.add((key,fixed))
            if key not in sources:
                postings={}
                for cid,c in enumerate(key):
                    for lit in c:postings.setdefault(abs(lit),set()).add(cid)
                sources[key]=postings
            affected=set()
            for v in assignment:affected.update(sources[key].get(v,()))
            totals['affected_clauses']+=len(affected)
            totals['affected_literals']+=sum(len(key[cid]) for cid in affected)
            if key in cache:
                totals['source_cache_hits']+=1;cache.move_to_end(key)
            else:
                totals['source_cache_misses']+=1
                weight=1+len(key)+literals
                if weight<=limit:
                    while used+weight>limit:
                        _,old=cache.popitem(last=False);used-=old
                        totals['source_cache_evictions']+=1
                    cache[key]=weight;used+=weight
                    totals['source_cache_preparation_literals']+=literals
        with tempfile.TemporaryDirectory() as tmp:
            h=OrderedPropagationInventory(Path(tmp)/'history.db',max_depth=2,probe_limit=4,learn_limit=4)
            sys.setprofile(profile)
            try:discovery=h.inspect(report['cases'][i]['source'])
            finally:sys.setprofile(None)
            h.close()
        rows.append(dict(case=i,summary=discovery['summary'],totals=dict(totals),callers=dict(callers),
                         distinct_sources=len(sources),distinct_objects=len(objects),
                         distinct_exact_restrictions=len(results)))
    result=dict(rows=rows,indices=indices,source_cache_unit_limit=32768,
        input_report_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limitations=['Instrumented acquisition only; source objects retained to avoid id reuse during analysis',
            'No timing or memory comparison: this diagnostic itself changes overhead and lifetime',
            'Affected-literal estimate still requires output assembly, source lookup, index construction and checking',
            'Cache units count one source plus clauses plus literal occurrences, not physical bytes'])
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main(Path(sys.argv[1]))
