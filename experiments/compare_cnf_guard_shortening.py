#!/usr/bin/env python3
"""Offline shortening census and matched local trials; no live policy changes."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cover_support as prior
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_shortening import discover,compile_program
from experiments.cnf_guard_clause_cover import discover as old_discover
from experiments.cnf_guard_interactions import local_hints
from experiments.cnf_guard_probe_census import decode_key
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_fresh_mixtures import attempt
from experiments.validate_cnf_whole_proof_reuse import audit
from solver.test_cnf_guard_shortening import chain
base=prior.base;old=prior.old
PARENT=Path('experiments/results/cnf-cover-support')
MODES=('fresh','full','support')
FILES=('experiments/cnf_guard_shortening.py','solver/test_cnf_guard_shortening.py','experiments/compare_cnf_guard_shortening.py')
LIMITS=dict(round_limit=32,root_limit=64,edge_limit=16384,path_limit=256)


def prepare(out):
    assert not (out/'protocol.json').exists();out.mkdir(parents=True,exist_ok=True)
    parent=base.load(PARENT/'checkpoint.json');p=old.bound(parent['guard_covers']['protocol']);inputs=old.bound(p['cases'])
    cases=[];records=[];seen={};began=time.perf_counter()
    for target,binding in zip(p['targets'],p['inputs']):
        source=native.normalize(inputs[target]['source'])[0]
        templates=old.bound(old.bound(binding)['extraction'])['templates']
        report=base.load(f'experiments/results/cnf-guard-covers/serial/target-{target}-census-0/report.json')
        events=old.bound(report['events'])['events'];rows=[]
        for index,event in enumerate(events):
            c=Counter();tick=time.perf_counter();local,hints,whole=local_hints(source,templates,event,c)
            bound_seconds=time.perf_counter()-tick;bound_counts=dict(c);ts=[h['template'] for h in hints]
            c=Counter();tick=time.perf_counter();program=discover(local,ts,c,**LIMITS);seconds=time.perf_counter()-tick
            graph=sorted({cl for cl in local if 1<=len(cl)<=2}|{tuple(h['clause']) for h in hints if 1<=len(h['clause'])<=2})
            model,proof=native.two_cnf(graph,Counter());oc=Counter();tick=time.perf_counter()
            cover=None if proof is not None else old_discover(local,graph,model,oc,root_limit=64,edge_limit=16384)
            old_seconds=time.perf_counter()-tick
            row=dict(target=target,event=index,source_root=event['root'],site_closed=event['site_closed'],whole_residual=whole,
                program=program,counts=dict(c),binding_counts=bound_counts,binding_seconds=bound_seconds,
                discovery_seconds=seconds,old_cover=cover,old_scc_conflict=proof is not None,
                old_cover_seconds=old_seconds,old_cover_counts=dict(oc),events=report['events'])
            if program['status']=='refuted':
                identity=base.key_sha(base.encode([local,ts]))
                if identity not in seen:
                    name=f'local-{target}-{index}';seen[identity]=name
                    case=dict(name=name,category='local',source=local,templates=ts,program=program,
                        root=event['root'],target=target,event=index,binding_seconds=bound_seconds,
                        discovery_seconds=seconds,old_cover=cover is not None,old_scc_conflict=proof is not None)
                    base.write(out/(name+'.json'),case);cases.append(old.binding(out/(name+'.json')))
                row['case']=seen[identity]
            rows.append(row)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'query';restore_archive(report['archive'],path);reader=CanonicalVerifySnapshot(path)
            try:
                aff=TerminalStore(reader);equiv=MultiEquivalenceStore(reader)
                for row in rows:
                    if row['program']['status']=='refuted':
                        root=row['source_root'];row['present_after_query']=reader._read(root) is not None or aff.read(root) is not None or equiv.read(root) is not None
            finally:reader.close()
        records.extend(rows);print(base.encode(dict(target=target,cases=len(cases),statuses=Counter(r['program']['status'] for r in rows))),flush=True)
    for depth in (1,2,4,8):
        for padding in (0,64):
            source,ts=chain(depth,padding);c=Counter();tick=time.perf_counter();program=discover(source,ts,c,**LIMITS);elapsed=time.perf_counter()-tick
            assert program['status']=='refuted';name=f'chain-{depth}-{padding}'
            case=dict(name=name,category='controlled',source=source,templates=ts,program=program,root=native.token(source,Counter()),
                discovery_seconds=elapsed,binding_seconds=0.,depth=depth,padding=padding)
            base.write(out/(name+'.json'),case);cases.append(old.binding(out/(name+'.json')))
    base.write(out/'census.json',dict(records=records,seconds=time.perf_counter()-began,
        counts=dict(Counter(r['program']['reason'] for r in records)),unique_compilation_cases=len(cases)-8))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        limits=LIMITS,cases=cases,census=old.binding(out/'census.json'),node_limit=256,orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['Offline census of all 615 saved satisfiable-graph events. Local support binding is charged separately; original template acquisition and live routing remain additional.',
        'Discovery uses a newly checked local graph, including all available supported short guards. Comparisons to old covers use that same graph and relaxed matching BFS budgets. This is not a live query rerun.',
        'Every discovered refutation configuration is compared with capped ordinary solving and full/support compilation in two alternating isolated serial repetitions. Discovery and source binding must be added to compiler cost.',
        'Eight supplied chain controls test repeated shortening and overlapping padding, not population coverage. Satisfiable deletions, unlabelled random inputs and signed renamings are checked in tests.',
        'Complete worker includes load/setup/compile/warm verification/cold replay/accounting/archive compression. Import/startup, earlier acquisition, common preparation and final validation are additional.',
        'No new native proof rule, Lean refinement, unrestricted-SAT polynomial guarantee or whole-query improvement is claimed.']))


def trial(dest,out,index,mode):
    p=base.load(out/'protocol.json');case=old.bound(p['cases'][index]);dest.mkdir();began=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';c=Counter();tick=time.perf_counter()
        s=LazyBinaryClosureSolver(path,node_limit=p['node_limit']) if mode=='fresh' else native.ResidualSolver(path)
        setup=time.perf_counter()-tick
        try:
            tick=time.perf_counter()
            if mode=='fresh':result=attempt(s,case['source'])
            else:
                root=compile_program(s,case['source'],case['templates'],case['program'],c,select_support=mode=='support')
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;stored=old.tables(s.db);native_counts=dict(s.counts)
            tick=time.perf_counter()
            if result['status']=='unsat':
                if mode!='fresh':assert compile_program(s,case['source'],case['templates'],case['program'],Counter(),select_support=mode=='support')==case['root']
                else:assert attempt(s,case['source'])['status']=='unsat'
            warm=time.perf_counter()-tick;assert old.tables(s.db)==stored
        finally:s.close()
        tick=time.perf_counter();actual,readers=audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert actual==stored
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=p['cases'][index],mode=mode,result=result,counts=dict(c),native_counts=native_counts,
        setup_seconds=setup,solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,
        complete_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        authority_tables={t:len(v) for t,v in stored.items()},digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for rows in stored.values() for k,v in rows.items()),archive=archive,cold_readers=readers))


def run(out):
    p=base.load(out/'protocol.json');samples=[];began=time.perf_counter()
    for i in range(len(p['cases'])):
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'case-{i}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),str(i),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),index=i,mode=mode,repeat=repeat))
        print(base.encode(dict(case=i,total=len(p['cases']))),flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples,seconds=time.perf_counter()-began))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trial':trial(Path(sys.argv[3]),out,int(sys.argv[4]),sys.argv[5])
    else:raise ValueError(action)
