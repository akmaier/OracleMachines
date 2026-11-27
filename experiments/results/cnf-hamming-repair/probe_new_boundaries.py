"""Frozen constructed transfer probe; planted witnesses are audit-only."""
from pathlib import Path
from collections import Counter
import hashlib,json,random,sys,time
from experiments import cnf_hamming_repair as e


def write(p,x):p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare(out):
    assert not (out/'constructed-protocol.json').exists()
    rng=random.Random(2811260032);inputs=[];witnesses=[]
    for n in (50,60,70,80):
        for j in range(8):
            names=sorted(rng.sample(range(1,10000),n));model={v:rng.choice((False,True)) for v in names};clauses=set()
            while len(clauses)<round(4.36*n):
                c=tuple(sorted(rng.choice((-1,1))*v for v in rng.sample(names,3)))
                if any(model[abs(v)]==(v>0) for v in c):clauses.add(c)
            source=[list(c) for c in sorted(clauses)];rng.shuffle(source)
            assert sorted({abs(v) for c in source for v in c})==names
            inputs.append(dict(id=len(inputs),source=source))
            witnesses.append(dict(format=e.previous.FORMAT,names=names,values=[model[v] for v in names]))
    write(out/'constructed-inputs.json',inputs);write(out/'constructed-audit-witnesses.json',witnesses)
    files=[out/'constructed-inputs.json',out/'constructed-audit-witnesses.json',Path(__file__),Path('experiments/cnf_hamming_repair.py')]
    write(out/'constructed-protocol.json',dict(files={str(p):sha(p) for p in files},seed=2811260032,node_limit=e.NODE_LIMIT,scope='32 new constructed planted-SAT sources, eight at each n=50,60,70,80, density 4.36 and sparse names. Protocol frozen before running, after main policy freeze. Repair-only probe; no claim these miss the full portfolio or represent external inputs. Audit witnesses never seed discovery. Timings can overlap independent validation and are not matched performance evidence.'))


def run(out):
    p=load(out/'constructed-protocol.json')
    for file,h in p['files'].items():assert sha(Path(file))==h
    rows=load(out/'constructed-inputs.json');audit=load(out/'constructed-audit-witnesses.json');records=[];summary=Counter()
    for row,witness in zip(rows,audit):
        source=row['source'];assert e.previous.check(source,witness)['answer']
        c=Counter();start=time.perf_counter();seed=e.proposal(source,c);r=e.search(source,seed,len(seed['names']),c,node_limit=p['node_limit'])
        if r['witness'] is not None:assert e.previous.check(source,r['witness'])['answer']
        else:assert r['diagnostic']['reason']=='budget' and r['exclusion'] is None
        summary[r['diagnostic']['reason']]+=1
        records.append(dict(id=row['id'],variables=len(seed['names']),result=r,counts=dict(c),seconds=time.perf_counter()-start))
    write(out/'constructed-results.json',dict(passed=True,summary=dict(summary),records=records,scope=p['scope']))
    print(json.dumps(dict(summary=dict(summary),unresolved_ids=[r['id'] for r in records if r['result']['witness'] is None])))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
