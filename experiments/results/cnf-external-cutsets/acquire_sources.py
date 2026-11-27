"""Download fixed public SATLIB archives; preserve selected bytes and provenance."""
from pathlib import Path
from urllib.request import urlopen
import hashlib,io,json,tarfile
out=Path(__file__).parent
root='https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/'
collections=[('uf20','RND3SAT/uf20-91.tar.gz',True),('uf50','RND3SAT/uf50-218.tar.gz',True),('uuf50','RND3SAT/uuf50-218.tar.gz',False),('flat30','GCP/flat30-60.tar.gz',True),('par8','DIMACS/PARITY/parity.tar.gz',True),('phole','DIMACS/PHOLE/pigeon-hole.tar.gz',False)]
assert not (out/'acquisition.json').exists()
records=[]
for group,path,label in collections:
 url=root+path
 with urlopen(url,timeout=45) as response:data=response.read(25000000)
 assert len(data)<25000000
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
  members=sorted((m for m in archive.getmembers() if m.isfile() and m.name.lower().endswith('.cnf') and (group!='par8' or Path(m.name).name.startswith('par8'))),key=lambda m:(Path(m.name).name,m.name))
  chosen=members if group=='phole' else members[:4]
  assert len(chosen)==(5 if group=='phole' else 4),(group,len(chosen))
  for member in chosen:
   raw=archive.extractfile(member).read();dest=out/'raw'/(group+'-'+Path(member.name).name);assert not dest.exists();dest.write_bytes(raw)
   records.append(dict(group=group,url=url,archive_sha256=hashlib.sha256(data).hexdigest(),archive_bytes=len(data),member=member.name,path=str(dest),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),publisher_answer=label))
 print(group,len(chosen),len(data),flush=True)
(out/'acquisition.json').write_text(json.dumps(dict(records=records,selection_sha256=hashlib.sha256((out/'selection.json').read_bytes()).hexdigest(),scope='Selected original bytes from public SATLIB archives. Publisher labels are provenance only, never certificate authority. No archive paths are extracted onto the filesystem.'),sort_keys=True,indent=2)+'\n')
