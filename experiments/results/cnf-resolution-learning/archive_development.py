"""Lossless archival of large probes, with corrected initial source provenance."""
from pathlib import Path
import gzip,hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments.compare_cnf_resolution_learning import load,write,binding,sha
out=Path(__file__).parent
records=[]
for name,source,initial in [('development.json','initial-core.py.gz',True),('activity-development.json','activity-core.py.gz',False)]:
    path=out/name;archive=Path(str(path)+'.gz')
    if path.exists():
        raw=path.read_bytes();archive.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(archive.read_bytes())==raw;path.unlink()
    elif archive.exists():raw=gzip.decompress(archive.read_bytes())
    else:continue
    data=json.loads(raw);core=gzip.decompress((out/source).read_bytes());core_sha=hashlib.sha256(core).hexdigest()
    if not initial:assert core_sha==data['source']['sha256']
    else:assert core_sha==load(out/'initial-policy.json')['source_sha256']
    summary=[{k:v for k,v in c.items() if k!='proof'} for c in data['cases']]
    write(out/(name.replace('.json','-summary.json')),dict(cases=summary))
    records.append(dict(archive=binding(archive),uncompressed_sha256=hashlib.sha256(raw).hexdigest(),source_archive=binding(out/source),source_sha256=core_sha,initial=initial,cases=len(data['cases']),provenance_note='The initial probe recorded the live source binding at completion after that file had been revised. Its executed version is the separately archived initial source, captured before revision; preserve the original late-bound field verbatim in the raw probe.' if initial else 'The activity probe captured its source binding at start; the archived bytes match exactly. The final source adds guarded transport without changing search.'))
write(out/'development-provenance.json',dict(records=records))
print([(r['initial'],r['cases']) for r in records])
