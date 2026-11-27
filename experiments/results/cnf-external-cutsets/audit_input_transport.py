"""Independent raw-token audit and exact signed-renaming checks, outside timing."""
from collections import Counter
from pathlib import Path
import json,random,time
from experiments import compare_cnf_external_cutsets as s
base=s.base;old=s.old


def reference_parse(text):
    # Independent cursor parser for the frozen source files: separate line roles,
    # then consume complete zero-terminated integer clauses from a token stream.
    lines=[line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith('c')]
    assert lines[0].split()[:2]==['p','cnf'];_,_,nv,nc=lines.pop(0).split();nv=int(nv);nc=int(nc)
    if '%' in lines:
        end=lines.index('%');assert lines[end+1:] in ([],['0']);lines=lines[:end]
    tokens=list(map(int,' '.join(lines).split()));clauses=[];i=0
    while i<len(tokens):
        stop=tokens.index(0,i);clause=tokens[i:stop];assert all(1<=abs(v)<=nv for v in clause);clauses.append(clause);i=stop+1
    assert len(clauses)==nc;return clauses


def main(out):
    start=time.perf_counter();rows=base.load(out/'panel.json');desc=base.load(out/'descriptions.json');byid={r['id']:r for r in rows};groups=[];maps=[];rejected=0
    for row in rows:
        source=reference_parse(Path(row['raw']['path']).read_text());assert source==row['source']
        canonical=s.emit_dimacs(source);lines=canonical.splitlines();header=lines[0].split();n=int(header[2]);m=int(header[3])
        malformed=['p cnf '+str(n)+' '+str(m+1)+'\n'+'\n'.join(lines[1:]),canonical+'0\n','p cnf '+str(n)+' '+str(m)+'\n'+str(n+1)+' '+ ' '.join(' '.join(map(str,c+[0])) for c in source),'\n'.join(lines[1:])]
        for text in malformed:
            try:s.e.parse_dimacs(text)
            except ValueError:rejected+=1
            else:raise AssertionError('Malformed DIMACS admitted')
        d=desc[row['id']]
        if d['kind']=='original' and d['group'] not in groups:groups.append(d['group'])
        if d['kind']!='signed-permutation':continue
        original=byid[d['original']]['source'];names=sorted({abs(v) for c in original for v in c});rng=random.Random(2711271954+groups.index(d['group']));perm=rng.sample(range(11,11+len(names)),len(names));sign=[rng.choice((-1,1)) for _ in names];mapping={v:(perm[i],sign[i]) for i,v in enumerate(names)}
        assert len({v for v,_ in mapping.values()})==len(names)
        transformed=Counter(tuple(sorted(mapping[abs(l)][0]*mapping[abs(l)][1]*(1 if l>0 else -1) for l in c)) for c in original)
        assert transformed==Counter(tuple(sorted(c)) for c in source)
        maps.append(dict(id=row['id'],original=d['original'],mapping=[[v,*mapping[v]] for v in names],exact_clause_multiset=True))
    assert len(maps)==6 and rejected==148
    base.write(out/'input-audit.json',dict(passed=True,raw_files_independently_parsed=len(rows),rejected_malformed_inputs=rejected,signed_bijections=maps,seconds=time.perf_counter()-start,scope='Exact literal bijections and clause multisets establish equivalence of six renamed controls. Original SATLIB labels remain metadata only; deleted/flipped edits have no inherited answer. This checks admission/transport, not unresolved SAT truth.'))
    print(base.encode(dict(passed=True,raw_inputs=len(rows),renamings=len(maps),malformed_rejected=rejected)))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
