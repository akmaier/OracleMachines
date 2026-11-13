#!/usr/bin/env python3
"""Extract checked pair reductions from the saved open frontier; preserve misses."""
from collections import Counter
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_probes import restore_report
from experiments.cnf_coupled_pivots import BudgetedInventory, AdmissionExhausted
from experiments.cnf_trace_reuse import (source_attempts, make_record, verify_rewrite, lift_rewrite,
    pair_witness, check_pair, TraceRoutes)
from experiments.cnf_common_consequence import first_common_pair
from experiments.cnf_probe_equivalence import first_equivalence_pair, substitute_block
from experiments.cnf_probe_learning import learning_batch
from experiments.cnf_residual_dag import ResidualSolver, restrict, holds
from experiments.cnf_simplification import discover_simplification
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_probe_continuation import (
    sha, sha_key, digests, export_delta, apply_delta, compressed, unpack, audit, WithoutGrowth)

PARENT = Path('experiments/results/cnf-probe-resumption/report.json')


def archive_json(path, value):
    raw = (encode(value)+'\n').encode(); path.write_bytes(gzip.compress(raw, mtime=0))
    return dict(path=str(path), sha256=sha(path), bytes=len(raw), compressed_bytes=path.stat().st_size)


def read_archive(item):
    if sha(item['path']) != item['sha256']: raise ValueError('Changed artifact')
    return json.loads(gzip.decompress(Path(item['path']).read_bytes()))


def restore_checkpoint(report_path, path, tmp):
    """Restore the parent eight-table history, additive node delta and proof refs.

    Callers MUST use the returned records in TraceRoutes; the parent probe runner
    alone does not know about external trace-rewrite routes.
    """
    r = json.loads(Path(report_path).read_text())
    if sha(r['parent']['path']) != r['parent']['sha256']: raise ValueError('Changed parent')
    for p,digest in r['fingerprints'].items():
        if sha(p) != digest: raise ValueError('Changed implementation')
    restore_report(Path(r['parent']['path']),path,tmp)
    if digests(path) != r['seed_table_digests']: raise ValueError('Incorrect parent history')
    d = r['delta']
    if sha(d['path']) != d['sha256']: raise ValueError('Changed delta')
    unpack(d['path'],tmp/'trace-delta',d['database_sha256']); apply_delta(path,tmp/'trace-delta')
    if digests(path) != r['logical_table_digests']: raise ValueError('Incorrect reconstructed history')
    return r, read_archive(r['rewrites'])


def scan(h, opportunity, counts):
    targets = {r['source_sha256']:r for r in opportunity['rows'] if r['status']=='clear' and r['open_selected_cases']}
    sources = {json.loads(p)['source'] for p, in h.db.execute('SELECT payload FROM cnf_probe_windows_v1')}
    rows = []; records = []
    for source in sorted(sources):
        identity = sha_key(source)
        if identity not in targets: continue
        node = h._load(source); attempts, refs = source_attempts(h,source,counts)
        common = first_common_pair(attempts,counts); equiv = first_equivalence_pair(attempts,counts)
        # This is a bounded opportunity list, not an applied learning pass.
        batch = learning_batch(node['cnf'],attempts,16,counts)
        witness = common or equiv
        row = dict(source_sha256=identity,source=source,cases=targets[identity]['open_selected_cases'],
            exhausted=not targets[identity]['remaining_ranked_candidates'],attempts=len(attempts),
            common=common,equivalence=equiv,learning_cap16=batch,references=refs)
        rows.append(row)
        if witness:
            i = 2*witness['pair']; records.append(make_record(h,source,refs[i:i+2],counts))
    if {r['source_sha256'] for r in rows} != set(targets): raise ValueError('Missing open source')
    return rows, records


def matched(h, records, repeats=5, iterations=100):
    """Same chosen pair and checked substitution, after discovery chose the pair.

    Saved mode includes SQL/JSON lookup. Fresh mode knows the same variable,
    rediscovers its two closures and checks them. Neither mode acquires a target.
    """
    samples = []
    for repeat in range(repeats):
        for mode in (('saved','fresh') if repeat%2==0 else ('fresh','saved')):
            counts=Counter(); started=time.perf_counter()
            for _ in range(iterations):
                for record in records:
                    if mode=='saved':
                        verify_rewrite(h,record,counts)
                    else:
                        node=h._load(record['source'])
                        from experiments.cnf_trace_reuse import read_attempt
                        variable=read_attempt(h,record['source'],record['references'][0],Counter())['variable']
                        attempts=[dict(variable=variable,value=b,certificate=discover_simplification(
                            restrict(node['cnf'],{variable:b},counts),counts,pure=False)) for b in (False,True)]
                        counts['fresh_control_assumptions']+=2
                        check_pair(node['cnf'],attempts,counts); kind,witness=pair_witness(attempts,counts)
                        # This checkpoint's matched control concerns equivalence only.
                        assert kind==record['reduction']['kind']=='equivalence' and witness==record['reduction']['witness']
                        target=substitute_block(node['cnf'],witness,counts)
                        _,names,key=h._canonical(target,node['depth'])
                        assert encode(record['edge'])==encode(dict(key=key,names=names))
            samples.append(dict(mode=mode,repeat=repeat,seconds=time.perf_counter()-started,counts=dict(counts)))
    return dict(records=len(records),iterations=iterations,samples=samples,
        scope='Warm chosen-pair verification/substitution only, including reference lookup in saved mode and one variable lookup in fresh mode. Selection, preparation, persistence and target recognition excluded from both; fresh-control assumptions are separate from zero-probe rewrite acquisition.')


def reference(h, records, r, out, tmp):
    path=tmp/'reference'; solver=AccountedResidualSolver(path); started=time.perf_counter(); rows=[]
    for record in records:
        node=h._load(record['source']); target,_=verify_rewrite(h,record,Counter())
        child=h._load(record['edge']['key'])
        a=solver.solve(node['cnf']); b=solver.solve(target); assert a['answer']==b['answer']
        if child is not None:
            c=solver.solve(child['cnf']); assert c['answer']==a['answer']
            if c['answer']: assert holds(node['cnf'],lift_rewrite(h,record,c['model'],Counter()))
        rows.append(dict(source_sha256=sha_key(record['source']),source=a,target=b))
    originals=[]
    for case in r['gains']:
        result=solver.solve(r['cases'][case]['source'])
        if result['answer']: assert holds(r['cases'][case]['source'],result['model'])
        originals.append(dict(case=case,result=result))
    solver.close(); elapsed=time.perf_counter()-started; before=sha(path); started=time.perf_counter()
    solver=ResidualSolver(path)
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'): assert solver._read(key) is not None
    verified=len(solver.checked); assert not solver.counts.get('expanded_nodes',0); solver.close(); assert sha(path)==before
    cold=time.perf_counter()-started; archive=out/'reference.sqlite3.gz'; compressed(path,archive)
    return dict(rows=rows,originals=originals,seconds=elapsed,cold_seconds=cold,verified_nodes=verified,
        path=str(archive),sha256=sha(archive),database_sha256=before,database_bytes=path.stat().st_size,
        compressed_bytes=archive.stat().st_size)


def run(out):
    started_pipeline=time.perf_counter(); out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td); seed=tmp/'seed'; history=tmp/'history'; started=time.perf_counter()
        parent=restore_report(PARENT,seed,tmp); restore_seconds=time.perf_counter()-started
        r=dict(parent=dict(path=str(PARENT),sha256=sha(PARENT)),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_trace_reuse.py','experiments/compare_cnf_trace_reuse.py',
                'solver/test_cnf_trace_reuse.py','solver/fixtures/trace-reuse.json')},
            options=parent['options'],cases=parent['cases'],seed_table_digests=digests(seed),
            seed_database_bytes=seed.stat().st_size,restore_seconds=restore_seconds,
            policy='Scan all 41 exposed clear streams; at most one paired rewrite and 32 target-state admissions per source. Deriving the paired rewrite uses no new assumptions; target recognition may probe and is charged separately.',
            limitations=['Reused development frontier, not an independent holdout or universal SAT class.',
                'Logical implication checker is Python, not Lean-verified.',
                'Common/equivalence scan is complete only for the saved pairs; binary-learning candidates are capped at 16 per source and are not applied.',
                'Reference proofs and fresh microbenchmark controls have separately charged new computations; peak RAM is unmeasured.'])
        shutil.copyfile(seed,history); h=BudgetedInventory(history,**r['options']); h.set_admission_budget(0)
        opportunity_path=PARENT.parent/'continuation-opportunity.json'; assert sha(opportunity_path)==parent['opportunity_sha256']
        started=time.perf_counter(); counts=Counter(); rows,records=scan(h,json.loads(opportunity_path.read_text()),counts)
        r['scan']=dict(seconds=time.perf_counter()-started,counts=dict(counts),inventory_counts=dict(h.counts),
            prepared_counts=dict(h.prepared.counts),sources=len(rows),attempts=sum(x['attempts'] for x in rows),
            common_sources=sum(x['common'] is not None for x in rows),equivalence_sources=sum(x['equivalence'] is not None for x in rows),
            learning_sources=sum(bool(x['learning_cap16']) for x in rows),learning_clauses=sum(len(x['learning_cap16']) for x in rows))
        r['opportunities']=archive_json(out/'opportunities.json.gz',rows)
        r['rewrites']=archive_json(out/'rewrites.json.gz',records)  # Save before any target acquisition.
        started=time.perf_counter(); roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        routes=TraceRoutes(h); baseline,_=compose(h,roots,routes,Counter()); assert baseline==parent['final_closed']
        r['preparation_seconds']=time.perf_counter()-started; r['baseline_closed']=baseline; r['acquisitions']=[]
        for record in records:
            h.set_admission_budget(32); h.counts=Counter(); counts=Counter(); started=time.perf_counter()
            target,_=verify_rewrite(h,record,counts); node=h._load(record['source']); pending=False
            try: assert h._edge(target,node['depth'])==record['edge']
            except AdmissionExhausted: pending=True
            routes.add_rewrite(h,record)
            r['acquisitions'].append(dict(source_sha256=sha_key(record['source']),seconds=time.perf_counter()-started,
                pending=pending,counts=dict(counts),inventory_counts=dict(h.counts),admission_counts=dict(h.admission_counts),
                admitted_state_sha256=sorted(map(sha_key,h.admitted))))
        final,plan=compose(h,roots,routes,Counter()); verify_plan(h,plan,plan['roots'],routes,Counter())
        assert all(b or not a for a,b in zip(baseline,final)); r['final_closed']=final
        r['gains']=[i for i,(a,b) in enumerate(zip(baseline,final)) if b and not a]
        r['without_growth_closed'],without=compose(h,roots,WithoutGrowth(routes),Counter())
        verify_plan(h,without,without['roots'],WithoutGrowth(routes),Counter())
        r['matched']=matched(h,records); r['certificate']=archive_json(out/'coverage.json.gz',plan)
        h.close(); r['expanded_database_bytes']=history.stat().st_size
        delta=tmp/'delta'; started=time.perf_counter(); r['preserved_rows'],r['delta_rows']=export_delta(seed,history,delta)
        compressed(delta,out/'proof-delta.sqlite3.gz'); r['delta']=dict(path=str(out/'proof-delta.sqlite3.gz'),sha256=sha(out/'proof-delta.sqlite3.gz'),
            database_sha256=sha(delta),database_bytes=delta.stat().st_size,compressed_bytes=(out/'proof-delta.sqlite3.gz').stat().st_size,
            export_seconds=time.perf_counter()-started)
        r['logical_table_digests']=digests(history); rebuilt=tmp/'rebuilt'; shutil.copyfile(seed,rebuilt); apply_delta(rebuilt,delta)
        assert digests(rebuilt)==r['logical_table_digests']; before=sha(rebuilt); apply_delta(rebuilt,delta); assert sha(rebuilt)==before
        print('cold inventory audit',flush=True); r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        started=time.perf_counter(); h=BudgetedInventory(rebuilt,**r['options']); h.set_admission_budget(0)
        routes=TraceRoutes(h,read_archive(r['rewrites'])); verify_plan(h,read_archive(r['certificate']),plan['roots'],routes,Counter())
        assert compose(h,roots,routes,Counter())[0]==final and not h.admitted
        r['cold_routes']=dict(seconds=time.perf_counter()-started,counts=dict(routes.counts))
        r['reference']=reference(h,records,r,out,tmp); h.close(); assert sha(rebuilt)==before
    r['pipeline_seconds']=time.perf_counter()-started_pipeline
    (out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],scan=r['scan'],new_rows=r['delta_rows'])),flush=True)


if __name__=='__main__': run(Path(sys.argv[1]))
