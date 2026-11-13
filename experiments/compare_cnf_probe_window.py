#!/usr/bin/env python3
"""Bounded probe-window continuations on the complete retained original history."""
from collections import Counter
import gzip
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_window import TABLE,WindowRoutes,search,record_key,verify_window
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_residual_dag import restrict,holds,ResidualSolver
from experiments.cnf_simplification import discover_simplification,check_simplification
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.compare_cnf_growth_escape import (
    TABLES as OLD_TABLES,restore_latest,apply_delta as apply_growth_delta,sha,sha_key,unpack)
from experiments.compare_cnf_clause_mask import table_digest
from experiments.compare_cnf_pivot_alternatives import compressed
from experiments.compare_cnf_retained_plans import audit

TABLES=OLD_TABLES+(TABLE,)
GROWTH=Path('experiments/results/cnf-growth-escape/report.json')
ROUTES=Path('experiments/results/cnf-growth-routes/report.json')
CORE=Path('experiments/results/cnf-coupled-pivots-originals/core-admission-audit.json')


class WithoutGrowth:
    def __init__(self,routes):
        self.by_source={k:[(rule,children) for rule,children in rows if rule['kind']!='growth']
                        for k,rows in routes.by_source.items()}


def digests(path):
    db=sqlite3.connect(path)
    try:return {t:table_digest(db,t) for t in TABLES}
    finally:db.close()


def restore(path,tmp):
    restore_latest(path,tmp);g=json.loads(GROWTH.read_text());r=json.loads(ROUTES.read_text())
    assert r['source_report_sha256']==sha(GROWTH)
    for report in (g,r):
        for p,d in report['fingerprints'].items():assert sha(p)==d,p
    d=g['delta'];assert sha(d['path'])==d['sha256']
    unpack(d['path'],tmp/'growth',d['database_sha256']);apply_growth_delta(path,tmp/'growth')
    db=sqlite3.connect(path)
    assert {t:table_digest(db,t) for t in OLD_TABLES}==r['logical_table_digests']
    db.execute(f'CREATE TABLE {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');db.commit();db.close()
    return r,[dict(path=str(p),sha256=sha(p)) for p in (GROWTH,ROUTES,CORE)]


def export_delta(seed,history,path):
    db=sqlite3.connect(history);out=sqlite3.connect(path);db.execute('ATTACH DATABASE ? AS old',(str(seed),))
    preserved={};added={}
    try:
        for t in TABLES:
            assert db.execute(f'SELECT count(*) FROM old.{t} o LEFT JOIN main.{t} n ON o.id=n.id WHERE n.id IS NULL OR n.payload!=o.payload').fetchone()[0]==0
            preserved[t]=db.execute(f'SELECT count(*) FROM old.{t}').fetchone()[0]
            out.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            rows=db.execute(f'SELECT n.id,n.payload FROM main.{t} n WHERE NOT EXISTS (SELECT 1 FROM old.{t} o WHERE o.id=n.id) ORDER BY n.rowid')
            out.executemany(f'INSERT INTO {t} VALUES (?,?)',rows)
            added[t]=out.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
        out.commit();return preserved,added
    finally:out.close();db.close()


def apply_delta(history,path):
    db=sqlite3.connect(history);delta=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
    try:
        with db:
            for t in TABLES:
                db.execute(f'CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                for key,payload in delta.execute(f'SELECT id,payload FROM {t} ORDER BY rowid'):
                    old=db.execute(f'SELECT payload FROM {t} WHERE id=?',(key,)).fetchone()
                    if old is not None and old!=(payload,):raise ValueError('Conflicting window delta payload')
                    db.execute(f'INSERT OR IGNORE INTO {t} VALUES (?,?)',(key,payload))
    finally:delta.close();db.close()


def mechanism(source):
    counts=Counter();target=check_additive_elimination(source,dict(variable=15),counts,clause_growth_limit=3)
    rows=[]
    for name,cnf in [('source',source),('projection',target)]:
        attempts=[]
        for variable in sorted({abs(l) for c in cnf for l in c}):
            for value in (False,True):
                branch=restrict(cnf,{variable:value},counts)
                certificate=discover_simplification(branch,counts,pure=False)
                check_simplification(branch,certificate,counts,pure=False)
                attempts.append(dict(variable=variable,value=value,certificate=certificate))
        rows.append(dict(name=name,source=cnf,binary_clauses=sum(len(c)==2 for c in cnf),
            choices=probe_choices(cnf,4,counts),full_binary_order=probe_choices(cnf,64,counts),attempts=attempts))
    return dict(rows=rows,counts=dict(counts),claim_scope='Complete single-assumption unit-propagation diagnostic for this core only; source coordinates are retained.')


def endpoint_audit(history,r,roots,out,tmp):
    h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
    path=tmp/'endpoints';solver=AccountedResidualSolver(path);started=time.perf_counter();rows=[]
    for i in r['gains']:
        answer=solver.solve(r['cases'][i]['source'])
        if answer['answer']:assert holds(r['cases'][i]['source'],answer['model'])
        rows.append(dict(case=i,result=answer))
    # Check every new local closed target, including endpoints that do not yet
    # supply complete original coverage. Models lift through the forced value
    # and its independently checked unit closure.
    local=[]
    for identity,payload in h.db.execute(f'SELECT id,payload FROM {TABLE}'):
        record=json.loads(payload)
        if record['edge'] is None:continue
        child=h._load(record['edge']['key'])
        if child is None or not child['summary']['closed']:continue
        node=h._load(record['source']);target=verify_window(h,record,Counter())
        a,b=solver.solve(node['cnf']),solver.solve(target);assert a['answer']==b['answer']
        if b['answer']:
            last=record['probing']['attempts'][-1];fixed={last['variable']:not last['value']}
            _,closure=check_simplification(restrict(node['cnf'],fixed,Counter()),record['probing']['closure'],Counter(),pure=False)
            fixed.update(closure);model={abs(l):False for c in node['cnf'] for l in c};model.update(b['model']);model.update(fixed)
            assert holds(node['cnf'],model)
        local.append(dict(window_sha256=sha_key(identity),source=a,target=b))
    solver.close();h.close();elapsed=time.perf_counter()-started
    before=sha(path);started=time.perf_counter();solver=ResidualSolver(path);verified=0
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
        assert solver._read(key) is not None;verified+=1
    assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(path)==before
    cold=time.perf_counter()-started;archive=out/'endpoints.sqlite3.gz';compressed(path,archive)
    return dict(originals=rows,local=local,seconds=elapsed,cold_seconds=cold,verified_nodes=verified,
        path=str(archive),sha256=sha(archive),database_sha256=before,database_bytes=path.stat().st_size)


def main(out):
    pipeline_started=time.perf_counter()
    out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);seed=tmp/'seed';history=tmp/'history';started=time.perf_counter()
        prior,inputs=restore(seed,tmp);restore_seconds=time.perf_counter()-started
        r=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),inputs=inputs,
            fingerprints={p:sha(p) for p in ('experiments/cnf_probe_window.py','experiments/compare_cnf_probe_window.py','solver/test_cnf_probe_window.py')},
            options=prior['options'],cases=prior['cases'],policy=dict(source_limit=4,state_limit=32,width=4),
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,restore_seconds=restore_seconds,
            seed_database_sha256=sha(seed),records=[],eligibility_seconds=0.0,limitations=[
            'A continuation of the existing binary-frequency order, at most four untried variables from its first 64 entries per unresolved source.',
            'At most four distinct unresolved sources and 32 newly entered recognition states per original; negative and pending windows remain checked reusable records.',
            'Selected development sources, no independent holdout or general SAT speedup. Preparation, per-state work, storage and cold verification remain additional.',
            'The already covered positive-control core runs first and remains in the paid history; its preparation and acquisition are separately reported.'])
        source=json.loads(CORE.read_text())['cores'][0]['source']
        started=time.perf_counter();r['mechanism']=mechanism(source);r['mechanism_seconds']=time.perf_counter()-started
        started=time.perf_counter();shutil.copyfile(seed,history);r['clone_seconds']=time.perf_counter()-started
        h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0);started=time.perf_counter()
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];routes=WindowRoutes(h)
        baseline,_=compose(h,roots,routes,Counter());assert baseline==prior['final_closed'];assert not h.admitted
        r['baseline_closed']=baseline;r['preparation_seconds']=time.perf_counter()-started
        _,_,core=h._canonical(source,0);assert h._load(core)['kind']=='unresolved'
        for case,root in [('positive_control',core)]+list(enumerate(roots)):
            started=time.perf_counter()
            skip=case!='positive_control' and compose(h,[root],routes,Counter())[0][0]
            r['eligibility_seconds']+=time.perf_counter()-started
            if skip:continue
            h.counts=Counter();h.prepared.counts=Counter();counts=Counter();started=time.perf_counter()
            result=search(h,root,routes,counts,**r['policy'])
            covered,plan=compose(h,[root],routes,counts)
            if covered[0]:verify_plan(h,plan,[root],routes,counts)
            row=dict(case=case,seconds=time.perf_counter()-started,closed=covered[0],search=result,counts=dict(counts),
                inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
                admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
            if case=='positive_control':
                control_closed,control_plan=compose(h,[root],WithoutGrowth(routes),Counter())
                row['closed_without_growth']=control_closed[0]
                if control_closed[0]:verify_plan(h,control_plan,[root],WithoutGrowth(routes),Counter())
            assert len(h.admitted)<=32 and h.counts.get('inserted_nodes',0)<=len(h.admitted)
            r['records'].append(row);(out/'checkpoint.json').write_text(encode(r)+'\n')
            print('case',case,'windows',counts.get('new_probe_windows',0),'states',len(h.admitted),'closed',covered[0],flush=True)
        started=time.perf_counter();final,plan=compose(h,roots,routes,Counter());r['recomposition_seconds']=time.perf_counter()-started
        verify_plan(h,plan,[k for k,b in zip(roots,final,strict=True) if b],routes,Counter())
        r['final_closed']=final;r['gains']=[i for i,(a,b) in enumerate(zip(baseline,final,strict=True)) if b and not a]
        r['without_growth_closed'],without_plan=compose(h,roots,WithoutGrowth(routes),Counter())
        verify_plan(h,without_plan,without_plan['roots'],WithoutGrowth(routes),Counter())
        assert all(b or not a for a,b in zip(baseline,final,strict=True))
        r['window_kinds']=dict(Counter(rec['probing']['status'] for rec in routes.windows.values()))
        r['pending_windows']=sum(rec['edge'] is not None and h._load(rec['edge']['key']) is None for rec in routes.windows.values())
        r['storage']=h.storage();h.close();r['expanded_database_bytes']=history.stat().st_size
        started=time.perf_counter();certificate=out/'coverage.json.gz';payload=(encode(plan)+'\n').encode();certificate.write_bytes(gzip.compress(payload,mtime=0))
        r['certificate']=dict(path=str(certificate),sha256=sha(certificate),bytes=len(payload),compressed_bytes=certificate.stat().st_size,
            serialization_seconds=time.perf_counter()-started)
        delta=tmp/'delta';started=time.perf_counter();r['preserved_rows'],r['delta_rows']=export_delta(seed,history,delta)
        archive=out/'proof-delta.sqlite3.gz';compressed(delta,archive)
        r['delta']=dict(path=str(archive),sha256=sha(archive),database_sha256=sha(delta),database_bytes=delta.stat().st_size,
            compressed_bytes=archive.stat().st_size,export_seconds=time.perf_counter()-started)
        started=time.perf_counter();rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
        r['logical_table_digests']=digests(history);assert digests(rebuilt)==r['logical_table_digests']
        before=sha(rebuilt);apply_delta(rebuilt,delta);assert sha(rebuilt)==before
        r['rebuild_seconds']=time.perf_counter()-started
        print('cold audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        started=time.perf_counter();h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0);cold_routes=WindowRoutes(h)
        counts=Counter();verify_plan(h,json.loads(gzip.decompress(certificate.read_bytes())),plan['roots'],cold_routes,counts)
        replayed,_=compose(h,roots,cold_routes,Counter());assert replayed==final
        assert not h.admitted;h.close();assert sha(rebuilt)==before
        r['cold_routes']=dict(seconds=time.perf_counter()-started,counts=dict(cold_routes.counts),witness_counts=dict(counts),bytes_unchanged=True)
        r['reference']=endpoint_audit(rebuilt,r,roots,out,tmp)
        # Every acquired node must have an actual admission reservation; rows in
        # all unrelated tables must be preserved, never rewritten or deleted.
        db=sqlite3.connect(delta);admitted=set().union(*(set(row['admitted_state_sha256']) for row in r['records']))
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'));db.close()
    r['pipeline_seconds']=time.perf_counter()-pipeline_started
    (out/'report.json').write_text(encode(r)+'\n');(out/'checkpoint.json').unlink()
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],new_rows=r['delta_rows'])),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
