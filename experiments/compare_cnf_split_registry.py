#!/usr/bin/env python3
"""Matched enumeration with full rebuilding versus incremental split checking."""
from collections import Counter
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap as base
from experiments.cnf_split_registry import SplitRegistry

PARENT = Path('experiments/results/cnf-bootstrap-conditioning')
MODES = ('rebuild', 'incremental')
QUERY_FIELDS = ('case','source_sha256','root','root_depth','closed','capped','chosen','pending',
                'entered','stored','admitted_ids','stored_ids','probes')


def worker(out, protocol, seed, expected, mode):
    out.mkdir();began = time.perf_counter();records = [];evidence = {}
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'h';base.restore_archive(seed['archive'], path)
        h = base.CompleteAdmissionInventory(path, **base.OPTIONS);h.set_admission_budget(0)
        initial = base.rows(h);calls = Counter();original_verify = base.split.verify
        def counted(*args, **kwargs):
            calls['verify_calls'] += 1
            return original_verify(*args, **kwargs)
        try:
            for key in initial:assert base.owner(h, key)._load(key) is not None
            registry = SplitRegistry(h) if mode == 'incremental' else None
            setup = time.perf_counter()-began;started = time.perf_counter()
            with patch.object(base.split, 'verify', counted):
                for case, old, previous in zip(protocol['cases'], seed['records'], expected['records'], strict=True):
                    tick = time.perf_counter();h.set_admission_budget(40);h.counts = Counter();counts = Counter()
                    before = base.rows(h);old_calls = calls['verify_calls'];chosen = [];pending = [];route_seconds = 0
                    root = h._canonical(case['source'], 0)[2];closed = False
                    for variable in old['variables']:
                        record = base.split.acquire_record(h, old['leaf'], variable, counts)
                        evidence[base.split.record_key(record)] = record
                        chosen.append(variable);pending.append(base.acquire(h, record))
                        route_tick = time.perf_counter()
                        routes = registry.refresh() if registry else base.routes_for(h, evidence.values())
                        route_seconds += time.perf_counter()-route_tick
                        closed = base.compose(h, [root], routes, Counter())[0][0]
                        if closed:break
                    after = base.rows(h);fresh = set(after)-set(before)
                    assert before.items() <= after.items() and fresh <= h.admitted and len(h.admitted) <= 40
                    row = dict(case=old['case'], source_sha256=base.source_id(case['source']), root=root,root_depth=0,
                        closed=closed,capped=any(any(p) for p in pending),chosen=chosen,pending=pending,
                        entered=len(h.admitted),stored=len(fresh),admitted_ids=sorted(map(base.key_sha,h.admitted)),
                        stored_ids=sorted(map(base.key_sha,fresh)),probes=h.counts['probe_attempts'],
                        counts=dict(h.counts),candidate_counts=dict(counts),admission_counts=dict(h.admission_counts),
                        verify_calls=calls['verify_calls']-old_calls,route_seconds=route_seconds,
                        seconds=time.perf_counter()-tick)
                    assert all(row[k] == previous[k] for k in QUERY_FIELDS), old['case']
                    records.append(row)
            elapsed = time.perf_counter()-started
            assert initial.items() <= base.rows(h).items()
            digest = base.key_sha(base.encode(sorted(base.rows(h).items())))
            assert digest == expected['pattern_digest']
            assert list(evidence.values()) == expected['evidence']
            statistics = registry.statistics() if registry else None
        finally:h.close()
        cold = base.replay(path, protocol, records, list(evidence.values()))
        assert cold['final_closed'] == expected['cold']['final_closed']
        assert cold['proof'] == expected['cold']['proof']
        archive = base.archive(path, out)
        assert archive['database_sha256'] == expected['archive']['database_sha256']
        result = dict(mode=mode,setup_seconds=setup,operation_seconds=elapsed,records=records,
            covered=sum(r['closed'] for r in records),entered=sum(r['entered'] for r in records),
            stored=sum(r['stored'] for r in records),probes=sum(r['probes'] for r in records),
            fresh_assumptions=sum(r['candidate_counts'].get('bootstrap_fresh_assumptions',0) for r in records),
            pairs=len(evidence),pattern_digest=digest,verify_calls=calls['verify_calls'],
            route_seconds=sum(r['route_seconds'] for r in records),registry=statistics,archive=archive,
            evidence_binding=protocol['expected'],cold={k:v for k,v in cold.items() if k!='proof'},
            cold_proof_sha256=base.key_sha(base.encode(cold['proof'])))
        base.write(out/'report.json', result)
        return result


def run(out):
    out.mkdir(exist_ok=False)
    parent = base.load(PARENT/'protocol.json');seed = base.load(PARENT/'seed.json')
    previous = base.load(PARENT/'validation.json');expected = base.load(PARENT/'enumerate-0/report.json')
    sources = dict(previous['source_fingerprints'])
    for p in sources:assert base.sha(p) == sources[p], p
    sources = base.source_fingerprints(sources)
    for p in ('experiments/cnf_split_registry.py','experiments/compare_cnf_split_registry.py',
              'solver/test_cnf_split_registry.py'):sources[p] = base.sha(p)
    binding = lambda p:dict(path=str(p),sha256=base.sha(p))
    protocol = dict(parent=binding(PARENT/'protocol.json'), seed=binding(PARENT/'seed.json'),
        expected=binding(PARENT/'enumerate-0/report.json'), checkpoint=binding(PARENT/'checkpoint.json'),
        cases=parent['cases'],options=parent['options'],state_limit=40,candidate_limit=4,
        source_fingerprints=sources,orders=[MODES,tuple(reversed(MODES)),MODES],
        rationale='Only external split-route maintenance changes. Same prepared seed, candidates, order, complete recognition allowance and full row audits.',
        limitations=['The 24 adaptive synthetic inputs and selected enumeration policy are reused, not a new holdout.',
            'Both arms have the same small verify-call counter wrapper; profiling is not enabled during benchmark timings.',
            'The live cache requires committed append-only writes on one inventory; other writes invalidate it.',
            'Guards read count/index pages and new row IDs; composition, source trace acquisition and cold checking remain charged.',
            'SQL archives and proof remain byte-identical. Live metadata JSON size is not peak RAM.'])
    base.write(out/'protocol.json', protocol);samples=[]
    for repeat, order in enumerate(protocol['orders']):
        for mode in order:
            dest = out/f'{mode}-{repeat}';result = worker(dest, protocol, seed, expected, mode)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
            print(base.encode({k:result[k] for k in ('mode','covered','stored','probes','verify_calls','route_seconds','operation_seconds')}),flush=True)
    summary = {}
    for mode in MODES:
        values = [base.load(s['path']) for s in samples if s['mode']==mode]
        summary[mode] = {k:sum(r[k] for r in values)/len(values) for k in
            ('setup_seconds','operation_seconds','route_seconds','verify_calls')}
    base.write(out/'report.json', dict(protocol_sha256=base.sha(out/'protocol.json'),samples=samples,summary=summary,
        same_patterns_pairs_proof_and_database=True))
    print(base.encode(summary),flush=True)


if __name__ == '__main__':run(Path(sys.argv[1]))
