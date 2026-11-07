#!/usr/bin/env python3
"""Reproduce semantic-propagation and native-replay gaps using temporary stores.

These are operation-count diagnostics, not statistically timed benchmarks.
The user archive and historical experiment files are never modified.
"""
import argparse,gzip,hashlib,json,random,statistics,subprocess,tempfile,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from solver.persistent import PersistentSolver,DEFAULT_ENGINE
from solver.test_interfaces import xor,neg
from solver import planning
from solver.resources import Deadline
from solver.interfaces import counters

def replay_diagnostic():
    rng=random.Random(1709);rows=[]
    for width in (3,4):
        q=1<<width
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
            initial=s.layered(width,append=[rng.getrandbits(q*q)|1 for _ in range(256)],left=1,right=1)
            edited=s.layered(width,initial['state'],replace={127:rng.getrandbits(q*q)|1},left=1,right=1)
            repeated=s.layered(width,edited['state'],left=1,right=1)
            assert all(x['answer'] for x in (initial,edited,repeated))
            rows.append(dict(width=width,threshold=max(64,48000//(q*q)),initial=initial['layered'],edit=edited['layered'],repeat=repeated['layered']))
    return rows

def semantic_diagnostic():
    with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',interfaces=True) as s:
        first=s.expand(add={f'e{i}':xor(i,i+1) for i in range(16)})
        def plan(state):
            evidence=s.db.execute('SELECT evidence FROM expansion_states WHERE id=?',(state,)).fetchone()[0]
            return planning.load_plan(s.interfaces.store.get(evidence,'expansion_result')['plan'],s.interfaces.store,Deadline(30),counters())
        oldout=plan(first['state'])['buckets']['0']['output']
        second=s.expand(first['state'],add={'e0':neg(xor(0,1))})
        newout=plan(second['state'])['buckets']['0']['output']
        a,b=s.interfaces.read(oldout),s.interfaces.read(newout)
        av=[s.interfaces.acquire(a,i) for i in range(len(a['rows']))]
        bv=[s.interfaces.acquire(b,i) for i in range(len(b['rows']))]
        assert first['answer'] and second['answer']
        return dict(size=16,answer=[first['answer'],second['answer']],same_projected_scope=a['scope']==b['scope'],scope=a['scope'],old_rows=av,new_rows=bv,same_projected_identity=oldout==newout,
            metrics={k:second['interfaces'][k] for k in ['affected_buckets','reused_buckets','propagation_stops','source_delta_reads','plan_copy_entries']})

def phase_analysis():
    source=ROOT/'experiments/results/structured/runs.jsonl.gz'
    rows=[json.loads(l) for l in gzip.open(source,'rt')];out={}
    for mode in ('checked','portfolio','learned','adaptive'):
        totals=defaultdict(list)
        for r in rows:
            if r['mode']!=mode or r['stream']!='chronological_shift':continue
            phases=Counter()
            for q in r['records']:
                if q['event']=='query':phases.update(q.get('result',{}).get('phase_ns',{}))
            for key,value in phases.items():totals[key].append(value/1e6)
        out[mode]={key:statistics.median(values) for key,values in totals.items()}
    return dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),median_stream_phase_ms=out)

def routing_diagnostic():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',adaptive=True) as s:
        error=None
        with patch.object(s,'archive_usage',side_effect=RuntimeError('injected storage accounting failure')):
            try:s.solve('010',learn=False)
            except RuntimeError as exc:error=str(exc)
        observations=[dict(r) for r in s.db.execute('SELECT route,success FROM route_observations')]
        return dict(requests=1,injected_after='core answer and first route observation',error=error,observations=observations)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    reports=dict(replay=replay_diagnostic(),semantic=semantic_diagnostic(),routing=routing_diagnostic(),phases=phase_analysis())
    for name,report in reports.items():(args.output/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    files=[Path(__file__),DEFAULT_ENGINE,ROOT/'formal/Solver.lean',*sorted((ROOT/'solver').glob('*.py')),*sorted((ROOT/'formal/OracleMachines').glob('*.lean'))]
    metadata=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),replay_seed=1709,
        purpose='Deterministic operation-count diagnostics; existing chronological phase reanalysis',
        fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(dict(replay=reports['replay'],semantic=reports['semantic']),indent=2))
if __name__=='__main__':main()
