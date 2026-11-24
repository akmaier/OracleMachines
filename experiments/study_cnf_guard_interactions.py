#!/usr/bin/env python3
"""Census binary interactions of guard consequences at saved local residuals."""
from collections import Counter
from pathlib import Path
import json,resource,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_certificates as previous
from experiments.cnf_guard_interactions import local_hints,inspect,compile_path
from experiments.cnf_hint_transport import CoreHintStore
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_partial_residual_pool import charge
from experiments.cnf_fresh_mixtures import attempt
from experiments import cnf_residual_dag as native
base=previous.base;old=previous.old
PARENT=Path('experiments/results/cnf-guard-certificate-reuse')
CENSUS=Path('experiments/results/cnf-guard-probe-census')
FILES=('experiments/cnf_guard_interactions.py','solver/test_cnf_guard_interactions.py','experiments/study_cnf_guard_interactions.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    parent=base.load(PARENT/'checkpoint.json');prior=base.load(PARENT/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        targets=prior['targets'],inputs=[old.binding(CENSUS/f'target-{t}/report.json') for t in prior['targets']],
        compile_per_context=2,compile_per_target=16,path_limit=256,baseline_node_limit=256,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
            'All 648 saved ordinary-probe contexts from eight exposed edits are inspected. Earlier origin acquisition and passive context capture are additional costs; no later repeats or cumulative history seed discovery or compilation.',
            'Each compatible source template is transported under the fixed context only if all surviving support clauses occur in the actual local CNF. Its negated remaining guard is checked by the existing exact-core RUP checker.',
            'All guard widths are recorded. Reachability closes only the width-at-most-two fragment, compared with original binary clauses, guard clauses alone and their union. The learned graph is a necessary condition, not an exact replacement of the whole CNF.',
            'Candidates are forced literals absent from original binary closure and direct unit guards. Selected witnesses must use a new binary guard clause; choose chronological contexts, mixed witnesses first, then literal order, at most two per context and sixteen per target.',
            'Each selected candidate has one cold native acquisition and one cold proof-compilation pair with empty stores. Transport uses provisioned templates; matching, preparation and persistence are separately charged, not omitted from the study. One pair is diagnostic, not a reliable speedup estimate.',
            'Path compilation uses saved unit leaves and existing native split nodes, without SAT search. Conservative leaf misses use the existing small-support materializer, with its propagation charged. Every native publication is checked.',
            'All accepted RUP hints and both arms\' retained native rows are preserved separately. Warm and cold replay include full checks. Graph components need not be independent source components; support overlaps and source components are recorded.',
            'Limits bound selected certificates and path length only, not total candidate discovery, normalization, RUP checking, graph memory or the lifetime proof archive. No live policy, new whole-input performance result or unrestricted polynomial SAT bound.']))


def run(out):
    p=base.load(out/'protocol.json');began=time.perf_counter();reports=[]
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);hintpath=temp/'hints';nativepath=temp/'native'
        hints_store=CoreHintStore(hintpath);bank=native.ResidualSolver(nativepath)
        try:
            for target,binding in zip(p['targets'],p['inputs']):
                parent=old.bound(binding);observation=old.bound(parent['observation'])
                origin=old.bound(parent['source_report']);templates=old.bound(origin['extraction'])['templates']
                dest=out/f'target-{target}';dest.mkdir();records=[];c=Counter();totals=Counter();selected=0
                timings=Counter();tick=time.perf_counter();bank_bytes=charge(templates);timings['bank_account_seconds']=time.perf_counter()-tick
                for event_index,event in enumerate(observation['events']):
                    tick=time.perf_counter();local,hs,whole=local_hints(observation['source'],templates,event,c)
                    r=inspect(local,hs,c);timings['discovery_seconds']+=time.perf_counter()-tick
                    tick=time.perf_counter()
                    for h in hs:hints_store.put(local,h['clause'],h['proof'])
                    timings['hint_persist_seconds']+=time.perf_counter()-tick
                    profiles=r['profiles'];combined=profiles['combined'];original=set(map(tuple,profiles['original']['clauses']))
                    new_binary={tuple(h['clause']) for h in hs if len(h['clause'])==2}-original
                    candidates=[lit for lit in r['new_candidates'] if any(tuple(combined['clauses'][cid]) in new_binary for _,cid in combined['paths'][lit])]
                    candidates.sort(key=lambda lit:(lit not in r['mixed'],lit))
                    results=[]
                    for forced in candidates[:min(p['compile_per_context'],p['compile_per_target']-selected)]:
                        path=combined['paths'][forced]
                        if len(path)>p['path_limit']:totals['path_limit_skips']+=1;continue
                        selected+=1;raw=native.restrict_scan(local,{abs(forced):forced<0},c);pair={}
                        for mode in ('compile','fresh') if selected%2 else ('fresh','compile'):
                            tick=time.perf_counter();s=native.ResidualSolver() if mode=='compile' else LazyBinaryClosureSolver(node_limit=p['baseline_node_limit'])
                            cc=Counter()
                            try:
                                if mode=='compile':
                                    root=compile_path(s,local,hs,combined,forced,cc,path_limit=p['path_limit']);node=s._read(root)
                                    assert node is not None and node['answer'] is False
                                    result=dict(status='unsat',root=root,counts=dict(s.counts),composition_counts=dict(cc))
                                else:
                                    got=attempt(s,raw);assert got['status'] in ('unsat','unresolved')
                                    result=dict(status=got['status'],root=None if got['result'] is None else got['result']['root'],counts=dict(s.counts),composition_counts={})
                                elapsed=time.perf_counter()-tick
                                rows=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY rowid'))
                                result.update(seconds=elapsed,nodes=len(rows),checked_bytes=charge(s.checked),payload_bytes=sum(len(k.encode())+len(v.encode()) for k,v in rows))
                                tick=time.perf_counter()
                                for k,payload in rows:bank._store(k,json.loads(payload))
                                timings['native_preserve_seconds']+=time.perf_counter()-tick
                            finally:s.close()
                            pair[mode]=result;timings[mode+'_seconds']+=elapsed
                        if pair['fresh']['root'] is not None:assert pair['compile']['root']==pair['fresh']['root']
                        results.append(dict(forced=forced,mixed=forced in r['mixed'],path=path,comparison=pair))
                    totals['contexts']+=1;totals['whole_contexts']+=whole;totals['accepted_hints']+=len(hs)
                    totals['unique_guard_clauses']+=len(r['guards']);totals['contexts_with_hints']+=bool(hs)
                    totals['multi_assumption_candidates']+=len(candidates);totals['contexts_with_multi_candidates']+=bool(candidates)
                    for k in ('guard_composed','mixed','new_candidates'):totals[k]+=len(r[k])
                    totals['guard_components']+=r['guard_components'];totals['support_overlap_pairs']+=r['support_overlap_pairs']
                    for mode,profile in profiles.items():totals[mode+'_contradictory_contexts']+=bool(profile['contradictory']) or profile['empty']
                    records.append(dict(event=event_index,root=event['root'],whole=whole,hints=hs,analysis=r,multi_candidates=candidates,selected=results))
                base.write(dest/'records.json',records)
                report=dict(target=target,input=binding,records=old.binding(dest/'records.json'),counts=dict(c),summary=dict(totals),
                    timings=dict(timings),selected=selected,bank_bytes=bank_bytes,record_graph_bytes=charge(records))
                base.write(dest/'report.json',report);reports.append(old.binding(dest/'report.json'));print(target,dict(totals),'selected',selected,flush=True)
            tick=time.perf_counter();hint_rows=list(hints_store.db.execute('SELECT payload FROM cnf_core_hints_v1'))
            for payload, in hint_rows:
                r=json.loads(payload);assert hints_store.get(r['core'],r['clause'])==r['proof']
            for key, in bank.db.execute('SELECT id FROM cnf_residual_v1'):assert bank._read(key) is not None
            warm_seconds=time.perf_counter()-tick;storage=hints_store.storage();native_nodes=bank.db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0]
            hint_counts=dict(hints_store.counts);native_counts=dict(bank.counts)
        finally:hints_store.close();bank.close()
        tick=time.perf_counter();cold=CoreHintStore(hintpath);reader=CanonicalVerifySnapshot(nativepath)
        try:
            hint_audit=cold.audit()
            for key, in reader.db.execute('SELECT id FROM cnf_residual_v1'):assert reader._read(key) is not None
        finally:cold.close();reader.close()
        cold_seconds=time.perf_counter()-tick
        (out/'hints').mkdir();(out/'native').mkdir()
        archives=dict(hints=base.archive(hintpath,out/'hints'),native=base.archive(nativepath,out/'native'))
    base.write(out/'report.json',dict(protocol=old.binding(out/'protocol.json'),targets=reports,archives=archives,
        hint_storage=storage,hint_counts=hint_counts,native_counts=native_counts,native_nodes=native_nodes,
        hint_audit=hint_audit,warm_seconds=warm_seconds,cold_seconds=cold_seconds,
        complete_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='run':run(Path(sys.argv[2]))
