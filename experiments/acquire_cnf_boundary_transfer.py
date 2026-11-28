#!/usr/bin/env python3
"""Frozen SATLIB selection, safe in-memory archive reads and labelled audit data."""
from pathlib import Path
from collections import Counter
from urllib.request import urlopen
import hashlib,io,random,sys,tarfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_boundary_repair import load,write,binding,sha,bound,e
from experiments.cnf_external_cutsets import parse_dimacs


def emit(source):
    return 'p cnf %d %d\n'%(max((abs(v) for c in source for v in c),default=0),len(source))+''.join(' '.join(map(str,c+[0]))+'\n' for c in source)


def rename(source, seed):
    rng=random.Random(seed);names=sorted({abs(v) for c in source for v in c})
    ids=rng.sample(range(11,11+3*len(names)),len(names));signs=[rng.choice((-1,1)) for _ in names]
    mapping={v:ids[i]*signs[i] for i,v in enumerate(names)}
    return [[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in reversed(source)],mapping


def freeze(out):
    assert not (out/'selection.json').exists()
    parent='experiments/results/cnf-boundary-repair/checkpoint.json'
    write(out/'selection.json',dict(parent=binding(parent),parent_manifest=binding('experiments/results/cnf-boundary-repair/manifest.json'),source_index='https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html',groups=[dict(name=prefix+str(n),archive=f'{prefix}{n}-{m}.tar.gz',publisher_answer=prefix=='uf') for n,m in ((50,218),(75,325),(100,430)) for prefix in ('uf','uuf')],indices=[10,30,60,90],controls='For the first selected original of each group, append one signed sparse permutation (seed 202611280204 plus group index) and one edit removing the first clause and flipping the first literal in the last nonempty clause. Keep controls separate from originals.',policy=dict(node_limit=e.NODE_LIMIT,prefix_limit=e.PREFIX_LIMIT,max_rounds=e.MAX_ROUNDS),policy_files={file:sha(file) for file in ('experiments/cnf_boundary_repair.py','experiments/cnf_partition_repair.py','experiments/cnf_hamming_repair.py')},scope='Six size/truth groups; four zero-based lexicographic member indices per group, frozen before downloading new contents or evaluating. No outcome-guided filtering or tuning. Previously unused relative to the retained external, constructed and 182-case panels by exact normalized equality; not all-history semantic novelty or representative sampling.'))


def acquire(out):
    assert not (out/'panel.json').exists();selection=load(out/'selection.json')
    for file,h in selection['policy_files'].items():assert sha(file)==h
    records=[];rows=[];descriptions={};transports=[];originals=[]
    for i,group in enumerate(selection['groups']):
        url='https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/'+group['archive']
        with urlopen(url,timeout=45) as response:data=response.read(25000000)
        assert len(data)<25000000
        with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
            members=sorted((m for m in archive.getmembers() if m.isfile() and m.name.lower().endswith('.cnf')),key=lambda m:(Path(m.name).name,m.name))
            first=None
            for index in selection['indices']:
                member=members[index];raw=archive.extractfile(member).read();key=f't{len(rows):03}';path=out/'raw'/(key+'.cnf');path.write_bytes(raw)
                source,header=parse_dimacs(raw.decode());rows.append(dict(id=key,source=source,raw=binding(path)));first=first or (key,source)
                description=dict(group=group['name'],kind='original',publisher_answer=group['publisher_answer'],url=url,archive_sha256=hashlib.sha256(data).hexdigest(),archive_bytes=len(data),member=member.name,index=index,header=header)
                descriptions[key]=description;records.append(dict(**description,raw=binding(path)))
            originals.append((i,group,first))
        print(group['name'],len(members),flush=True)
    for i,group,(original,source) in originals:
        changed,mapping=rename(source,202611280204+i);edited=[c[:] for c in source[1:]];next(c for c in reversed(edited) if c)[0]*=-1
        for kind,variant,label in (('signed-permutation',changed,group['publisher_answer']),('edit',edited,None)):
            key=f't{len(rows):03}';path=out/'raw'/(key+'.cnf');path.write_text(emit(variant));assert parse_dimacs(path.read_text())[0]==variant
            rows.append(dict(id=key,source=variant,raw=binding(path)));descriptions[key]=dict(group=group['name'],kind=kind,original=original,publisher_answer=label)
            if kind=='signed-permutation':transports.append(dict(id=key,original=original,mapping={str(v):w for v,w in mapping.items()}))
    assert len(rows)==36
    prior_paths=('experiments/results/cnf-external-cutsets/panel.json','experiments/results/cnf-hamming-repair/constructed-inputs.json','experiments/results/cnf-verified-operators/panel.json')
    prior={path:{e.previous.capacity.canonical(r['source'],Counter()) for r in load(path)} for path in prior_paths}
    seen={};overlap=[]
    for row in rows:
        key=e.previous.capacity.canonical(row['source'],Counter());matches=[path for path,keys in prior.items() if key in keys]
        overlap.append(dict(id=row['id'],prior_matches=matches,same_panel_exact=seen.get(key)));seen.setdefault(key,row['id'])
        assert not matches and overlap[-1]['same_panel_exact'] is None
    write(out/'panel.json',rows);write(out/'descriptions.json',descriptions);write(out/'transports.json',transports)
    write(out/'overlaps.json',dict(records=overlap,prior_panels=[binding(path) for path in prior_paths],scope='Exact normalized equality only; signed controls remain related even when equality differs. No general isomorphism or all-history novelty claim.'))
    write(out/'acquisition.json',dict(selection=binding(out/'selection.json'),records=records,scope='Only selected raw member bytes retained; archives read in memory, no tar paths extracted. Publisher truth is audit-only.'))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
