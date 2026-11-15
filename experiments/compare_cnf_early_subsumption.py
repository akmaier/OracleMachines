#!/usr/bin/env python3
"""Supplemental family-exposure control after detecting a 2-CNF confound.

The first transfer protocol is preserved. This separately frozen control reuses
its 42 inputs; it is explicitly selected after inspecting that experiment.
"""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import experiments.compare_cnf_subsumption_transfer as prior
from experiments.cnf_early_subsumption import discover_family, check_family
from experiments.cnf_expanded_coverage import owner
from experiments.cnf_pattern_inventory import encode

FILES = ['experiments/cnf_early_subsumption.py', 'experiments/compare_cnf_early_subsumption.py',
         'solver/test_cnf_early_subsumption.py', 'experiments/validate_cnf_subsumption_transfer.py']
MODES = ('empty', 'subsumption', 'family')


def family_replay(path, protocol, records):
    tick = time.perf_counter(); h = prior.BudgetedInventory(path, **protocol['options'])
    h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with prior.no_acquisition():
            nodes = 0
            for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
                assert owner(h, key)._load(key) is not None; nodes += 1
            for i, row in enumerate(records):
                source = protocol['cases'][i]['source']
                assert row == json.loads(h.db.execute(f'SELECT payload FROM {prior.TABLE} WHERE id=?', (str(i),)).fetchone()[0])
                assert row['source_sha256'] == prior.source_id(source)
                if row['route'] == 'family':
                    check_family(source, row['certificate']); assert row['closed']
                elif row['root'] is not None:
                    assert row['route'] == 'ordinary'
                    assert h._canonical(source, h.config['max_depth'])[2] == row['root']
                    assert h._load(row['root'])['summary']['closed'] == row['closed']
                else:
                    assert row['capped'] and not row['closed']
                assert row['entered_states'] <= protocol['state_limit']
        return dict(seconds=time.perf_counter()-tick, nodes=nodes, queries=len(records), no_acquisition=True)
    finally:
        h.close()


def family_worker(out, protocol):
    out.mkdir(exist_ok=False); began = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'history'; h = prior.BudgetedInventory(path, **protocol['options'])
        h.db.execute(f'CREATE TABLE {prior.TABLE} (id TEXT PRIMARY KEY, payload TEXT NOT NULL)'); h.db.commit()
        initial = path.stat().st_size; records = []; ready = time.perf_counter()
        try:
            for i, case in enumerate(protocol['cases']):
                tick = time.perf_counter(); source = case['source']; counts = Counter()
                h.counts = Counter(); h.prepared.counts = Counter(); h.set_admission_budget(protocol['state_limit'])
                before = h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0]
                cert = discover_family(source, counts); root = None; capped = False
                if cert is not None:
                    check_family(source, cert, counts); closed = True; route = 'family'
                else:
                    root, closed, capped = prior.ordinary(h, source); route = 'ordinary'
                stored = h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0]-before
                row = dict(case=i, group=case['group'], source_sha256=prior.source_id(source), route=route,
                    root=root, closed=closed, capped=capped, certificate=cert,
                    entered_states=len(h.admitted), stored_states=stored, lookup_counts=dict(counts),
                    recognition_counts=dict(h.counts), probe_attempts=h.counts.get('probe_attempts', 0))
                with h.db:
                    h.db.execute(f'INSERT INTO {prior.TABLE} VALUES (?,?)', (str(i), encode(row)))
                row['operation_seconds'] = time.perf_counter()-tick
                with h.db:
                    h.db.execute(f'UPDATE {prior.TABLE} SET payload=? WHERE id=?', (encode(row), str(i)))
                records.append(row)
            elapsed = time.perf_counter()-ready; dbbytes = path.stat().st_size
        finally:
            h.close()
        before = prior.sha(path); cold = family_replay(path, protocol, records); assert prior.sha(path) == before
        tick = time.perf_counter(); archive = out/'history.sqlite3.gz'
        archive.write_bytes(gzip.compress(path.read_bytes(), mtime=0))
        result = dict(mode='family', preparation_seconds=ready-began, query_seconds=elapsed,
            records=records, cold=cold, database_bytes=dbbytes, database_growth=dbbytes-initial,
            archive=dict(path=str(archive), sha256=prior.sha(archive), database_sha256=before,
                         compressed_bytes=archive.stat().st_size), archive_seconds=time.perf_counter()-tick,
            total_seconds=time.perf_counter()-began,
            groups={g:dict(cases=sum(x['group']==g for x in records),
                covered=sum(x['closed'] for x in records if x['group']==g),
                reuse_hits=sum(x['route']=='family' for x in records if x['group']==g),
                entered=sum(x['entered_states'] for x in records if x['group']==g),
                stored=sum(x['stored_states'] for x in records if x['group']==g),
                probes=sum(x['probe_attempts'] for x in records if x['group']==g),
                operation_seconds=sum(x['operation_seconds'] for x in records if x['group']==g))
                for g in sorted({x['group'] for x in records})})
        (out/'report.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        return {k:result[k] for k in ('mode','preparation_seconds','query_seconds','database_growth','groups')}


def run(out, parent_path):
    started = time.perf_counter(); out.mkdir(exist_ok=False); parent = prior.load(parent_path)
    protocol_path = Path(parent['protocol']['path']); assert prior.sha(protocol_path)==parent['protocol']['sha256']
    fingerprints = dict(parent['fingerprints']); fingerprints.update({p:prior.sha(p) for p in FILES})
    frozen = dict(parent=dict(path=str(parent_path),sha256=prior.sha(parent_path)),
        protocol=parent['protocol'], bank=parent['bank'], fingerprints=fingerprints,
        modes=list(MODES), repetitions=2,
        rationale='The first study selected its template before inspecting its reduced classification. Its minimum is 2-CNF, so stored proof reuse must be compared with early family recognition requiring no prepared history. This supplemental control is frozen after that observation, not before the first experiment.',
        accounting='The inherited cap limits _discover admissions; fused conditioning may record additional states. Report actual stored rows separately.')
    (out/'frozen.json').write_text(json.dumps(frozen,indent=2,sort_keys=True)+'\n')
    samples = []
    for repeat, order in enumerate((MODES, tuple(reversed(MODES)))):
        for mode in order:
            destination = out/f'{mode}-{repeat}'
            command = [sys.executable, str(Path(__file__).resolve()), str(destination.resolve()),
                '--worker', mode, '--parent', str(parent_path.resolve())]
            tick = time.perf_counter(); p = subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
            (out/f'{mode}-{repeat}.txt').write_text(p.stdout+p.stderr)
            if p.returncode:
                raise RuntimeError('Supplemental worker failed; output retained')
            r = prior.load(destination/'report.json')
            samples.append(dict(mode=mode,repeat=repeat,path=str(destination/'report.json'),
                                sha256=prior.sha(destination/'report.json'),process_seconds=time.perf_counter()-tick))
            print(json.dumps(dict(mode=mode,repeat=repeat,covered=sum(x['closed'] for x in r['records']),
                hits=sum(x['route']!='ordinary' for x in r['records']),entered=sum(x['entered_states'] for x in r['records']),
                probes=sum(x['probe_attempts'] for x in r['records']),query_seconds=r['query_seconds'])),flush=True)
    for mode in MODES:
        a,b=[prior.load(s['path']) for s in samples if s['mode']==mode]
        for x,y in zip(a['records'],b['records'],strict=True):
            assert {k:v for k,v in x.items() if k!='operation_seconds'}=={k:v for k,v in y.items() if k!='operation_seconds'}
    for p,d in fingerprints.items():
        assert prior.sha(p)==d
    (out/'report.json').write_text(json.dumps(dict(**frozen,samples=samples,pipeline_seconds=time.perf_counter()-started),indent=2,sort_keys=True)+'\n')


def validate(out):
    began=time.perf_counter(); r=prior.load(out/'report.json'); protocol=prior.load(r['protocol']['path'])
    assert prior.sha(r['protocol']['path'])==r['protocol']['sha256']
    assert prior.sha(r['parent']['path'])==r['parent']['sha256']
    bank=prior.unpack(r['bank']); cold=[]; costs={}
    for p,d in r['fingerprints'].items():
        assert prior.sha(p)==d
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td); bank_check=prior.verify_bank(bank,tmp/'bank')
        for i,s in enumerate(r['samples']):
            assert prior.sha(s['path'])==s['sha256']; a=prior.load(s['path']); entry=a['archive']
            assert prior.sha(entry['path'])==entry['sha256']
            path=tmp/f'cold-{i}';path.write_bytes(gzip.decompress(Path(entry['path']).read_bytes()))
            assert prior.sha(path)==entry['database_sha256']
            result=family_replay(path,protocol,a['records']) if s['mode']=='family' else prior.cold_replay(path,protocol,bank,s['mode'],a['records'])
            assert prior.sha(path)==entry['database_sha256'];cold.append(dict(mode=s['mode'],repeat=s['repeat'],**result))
        for mode in MODES:
            arms=[prior.load(s['path']) for s in r['samples'] if s['mode']==mode];a=arms[0]
            costs[mode]=dict(covered=sum(x['closed'] for x in a['records']),
                fast_hits=sum(x['route']!='ordinary' for x in a['records']),
                admissions=sum(x['entered_states'] for x in a['records']),stored=sum(x['stored_states'] for x in a['records']),
                probes=sum(x['probe_attempts'] for x in a['records']),
                mean_prepared_query_seconds=sum(x['preparation_seconds']+x['query_seconds'] for x in arms)/2,
                mean_query_seconds=sum(x['query_seconds'] for x in arms)/2,database_bytes=a['database_bytes'],
                database_growth=a['database_growth'],mean_archive_bytes=sum(x['archive']['compressed_bytes'] for x in arms)/2,
                groups={g:dict(**{k:v for k,v in a['groups'][g].items() if k!='operation_seconds'},
                    mean_operation_seconds=sum(x['groups'][g]['operation_seconds'] for x in arms)/2) for g in a['groups']},
                remaining=[x['case'] for x in a['records'] if not x['closed']])
    result=dict(passed=True,report_sha256=prior.sha(out/'report.json'),cold=cold,costs=costs,
                bank_check=bank_check,seconds=time.perf_counter()-began)
    (out/'reconstruction.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({m:{k:v for k,v in c.items() if k!='groups'} for m,c in costs.items()}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path)
    p.add_argument('--worker',choices=MODES);p.add_argument('--validate',action='store_true');a=p.parse_args()
    if a.worker:
        parent=prior.load(a.parent);protocol=prior.load(parent['protocol']['path']);bank=prior.unpack(parent['bank'])
        print(json.dumps(family_worker(a.output,protocol) if a.worker=='family' else prior.worker(a.output,protocol,bank,a.worker)))
    elif a.validate:
        validate(a.output)
    else:
        run(a.output,a.parent)
