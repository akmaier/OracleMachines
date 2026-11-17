#!/usr/bin/env python3
"""Measure fresh family transfer with explicit pre-discovery familiarity."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_positive_child as previous
from experiments.cnf_cross_family import FAMILIES, SIZES, generate
from experiments.validate_cnf_unsat_support import bound

base = previous.base; binding = previous.binding; native = previous.native; prep = previous.prep
FIELDS = previous.FIELDS; OLD_FIELDS = previous.OLD_FIELDS
PARENT = Path('experiments/results/cnf-positive-child')
MODES = ('baseline', 'positive')
FILES = ('experiments/cnf_cross_family.py', 'solver/test_cnf_cross_family.py',
         'experiments/compare_cnf_cross_family.py', 'experiments/validate_cnf_cross_family.py')


def inherited(parent):
    return previous.inherited(parent) + bound(parent['positive_child_decisions'])


def exclusions(parent):
    records = sum((bound(parent[f]) for f in FIELDS), []) + inherited(parent)
    return [dict(query_root=k) for k in sorted({r['query_root'] for r in records})]


def inputs(s, p):
    # Preserve same-template transfer controls, but do not use them as the
    # principal evidence for acquisition of unfamiliar residuals.
    neighbours = prep.ordinary.eager.previous.inputs(s, p)
    cases = [dict(c, family='neighbour-control', configuration=None) for c in neighbours['cases']]
    excluded = {r['query_root'] for r in bound(p['previous_decisions'])} | set(native.rows(s))
    excluded.update(s._canonical(c['source'])[2] for c in cases)
    rejected = []
    for sample in range(4):
        for size in SIZES:
            for family in FAMILIES:
                for attempt in range(100):
                    source = generate(family, size, sample, attempt); key = s._canonical(source)[2]
                    if key not in excluded: break
                    rejected.append(dict(family=family, size=size, sample=sample, attempt=attempt, root=key))
                else: raise ValueError('Exhausted deterministic novelty attempts')
                excluded.add(key)
                cases.append(dict(case=len(cases), template_case=family, family=family, source=source,
                                  configuration=dict(size=size, sample=sample, attempt=attempt)))
    return dict(cases=cases, neighbour_selection=neighbours['selection'], rejected=rejected,
                selection=dict(neighbour_controls=len(neighbours['cases']), fresh_family_cases=48,
                               families=list(FAMILIES), requested_sizes=list(SIZES)))


def evaluate(s, source, target, guards, mode, eligible, limit):
    tick = time.perf_counter(); before = Counter(s.counts)
    cnf, names, root = s._canonical(target)
    familiarity = dict(root=root, known_after_preparation=not eligible, guards=len(guards),
                       variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf)))
    metrics = dict(s.counts-before); seconds = time.perf_counter()-tick
    result = previous.evaluate(s, source, target, guards, mode, eligible, limit)
    result.update(familiarity=familiarity, familiarity_metrics=metrics, familiarity_seconds=seconds)
    return result


def summarize(records):
    summary = previous.summarize(records)
    summary['known_after_preparation'] = sum(r['familiarity']['known_after_preparation'] for r in records)
    summary['unfamiliar_after_preparation'] = len(records)-summary['known_after_preparation']
    return summary


def worker(out, p, catalog, mode):
    assert mode in MODES
    # Family names and construction parameters are never arguments of evaluate.
    with patch.object(previous.old, 'inherited', inherited), patch.object(previous.old, 'evaluate', evaluate), patch.object(previous.old, 'summarize', summarize):
        previous.old.worker(out, p, catalog, mode)


def run(out):
    out.mkdir(exist_ok=False); parent = base.load(PARENT / 'checkpoint.json')
    bank = base.load('experiments/results/cnf-premise-guard/protocol.json')
    sources = dict(base.load(PARENT / 'validation.json')['source_fingerprints'])
    for f, h in sources.items(): assert base.sha(f) == h, f
    sources.update({f: base.sha(f) for f in FILES})
    base.write(out / 'previous-decisions.json', exclusions(parent))
    p = dict(parent=binding(PARENT / 'checkpoint.json'), source_fingerprints=sources,
        support_index=parent['extended_support_proposals'], causal_index=parent['causal_support_proposals'],
        template_catalog=bank['template_catalog'], cores=bank['cores'], bank_catalog=bank['bank_catalog'],
        previous_decisions=binding(out / 'previous-decisions.json'), node_limit=100000,
        alternative_budget=1, variable_limit=4, per_template=4, orders=[MODES, MODES[::-1]],
        limitations=['48 deterministic inputs from four finite generators plus 12 same-template controls; this is not arbitrary-SAT coverage or an exhaustive taxonomy.',
                    'Both policies retain identical ordinary and near-guard preparation. Baseline means the native acquisition path after that shared preparation, not a standalone external SAT solver.',
                    'Targets are excluded from inherited raw roots; actual familiarity is checked after preparation and independently reconstructed at every chronological prefix.',
                    'Family labels are analysis metadata. Only unlabelled source CNFs enter preparation and solving. All four fresh families are exhaustively truth-checked after timing; the larger neighbour controls retain native/composed certificate checks.',
                    'Two opposite worker orders, no concurrent tests or profiles. Generation is charged separately; query, persistence, warm and full cold replay costs are retained.',
                    'No solver optimization or new Lean theorem is introduced; failed discovery and alternate certificates remain preserved. No minimum-cost, polynomial-space or unrestricted-SAT efficiency claim.'])
    base.write(out / 'protocol.json', p); tick = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'initial'; base.restore_archive(parent['reference_union'], path); s = native.ResidualSolver(path)
        try: catalog = inputs(s, p)
        finally: s.close()
    assert len(catalog['cases']) == 60
    base.write(out / 'cases.json', catalog)
    base.write(out / 'generation.json', dict(seconds=time.perf_counter()-tick, selection=catalog['selection']))
    samples = []
    for repeat, order in enumerate(p['orders']):
        for mode in order:
            dest = out / f'{mode}-{repeat}'
            subprocess.run([sys.executable, __file__, 'worker', str(dest), str(out / 'protocol.json'), str(out / 'cases.json'), mode], check=True)
            samples.append(dict(repeat=repeat, mode=mode, **binding(dest / 'report.json')))
            print('fresh', repeat, mode, flush=True)
    summary = {}
    for mode in MODES:
        data = [bound(e)['summary'] for e in samples if e['mode'] == mode]; first = data[0]
        timed = [k for k in first if k.endswith('_seconds') or k == 'peak_rss_bytes']
        fixed = [k for k in first if k not in timed and k not in ('mode', 'sidecar_bytes')]
        for other in data[1:]:
            for k in fixed: assert first[k] == other[k], k
        summary[mode] = {**{k: first[k] for k in fixed}, **{'mean_'+k: sum(r[k] for r in data)/len(data) for k in timed},
                         'sidecar_bytes': [r['sidecar_bytes'] for r in data]}
    base.write(out / 'report.json', dict(protocol=binding(out / 'protocol.json'), cases=binding(out / 'cases.json'), samples=samples, summary=summary))
    print(base.encode(summary), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'worker': worker(Path(sys.argv[2]), base.load(sys.argv[3]), base.load(sys.argv[4]), sys.argv[5])
    else: run(Path(sys.argv[1]))
