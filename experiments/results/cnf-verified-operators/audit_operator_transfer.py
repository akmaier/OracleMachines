"""Audit generator-family transfer of exact checked operators, excluding repeats."""
from collections import Counter
from pathlib import Path
import runpy,time
from experiments import compare_cnf_verified_operators as s
base=s.base;k=s.k;old=s.old;out=Path(__file__).parent


def main():
    start=time.perf_counter();events=runpy.run_path(str(s.PARENT/'profile_check_reuse.py'))['events']
    rows=base.load(out/'panel.json');desc=base.load(out/'descriptions.json');report=base.load(out/'pass-0/report.json')
    seen={};roots=set();counts=Counter();pairs=Counter();records=[];bank=s.verified.VerifiedOperators()
    for row,result in zip(rows,report['results']):
        proof=base.load(out/'pass-0'/report['stored'][result['root']]);k.check_certificate(row['source'],proof)
        description=desc[row['id']]
        while 'previous' in description:description=description['previous']
        family=description['family'];fresh=result['root'] not in roots;roots.add(result['root']);local=set();cc=Counter()
        cc['unique_source' if fresh else 'repeated_source']+=1
        for program,_ in events(proof):
            if any(len(c)>program['limits']['bag_limit'] for c in program['cnf']):continue
            factors=[k.bucket.leaf(c) for c in program['cnf']]
            for step in program['steps']:
                inputs=[factors[i] for i in step['inputs']];key=bank._key(inputs,step['variable'],program['reduce'],step['scope'],step['bits'],step['choices'],Counter())
                width=len({x for f in inputs for x in f['scope']});rows_here=1<<(width-1);probes=2*rows_here*len(inputs)
                cc['operator_occurrences']+=1;cc['original_probes']+=probes
                if key in seen:
                    cc['hit_probes']+=probes;cc['hits']+=1
                    origin=seen[key]
                    if fresh and key not in local:
                        cc['distinct_source_match_probes']+=probes
                        if origin['family']!=family:
                            kind='nonconstant' if step['scope'] else 'constant';cc['cross_family_'+kind+'_probes']+=probes;cc['cross_family_'+kind+'_rows']+=rows_here;cc['cross_family_'+kind+'_operators']+=1;pairs[(origin['family'],family,kind)]+=probes
                else:seen[key]=dict(id=row['id'],family=family)
                local.add(key);factors.append(dict(scope=step['scope'],bits=step['bits']))
        counts.update(cc);records.append(dict(id=row['id'],family=family,counts=dict(cc)))
    assert len(seen)==1325 and counts['hit_probes']*2==report['cold_counts']['verified_operator_saved_probes']
    base.write(out/'transfer-audit.json',dict(passed=True,counts=dict(counts),distinct_operators=len(seen),family_pairs=[dict(source=a,target=b,kind=c,probes=n) for (a,b,c),n in sorted(pairs.items())],records=records,seconds=time.perf_counter()-start,scope='Post-hoc labels never enter recognition. Cross-family counts use the first owner of each exact checked signature and only first local occurrences in first occurrences of normalized sources. Families are generator labels, not disjoint semantic SAT classes. This counts local nonconstant operators, not shared whole residuals or unrestricted transfer.'))
    print(dict(counts))


if __name__=='__main__':main()
