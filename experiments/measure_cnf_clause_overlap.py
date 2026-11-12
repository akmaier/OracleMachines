#!/usr/bin/env python3
"""Observe reusable immutable clauses and fixed-position blocks in cold checks."""
from collections import Counter, OrderedDict
import gzip
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_single_pass_check import reconstruct_single_pass
from experiments.compare_cnf_retained_plans import sha


class Observer:
    def __init__(self):
        self.counts=Counter();self.objects={};self.values=set();self.widths=Counter()
        self.cache=OrderedDict();self.units=0
        self.blocks={n:set() for n in (4,8,16)}

    def __call__(self,cnf,assigned,counts,*,units):
        result=reconstruct_single_pass(cnf,assigned,counts,units=units)
        assert type(cnf) is tuple and all(type(c) is tuple and all(type(l) is int and l for l in c) for c in cnf)
        self.counts['calls']+=1;self.counts['empty_assignments']+=not assigned
        support=set(assigned);mask=sum(1<<v for v in ())
        mask=0
        for v in support:mask|=1<<(v%64)
        for clause in cnf:
            self.counts['clause_positions']+=1;self.counts['literal_positions']+=len(clause)
            self.widths[len(clause)]+=1
            cid=id(clause);self.objects[cid]=clause;self.values.add(clause)
            weight=3+len(clause)
            if cid in self.cache:
                self.counts['fifo_clause_hits']+=1
            else:
                self.counts['fifo_clause_admissions']+=1
                self.counts['fifo_preparation_literals']+=len(clause)
                if weight<=32768:
                    while self.units+weight>32768:
                        _,old=self.cache.popitem(last=False);self.units-=old;self.counts['fifo_evictions']+=1
                    self.cache[cid]=weight;self.units+=weight
            affected=any(abs(lit) in support for lit in clause)
            self.counts['affected_clauses']+=affected
            self.counts['affected_literal_positions']+=len(clause) if affected else 0
            cmask=0
            for lit in clause:cmask|=1<<(abs(lit)%64)
            self.counts['mask_false_positive_clauses']+=bool(mask&cmask) and not affected
        for n,seen in self.blocks.items():
            for offset in range(0,len(cnf),n):
                block=tuple(id(c) for c in cnf[offset:offset+n])
                self.counts[f'block_{n}_positions']+=1
                self.counts[f'block_{n}_hits']+=block in seen;seen.add(block)
                if all(abs(lit) not in support for c in cnf[offset:offset+n] for lit in c):
                    self.counts[f'block_{n}_unaffected']+=1
        return result


def main(output):
    if output.exists():raise FileExistsError(output)
    source=Path('experiments/results/cnf-prepared-probes-full/report.json');r=json.loads(source.read_text());rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        seed=Path(tmp)/'seed.db'
        with gzip.open(r['seed']['path'],'rb') as src,seed.open('wb') as dst:shutil.copyfileobj(src,dst)
        assert sha(seed)==r['seed']['database_sha256']
        for i in (1194,1441):
            path=Path(tmp)/str(i);shutil.copyfile(seed,path);h=PreparedProbeInventory(path,**r['options']);observer=Observer()
            h._checked_reconstruction=observer;h.prepared._checked_reconstruction=observer
            result=h.inspect(r['cases'][i]['source']);h.close()
            rows.append(dict(case=i,group=r['cases'][i]['group'],counts=dict(observer.counts),
                unique_clause_identities=len(observer.objects),unique_clause_values=len(observer.values),
                clause_width_positions=dict(observer.widths),fifo_retained_units=observer.units,
                summary=result['summary']))
    output.parent.mkdir(parents=True,exist_ok=True)
    data=dict(input_report_sha256=sha(source),script_sha256=sha(Path(__file__)),rows=rows,
        limitations=['Observers retain unbounded identity/value sets and instrument every check; no runtime or memory benefit is inferred',
                     'Fixed-position blocks have unrestricted observer histories; FIFO clause simulation alone has a 32768 logical-slot cap',
                     'Two isolated sources, not the sequential full corpus or a new SAT coverage result'])
    output.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(rows))


if __name__=='__main__':main(Path(sys.argv[1]))
