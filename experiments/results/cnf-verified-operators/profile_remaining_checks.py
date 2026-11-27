"""Post-hoc call profile of one JSON cold pass; not matched timing evidence."""
from collections import Counter
from pathlib import Path
import cProfile,pstats,time
from experiments import compare_cnf_verified_operators as s
base=s.base;out=Path(__file__).parent


def main():
    rows=base.load(out/'panel.json');report=base.load(out/'pass-0/report.json');protocol=base.load(out/'protocol.json');counts=Counter()
    def replay():
        engine=s.Engine('pass',protocol['cache_limits']);engine.phase('cold')
        for row,result in zip(rows,report['results']):
            cnf,_=s.native.normalize(row['source'],counts);root=s.native.token(cnf,counts)
            proof=base.load(out/'pass-0'/report['stored'][root]);got=engine.check_certificate(row['source'],proof,counts)
            if got['answer'] is not None:assert got['answer']==result['answer']
        return engine.finish()
    prof=cProfile.Profile();started=time.perf_counter();cache=prof.runcall(replay);elapsed=time.perf_counter()-started
    stats=pstats.Stats(prof);records=[]
    for (file,line,name),(primitive,calls,self_seconds,cumulative,callers) in stats.stats.items():
        if '/OracleMachines/' in file:file=file.split('/OracleMachines/')[-1]
        records.append(dict(file=file,line=line,name=name,primitive=primitive,calls=calls,self_seconds=self_seconds,cumulative_seconds=cumulative))
    records.sort(key=lambda r:r['self_seconds'],reverse=True)
    base.write(out/'remaining-check-profile.json',dict(records=records,counts=dict(counts),cache=cache,seconds=elapsed,scope='Instrumented one-pass JSON replay, excluding native fallback audit. Includes JSON reads and an empty operator bank; this is diagnostic CPU attribution, not a new matched timing sample. Cumulative times overlap.'))
    print(base.encode(records[:18]))


if __name__=='__main__':main()
