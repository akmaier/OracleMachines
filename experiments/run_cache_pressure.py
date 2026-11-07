#!/usr/bin/env python3
"""Separate retained-payload pressure experiment; no whole-RSS claim."""
import hashlib,json,random,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from solver.persistent import PersistentSolver,DEFAULT_ENGINE

def main():
    target=Path(sys.argv[1])
    if target.exists():raise ValueError('Output already exists')
    rng=random.Random(1708);edges=[rng.getrandbits(64)|1 for _ in range(256)]
    changes=[(rng.randrange(256),rng.getrandbits(64)|1) for _ in range(20)]
    report=dict(seed=1708,edges=edges,changes=changes,width=3,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),engine_sha256=hashlib.sha256(DEFAULT_ENGINE.read_bytes()).hexdigest(),runs=[])
    target.write_text(json.dumps(report,indent=2)+'\n')
    for repetition in range(3):
        for cap in ((4096,2*1024**2) if repetition%2==0 else (2*1024**2,4096)):
            row=dict(repeat=repetition,payload_cap=cap,queries=[],replayed=[]);report['runs'].append(row)
            try:
                with tempfile.TemporaryDirectory() as d:
                    path=Path(d)/'s.db';history=[]
                    with PersistentSolver(path,active_cache_bytes=cap,wal_checkpoint_bytes=65536) as s:
                        r=s.layered(3,append=edges,left=1,right=1,witness=True);row['queries'].append(r);history.append(r['state'])
                        for index,mask in changes:
                            r=s.layered(3,r['state'],replace={index:mask},left=1,right=1,witness=True)
                            row['queries'].append(r);history.append(r['state'])
                            assert r['answer'] and r['storage']['active_caches']['layered']['retained_payload_bytes']<=cap
                        assert s.db.execute('SELECT count(*) FROM layered_states').fetchone()[0]==len(history)
                        row['objects']=dict(s.db.execute('SELECT count(*) AS objects,sum(raw_bytes) AS raw_bytes,sum(length(payload)) AS stored_bytes FROM knowledge_objects').fetchone())
                        row['final_storage']=s.archive_usage()
                    with PersistentSolver(path,active_cache_bytes=cap) as s:
                        for state in (history[0],history[10],history[-1]):
                            replay=s.layered(3,state,left=1,right=1,witness=True);assert replay['answer'];row['replayed'].append(replay)
                    row['database_bytes']=path.stat().st_size
                row['status']='ok'
            except Exception as e:row.update(status='error',error=type(e).__name__+': '+str(e))
            target.write_text(json.dumps(report,separators=(',',':'))+'\n')
    if any(r['status']!='ok' for r in report['runs']):raise SystemExit('Pressure failures retained')
if __name__=='__main__':main()
