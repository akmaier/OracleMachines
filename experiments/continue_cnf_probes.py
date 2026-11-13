#!/usr/bin/env python3
"""One further bounded probe pass, restoring every earlier immutable checkpoint.

The recognizer, prefix checker and search policy are unchanged. The parent report
is explicit so future passes can resume this run instead of repeating its seed.
"""
from collections import Counter, defaultdict, deque
import argparse
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
from experiments.cnf_coupled_pivots import BudgetedInventory, FrontierIndex
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_probe_window import choices
from experiments.cnf_probe_continuation import TABLE, ContinuationRoutes, search
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_probe_continuation import (
    TABLES, PREVIOUS, restore, apply_delta, export_delta, digests, sha, sha_key,
    unpack, compressed, audit, WithoutGrowth, endpoints)

BASE = Path('experiments/results/cnf-probe-continuation/report.json')


def lineage(report_path):
    """Check report identities and return base-first additive reconstruction order."""
    ordered = []; seen = set(); path = Path(report_path)
    while True:
        actual = path.resolve()
        if actual in seen: raise ValueError('Cyclic checkpoint lineage')
        seen.add(actual); report = json.loads(path.read_text())
        for p,digest in report['fingerprints'].items():
            if sha(p) != digest: raise ValueError('Changed checkpoint implementation')
        ordered.append((path,report))
        if actual == BASE.resolve():
            if report['source_report_sha256'] != sha(PREVIOUS):
                raise ValueError('Changed base checkpoint parent')
            break
        parent = report.get('parent')
        if type(parent) is not dict or set(parent) != {'path','sha256'}:
            raise ValueError('Missing checkpoint parent')
        path = Path(parent['path'])
        if sha(path) != parent['sha256']: raise ValueError('Changed checkpoint parent')
    return list(reversed(ordered))


def restore_report(report_path, path, tmp):
    ordered = lineage(report_path)
    prior = restore(path,tmp)
    for i,(_,report) in enumerate(ordered):
        if digests(path) != report['seed_table_digests']:
            raise ValueError('Checkpoint does not extend the restored seed')
        if prior['final_closed'] != report['baseline_closed']:
            raise ValueError('Incorrect checkpoint baseline')
        delta = report['delta']
        if sha(delta['path']) != delta['sha256']: raise ValueError('Changed checkpoint delta')
        unpacked = tmp/f'continuation-{i}'
        unpack(delta['path'],unpacked,delta['database_sha256'])
        apply_delta(path,unpacked)
        if digests(path) != report['logical_table_digests']:
            raise ValueError('Incorrect reconstructed checkpoint')
        prior = report
    return prior


def opportunity(h, routes, roots):
    """No new discovery: inspect the latest checked block and its target per source."""
    latest = {source:record for record in routes.windows.values() for source in [record['source']]}
    for record in routes.continuations.values():
        source = record['source']
        if record['offset'] > latest[source].get('offset',0): latest[source] = record
    rows = []; frontier = FrontierIndex(h); exposed = defaultdict(set)
    # Follow saved forced rewrites from selected old-plan leaves of open roots.
    # Ignore closed subplans, and do no probing or hypothetical target acquisition.
    for case,root in enumerate(roots):
        if compose(h,[root],routes,Counter())[0][0]: continue
        todo = deque(frontier.frontier(root)); seen = set()
        while todo:
            source = todo.popleft()
            if source in seen: continue
            seen.add(source)
            if compose(h,[source],routes,Counter())[0][0]: continue
            record = latest.get(source)
            if record is not None and record['edge'] is not None and h._load(record['edge']['key']) is not None:
                todo.extend(frontier.frontier(record['edge']['key']))
            else:
                exposed[source].add(case)
    for source,record in sorted(latest.items()):
        node,ranked = choices(h,source,64,Counter())
        row = dict(source_sha256=sha_key(source),offset=record.get('offset',0),status=record['probing']['status'],
            depth=node['depth'],variables=len({abs(l) for c in node['cnf'] for l in c}),clauses=len(node['cnf']),
            open_selected_cases=sorted(exposed[source]))
        tried = {a['variable'] for a in node['profile']['probing'].get('attempts',[])}
        row['outside_ranked_pool'] = sorted({abs(l) for c in node['cnf'] for l in c} - tried - set(ranked))
        if row['status'] == 'clear':
            used = row['offset'] + len(record['probing']['attempts'])//2
            row['remaining_ranked_candidates'] = len(ranked)-used
        else:
            child = h._load(record['edge']['key'])
            row.update(pending=child is None,
                locally_closed=False if child is None else child['summary']['closed'],
                composed_closed=False if child is None else compose(h,[record['edge']['key']],routes,Counter())[0][0],
                selected_open_leaves=None if child is None else len(frontier.frontier(record['edge']['key'])))
        rows.append(row)
    unstarted = []
    for source in sorted(set(exposed)-set(latest)):
        node,ranked = choices(h,source,64,Counter())
        unstarted.append(dict(source_sha256=sha_key(source),ranked_candidates=len(ranked),open_selected_cases=sorted(exposed[source])))
    return dict(rows=rows,unstarted=unstarted,scope='All saved window sources, latest block each. Open selected cases follow existing forced rewrites and skip composed-closed subplans, without source/admission caps; other alternatives are not expanded. Ranking and route replay only, no new probing.')


def run(report_path, out):
    pipeline_started = time.perf_counter(); out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); seed = tmp/'seed'; history = tmp/'history'; started = time.perf_counter()
        prior = restore_report(report_path,seed,tmp); restore_seconds = time.perf_counter()-started
        r = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            parent=dict(path=str(report_path),sha256=sha(report_path)), options=prior['options'],cases=prior['cases'],
            fingerprints={p:sha(p) for p in ('experiments/continue_cnf_probes.py',
                'experiments/cnf_probe_continuation.py','solver/test_cnf_probe_resume.py')},
            policy=dict(source_limit=4,state_limit=32),width=4,seed_table_digests=digests(seed),
            seed_database_bytes=seed.stat().st_size,seed_database_sha256=sha(seed),
            restore_seconds=restore_seconds,records=[],eligibility_seconds=0.0,
            limitations=['One new four-candidate block per visited source; four distinct sources and 32 admitted states per original.',
                'Shared sources can advance again on later originals; the saved input order is part of the policy.',
                'Reused development cases, no independent holdout, peak RAM measurement, end-to-end solver speedup or unrestricted-SAT claim.',
                'Reference checking includes all saved locally closed continuation targets, charging repeated checks explicitly.'])
        started = time.perf_counter(); shutil.copyfile(seed,history); r['clone_seconds'] = time.perf_counter()-started
        h = BudgetedInventory(history,**r['options']); h.set_admission_budget(0); started = time.perf_counter()
        roots = [h.inspect(c['source'])['root']['key'] for c in r['cases']]; routes = ContinuationRoutes(h)
        baseline,_ = compose(h,roots,routes,Counter()); assert baseline == prior['final_closed'] and not h.admitted
        r['baseline_closed'] = baseline; r['preparation_seconds'] = time.perf_counter()-started
        old_continuations = set(routes.continuations); old_windows = set(routes.windows)
        for i,root in enumerate(roots):
            started = time.perf_counter(); skip = compose(h,[root],routes,Counter())[0][0]
            r['eligibility_seconds'] += time.perf_counter()-started
            if skip: continue
            h.counts = Counter(); h.prepared.counts = Counter(); counts = Counter(); started = time.perf_counter()
            result = search(h,root,routes,counts,**r['policy']); covered,plan = compose(h,[root],routes,counts)
            if covered[0]: verify_plan(h,plan,[root],routes,counts)
            row = dict(case=i,seconds=time.perf_counter()-started,closed=covered[0],search=result,counts=dict(counts),
                inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),admission_counts=dict(h.admission_counts),
                admitted_state_sha256=sorted(map(sha_key,h.admitted)))
            assert len(h.admitted) <= 32 and h.counts.get('inserted_nodes',0) <= len(h.admitted)
            r['records'].append(row); (out/'checkpoint.json').write_text(encode(r)+'\n')
            print('case',i,'blocks',counts.get('new_probe_continuations',0),'states',len(h.admitted),'closed',covered[0],flush=True)
        started = time.perf_counter(); routes.refresh(h); final,plan = compose(h,roots,routes,Counter())
        r['recomposition_seconds'] = time.perf_counter()-started
        verify_plan(h,plan,[k for k,b in zip(roots,final,strict=True) if b],routes,Counter())
        assert all(b or not a for a,b in zip(baseline,final,strict=True))
        r['final_closed'] = final; r['gains'] = [i for i,(a,b) in enumerate(zip(baseline,final,strict=True)) if b and not a]
        r['without_growth_closed'],without = compose(h,roots,WithoutGrowth(routes),Counter())
        verify_plan(h,without,without['roots'],WithoutGrowth(routes),Counter())
        r['new_continuation_kinds'] = dict(Counter(rec['probing']['status'] for k,rec in routes.continuations.items() if k not in old_continuations))
        r['new_window_kinds'] = dict(Counter(rec['probing']['status'] for k,rec in routes.windows.items() if k not in old_windows))
        r['pending_continuations'] = sum(rec['edge'] is not None and h._load(rec['edge']['key']) is None for rec in routes.continuations.values())
        r['storage'] = h.storage(); h.close(); r['expanded_database_bytes'] = history.stat().st_size
        started = time.perf_counter(); certificate = out/'coverage.json.gz'; payload = (encode(plan)+'\n').encode()
        certificate.write_bytes(gzip.compress(payload,mtime=0))
        r['certificate'] = dict(path=str(certificate),sha256=sha(certificate),bytes=len(payload),compressed_bytes=certificate.stat().st_size,
            serialization_seconds=time.perf_counter()-started)
        delta = tmp/'delta'; started = time.perf_counter(); r['preserved_rows'],r['delta_rows'] = export_delta(seed,history,delta)
        archive = out/'proof-delta.sqlite3.gz'; compressed(delta,archive)
        r['delta'] = dict(path=str(archive),sha256=sha(archive),database_sha256=sha(delta),database_bytes=delta.stat().st_size,
            compressed_bytes=archive.stat().st_size,export_seconds=time.perf_counter()-started)
        started = time.perf_counter(); rebuilt = tmp/'rebuilt'; shutil.copyfile(seed,rebuilt); apply_delta(rebuilt,delta)
        r['logical_table_digests'] = digests(history); assert digests(rebuilt) == r['logical_table_digests']
        before = sha(rebuilt); apply_delta(rebuilt,delta); assert sha(rebuilt) == before
        r['rebuild_seconds'] = time.perf_counter()-started
        print('cold audit',flush=True); r['audit'] = audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        started = time.perf_counter(); h = BudgetedInventory(rebuilt,**r['options']); h.set_admission_budget(0)
        cold_routes = ContinuationRoutes(h); counts = Counter()
        verify_plan(h,json.loads(gzip.decompress(certificate.read_bytes())),plan['roots'],cold_routes,counts)
        assert compose(h,roots,cold_routes,Counter())[0] == final and not h.admitted
        r['cold_routes'] = dict(seconds=time.perf_counter()-started,counts=dict(cold_routes.counts),witness_counts=dict(counts))
        r['reference'] = endpoints(h,cold_routes,r,out,tmp)
        started = time.perf_counter(); future = opportunity(h,cold_routes,roots)
        r['opportunity_seconds'] = time.perf_counter()-started
        (out/'continuation-opportunity.json').write_text(encode(future)+'\n')
        r['opportunity_sha256'] = sha(out/'continuation-opportunity.json')
        h.close(); assert sha(rebuilt) == before; r['cold_routes']['bytes_unchanged'] = True
        db = sqlite3.connect(delta); admitted = set().union(*(set(row['admitted_state_sha256']) for row in r['records']))
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1')); db.close()
    r['pipeline_seconds'] = time.perf_counter()-pipeline_started
    (out/'report.json').write_text(encode(r)+'\n'); (out/'checkpoint.json').unlink()
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],new_rows=r['delta_rows'])),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output',type=Path)
    parser.add_argument('--parent',type=Path,default=BASE)
    args = parser.parse_args(); run(args.parent,args.output)
