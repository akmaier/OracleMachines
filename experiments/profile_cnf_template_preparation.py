#!/usr/bin/env python3
"""Profile the shared query separately from the paired timing experiment."""
from pathlib import Path
import cProfile, pstats, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_template_preparation as study


def run(out):
    original = study.query
    prof = cProfile.Profile()
    study.query = lambda *args, **kwargs: prof.runcall(original, *args, **kwargs)
    dest = out / 'profile-shared'
    study.worker(dest, study.base.load(out / 'protocol.json'), 'shared')
    actual = study.base.load(dest / 'report.json')
    reference = study.base.load(out / 'shared-0/report.json')
    assert study.read_zip(actual['delta']) == study.read_zip(reference['delta'])
    for a, b in zip(study.bound(actual['queries']), study.bound(reference['queries'])):
        for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids'):
            assert a[field] == b[field], field
    prof.dump_stats(str(out / 'queries.pstats'))
    stats = pstats.Stats(prof)
    rows = [dict(file=f, line=line, function=name, primitive_calls=cc, calls=nc,
                 self_seconds=tt, cumulative_seconds=ct)
            for (f, line, name), (cc, nc, tt, ct, callers) in stats.stats.items()]
    study.base.write(out / 'profile.json', dict(
        script_sha256=study.base.sha(__file__), trial=study.binding(dest / 'report.json'),
        proofs_and_routes_unchanged=True, total_query_seconds=stats.total_tt,
        by_self=sorted(rows, key=lambda r: r['self_seconds'], reverse=True),
        by_cumulative=sorted(rows, key=lambda r: r['cumulative_seconds'], reverse=True),
        limitations=['Query-only instrumentation excluded from paired timing. Cumulative rows overlap; profile time is not an uninstrumented cost or a predicted speedup.']))
    print(study.base.encode(sorted(rows, key=lambda r: r['self_seconds'], reverse=True)[:12]), flush=True)


if __name__ == '__main__':
    run(Path(sys.argv[1]))
