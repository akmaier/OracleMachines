"""Diagnostic cProfile samples; use a new output directory from repository root."""
import argparse
import cProfile
import gzip
import hashlib
import json
from pathlib import Path
import pstats
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path.cwd()))
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_repair_history import RepairHistory
from experiments.cnf_residual_dag import ResidualSolver, holds

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True,
                    help='new directory; existing results are never overwritten')
OUT = parser.parse_args().output
OUT.mkdir(parents=True, exist_ok=False)
report = json.loads(Path('experiments/results/cnf-repair-history/report.json').read_text())


def summary(profile):
    stats = pstats.Stats(profile)
    rows = [dict(file=f, line=line, function=name, calls=nc, primitive_calls=cc,
                 self_seconds=tt, cumulative_seconds=ct)
            for (f, line, name), (cc, nc, tt, ct, callers) in stats.stats.items()]
    return dict(profiled_total_seconds=stats.total_tt,
                top_self=sorted(rows, key=lambda x: -x['self_seconds'])[:15],
                top_cumulative=sorted(rows, key=lambda x: -x['cumulative_seconds'])[:15])


def profile_history(case_id):
    case = report['cases'][case_id]
    source = tuple(map(tuple, case['base']))
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/'history.sqlite3'
        history = RepairHistory(path)
        profile = cProfile.Profile()
        profile.enable()
        result = history.prepare(source)
        assert result['answer'] == case['expected'][0]
        version = result['version']
        fallback = 0
        for step, clause in enumerate(case['additions'], 1):
            try:
                result = history.append_repair(version, clause)
            except UnsupportedExpansion:
                fallback += 1
                expanded = history.materialize(version)['cnf'] + (tuple(clause),)
                result = history.prepare(expanded)
            assert result['answer'] == case['expected'][step]
            version = result['version']
        profile.disable()
        source += tuple(map(tuple, case['additions']))
        assert history.materialize(version)['cnf'] == source
        if result['answer']:
            assert holds(source, history.witness(version)['model'])
        history.close()
        raw = path.read_bytes()
        name = f'case-{case_id:02d}.sqlite3.gz'
        (OUT/name).write_bytes(gzip.compress(raw, mtime=0))
    return dict(case=case_id, family=case['family'], additions=len(case['additions']),
                fallback=fallback, final_version=version, archive=name,
                database_sha256=hashlib.sha256(raw).hexdigest(), **summary(profile))


records = [profile_history(i) for i in (8, 13, 18, 19)]
case = json.loads(Path('experiments/results/cnf-residual-dag/report.json').read_text())['cases'][20]
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp)/'seeded.sqlite3'
    solver = ResidualSolver(path)
    profile = cProfile.Profile()
    profile.enable()
    result = solver.solve(case['cnf'])
    profile.disable()
    assert result['answer'] == case['expected']
    solver.close()
    raw = path.read_bytes()
    (OUT/'seeded-20.sqlite3.gz').write_bytes(gzip.compress(raw, mtime=0))
records.append(dict(family='seeded_3cnf', source='cnf-residual-dag case 20',
                    metrics=result['metrics'], archive='seeded-20.sqlite3.gz',
                    database_sha256=hashlib.sha256(raw).hexdigest(), **summary(profile)))
output = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
              profiles=records, limitations=[
                  'Single instrumented diagnostic samples; profiler distorts performance',
                  'Self times are exclusive; cumulative times overlap and must not be added',
                  'Setup/opening and final exports, snapshots, validation are outside profiling',
                  'History profile includes acquisition, all updates and fallback materialization',
                  'No representative workload mixture or competitive-CDCL comparison',
                  'Memory conclusions come from preceding separate allocation study, not this profile'])
(OUT/'report.json').write_text(json.dumps(output,indent=2)+'\n')
for r in records:
    print(r['family'], 'total',round(r['profiled_total_seconds'],5),'fallback',r.get('fallback'))
    print('self', [(x['function'],round(x['self_seconds'],5)) for x in r['top_self'][:6]])
    print('cumulative',[(x['function'],round(x['cumulative_seconds'],5)) for x in r['top_cumulative'][:6]])
