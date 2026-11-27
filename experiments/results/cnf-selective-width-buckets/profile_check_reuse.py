"""Source-bound census of repeated exact operators in one cold verification pass."""
from collections import Counter
from pathlib import Path
import time
from experiments import compare_cnf_selective_width_buckets as s
base=s.base;k=s.k;old=s.old;out=Path(__file__).parent


def events(proof):
    for node in proof['nodes']:
        yield node['bucket'],'outer'
        ref=node['refinement']
        if ref is None:continue
        for rnd in ref['rounds']:
            for n in rnd['terminal']['nodes']:yield n['bucket'],'terminal'
        if ref['widen'] is not None:
            prefix=ref['rounds'][-1]['terminal']['nodes'][-1]['bucket'] if ref['rounds'] else node['bucket']
            yield {**prefix,'limits':{**prefix['limits'],'bag_limit':prefix['limits']['bag_limit']+1},'steps':prefix['steps']+ref['widen']['steps']},'combined-width'


def main():
    began=time.perf_counter();report=base.load(out/'two-0/report.json');rows=base.load(out/'panel.json');seen={};unique_seen={};seen_roots=set();counts=Counter();records=[];context_counts=Counter()
    for row,result in zip(rows,report['results']):
        path=out/'two-0'/report['stored'][result['root']];proof=base.load(path);k.check_certificate(row['source'],proof)
        local_seen={};cc=Counter();new_source=result['root'] not in seen_roots;seen_roots.add(result['root'])
        cc['unique_sources' if new_source else 'repeated_queries']+=1
        for bucket,context in events(proof):
            cnf=tuple(map(tuple,bucket['cnf']))
            if any(len(c)>bucket['limits']['bag_limit'] for c in cnf):assert not bucket['steps'];continue
            factors=[k.bucket.leaf(c) for c in cnf];active=set(range(len(factors)))
            for step in bucket['steps']:
                ids=step['inputs'];inputs=[factors[i] for i in ids];v=step['variable'];assert ids==sorted(i for i in active if v in factors[i]['scope'])
                bag=sorted({x for f in inputs for x in f['scope']});slots={x:i for i,x in enumerate(bag)}
                key=k.bucket.cache_key(inputs,v,True);value=(tuple(slots[x] for x in step['scope']),step['bits'],step['choices'])
                rows_here=1<<(len(bag)-1);probes_here=2*rows_here*len(inputs);kind='constant' if not step['scope'] else 'nonconstant'
                cc['operator_occurrences']+=1;cc['verified_rows']+=rows_here;cc['verified_table_probes']+=probes_here;context_counts[context+'_rows']+=rows_here
                if new_source:
                    cc['unique_source_probes']+=probes_here
                    if key in local_seen:cc['unique_source_within_query_repeated_probes']+=probes_here
                    elif key in unique_seen:
                        assert unique_seen[key]==value;cc['across_distinct_sources_repeated_probes']+=probes_here
                    else:unique_seen[key]=value
                if key in local_seen:
                    assert local_seen[key]==value;cc['within_query_repeated_rows']+=rows_here;cc['within_query_repeated_probes']+=probes_here;cc['within_query_'+kind+'_rows']+=rows_here
                else:local_seen[key]=value
                if key in seen:
                    assert seen[key]==value;cc['within_pass_repeated_rows']+=rows_here;cc['within_pass_repeated_probes']+=probes_here;cc['within_pass_'+kind+'_rows']+=rows_here;cc['within_pass_hits']+=1
                else:seen[key]=value;cc['distinct_operator_rows']+=rows_here;cc['within_pass_misses']+=1
                active.difference_update(ids);active.add(len(factors));factors.append(dict(scope=step['scope'],bits=step['bits']))
        counts.update(cc);records.append(dict(id=row['id'],proof=old.binding(path),counts=dict(cc)))
    assert 2*counts['verified_rows']==report['cold_counts']['bucket_verified_rows']
    assert 2*counts['verified_table_probes']==report['cold_counts']['bucket_verify_table_probes']
    base.write(out/'checker-reuse-profile.json',dict(summary=dict(counts),contexts=dict(context_counts),distinct_operators=len(seen),distinct_operator_proposal_bytes=len(base.encode(list(seen.items())).encode()),records=records,seconds=time.perf_counter()-began,scope='Post-hoc census of one full cold pass, including repeated queries, bound to checked programs. Equality uses exact locally ordered input scopes/tables, pivot and result/choice tables. Repeated row counts are opportunities, not measured time savings; recognition, map checking, memory, lifetime and invalidation must be charged by a future implementation. No general signed/permutation canonicalizer or persistent authority is implemented.'))
    print(counts)


if __name__=='__main__':main()
