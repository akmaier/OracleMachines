#!/usr/bin/env python3
"""Profile only four exposed queries after rebuilding the same causal prefix."""
import cProfile
from pathlib import Path
import pstats
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_refined_origins as study


def run(out):
    original = study.prior.prior.query
    measured = []
    def query(s, case, q, policy, hints, banks, budget):
        if (case['index'], q['template']) not in ((7, 4), (15, 3), (19, 3), (20, 3)):
            return original(s, case, q, policy, hints, banks, budget)
        profiler = cProfile.Profile()
        result = profiler.runcall(original, s, case, q, policy, hints, banks, budget)
        path = out / f"profile-{case['index']}-{q['template']}.pstats"
        profiler.dump_stats(path)
        rows = []
        for (filename, line, function), (primitive, calls, own, cumulative, _) in pstats.Stats(profiler).stats.items():
            rows.append(dict(file=filename, line=line, function=function, primitive_calls=primitive,
                calls=calls, own_seconds=own, cumulative_seconds=cumulative))
        measured.append(dict(case=case['index'], template=q['template'], profile=study.binding(path),
            functions=sorted(rows, key=lambda r: -r['cumulative_seconds'])))
        return result
    study.prior.prior.query = query
    study.worker(out / 'profile-worker', study.base.load(out / 'protocol.json'), 'refined')
    prior = study.base.load(out / 'refined-0/report.json')
    report = study.base.load(out / 'profile-worker/report.json')
    assert study.read_zip(prior['delta']) == study.read_zip(report['delta'])
    for a, b in zip(study.bound(prior['queries']), study.bound(report['queries'])):
        for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids', 'partial', 'learned', 'screen'):
            assert a.get(field) == b.get(field), field
    study.base.write(out / 'profiling.json', dict(source=study.binding(__file__),
        report=study.binding(out / 'profile-worker/report.json'), matched_delta=prior['delta'], queries=measured,
        limitations=['Diagnostic profiler overhead excludes these timings from comparative means. Cumulative function times overlap and must not be added.',
            'Only the four exposed queries are profiled. Prior chronological queries, pools and lazy origins are reconstructed; no final hints or answers seed the profile.']))


if __name__ == '__main__': run(Path(sys.argv[1]))
