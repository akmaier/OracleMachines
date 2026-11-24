#!/usr/bin/env python3
"""Freeze and census guard probes on the eight exposed chronological edits."""
from collections import Counter
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_stopped_origins as old
from experiments.cnf_guard_probe_census import GuardProbeObserver,analyse_event
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_fresh_mixtures import attempt
from experiments import cnf_residual_dag as native
base=old.base;PARENT=Path('experiments/results/cnf-guard-frontier');ORIGINS=Path('experiments/results/cnf-stopped-origins')
FILES=('experiments/cnf_guard_probe_census.py','solver/test_cnf_guard_probe_census.py','experiments/study_cnf_guard_probes.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    parent=base.load(PARENT/'checkpoint.json');p=base.load(ORIGINS/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        origins=p['origins'],cases=p['cases'],node_limit=256,event_limit=256,event_key_bytes=8*1024*1024,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
            'All eight origin/edit pairs are exposed and retained. The native solver and observer each restore the exact causal prefix immediately before the edit; no later repeat or cumulative union supplies answers.',
            'One native/observed pair per target is a correctness and overhead census, not a statistically controlled speed comparison. It proposes no live search policy and claims no faster solving.',
            'The observer tracks source coordinates and matches saved guards only at actual ordinary whole-probe sites. Unsupported bindings and observation limits remain explicit misses.',
            'One missing guard assumption proposes a local variable/polarity. Full-source unit refutability is not automatically a refutation of a selected component/subset. Actual child unit propagation is independently replayed off-line.',
            'Presence is read before the ordinary probe using SQL without invoking native _read or warming checked state. This includes uncommitted rows; presence is evidence of availability, not independent proof authority.',
            'Posthoc candidate certificates are stored separately and never fed into either search. The opposite branch and the whole input remain unresolved unless ordinary search proves otherwise.',
            'Event-key and event-count caps do not bound coordinate lists, matching work, active capture frames, construction transients or full-process memory. Source templates are explicitly provisioned; recognition and fresh evaluation remain open.']))


def run(out):
    p=base.load(out/'protocol.json');cases=old.bound(p['cases']);reports=[];began=time.perf_counter()
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);bankpath=temp/'bank';bank=native.ResidualSolver(bankpath)
        try:
            for origin in p['origins']:
                dest=out/f'target-{origin+1}';dest.mkdir();reference=base.load(ORIGINS/f'origin-{origin}/report.json')
                templates=old.bound(reference['extraction'])['templates'];source=cases[origin+1]['source'];results={};archives={};times={}
                for mode,cls in (('native',LazyBinaryClosureSolver),('observed',GuardProbeObserver)):
                    path=temp/mode;tick=time.perf_counter();restore_archive(reference['prefix_archive'],path);restore_seconds=time.perf_counter()-tick
                    tick=time.perf_counter();s=cls(path,node_limit=256,handoff_bytes=2*1024*1024,**(dict(templates=templates) if mode=='observed' else {}));setup_seconds=time.perf_counter()-tick
                    try:
                        tick=time.perf_counter();result=attempt(s,source);solve_seconds=time.perf_counter()-tick
                        rows=old.tables(s.db)
                        if mode=='native':baseline=rows
                        else:
                            assert rows==baseline and (result['status'],result['metrics'])==(results['native']['status'],results['native']['metrics'])
                            observed=s.guard_report
                    finally:s.close()
                    results[mode]=result;folder=dest/mode;folder.mkdir();archives[mode]=base.archive(path,folder);path.unlink()
                    times[mode]=dict(restore_seconds=restore_seconds,setup_seconds=setup_seconds,solve_seconds=solve_seconds)
                base.write(dest/'observation.json',observed)
                tick=time.perf_counter();counts=Counter();checked=[];summary=Counter()
                for event in observed['events']:
                    analysis=analyse_event(observed['source'],templates,event,counts)
                    summary['contexts']+=1;summary['whole_residual_contexts']+=analysis['whole_residual']
                    summary['contexts_with_proposals']+=bool(analysis['candidates'])
                    assert len(event['available'])==len(analysis['candidates'])
                    for candidate,presence in zip(analysis['candidates'],event['available']):
                        assert candidate['root']==presence['root'];summary['proposals']+=1
                        candidate['present_at_event']=presence['present']
                        summary['tried' if candidate['tried'] else 'untried']+=1
                        summary['different_variable']+=candidate['different_variable']
                        summary['unit_conflicts' if candidate['node'] is not None else 'unit_inconclusive']+=1
                        if candidate['node'] is not None:
                            assert not presence['present'] or presence['answer'] is False
                            summary['untried_unit_conflicts']+=not candidate['tried']
                            summary['different_variable_unit_conflicts']+=candidate['different_variable']
                            summary['untried_absent_unit_conflicts']+=not candidate['tried'] and not presence['present']
                            bank._store(candidate['root'],candidate['node'])
                    checked.append(analysis)
                analysis_seconds=time.perf_counter()-tick
                base.write(dest/'checked.json',checked);base.write(dest/'results.json',results)
                r=dict(origin=origin,target=origin+1,source_report=old.binding(ORIGINS/f'origin-{origin}/report.json'),
                    observation=old.binding(dest/'observation.json'),checked=old.binding(dest/'checked.json'),results=old.binding(dest/'results.json'),
                    archives=archives,times=times,analysis_seconds=analysis_seconds,counts=dict(counts),summary=dict(summary),
                    native_digest={t:base.key_sha(base.encode(sorted(entries.items()))) for t,entries in baseline.items()})
                base.write(dest/'report.json',r);reports.append(old.binding(dest/'report.json'))
                print('target',origin+1,dict(summary),flush=True)
        finally:bank.close()
        folder=out/'conditional';folder.mkdir();archive=base.archive(bankpath,folder)
    base.write(out/'report.json',dict(protocol=old.binding(out/'protocol.json'),targets=reports,conditional_archive=archive,seconds=time.perf_counter()-began))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
