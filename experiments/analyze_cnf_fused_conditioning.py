#!/usr/bin/env python3
"""Check contraction of every archived OR plan and account for fused evidence."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from analyze_cnf_conditioning import load_nodes


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))


def shape_key(node):
    return encode([node['depth'],node['cnf']])


def statistics(nodes):
    counts, sizes = Counter(), Counter()
    fused = traces = units = pure = 0
    for key,node in nodes.items():
        counts[node['kind']] += 1
        sizes[node['kind']] += len(key.encode())+len(encode(node).encode())
        if node['kind']=='or':
            for a in node['alternatives']:
                for edge in a['edges']:
                    if 'closure' in edge:
                        fused += 1;traces += len(encode(edge['closure']).encode())
                        units += len(edge['closure']['units'])
                        pure += sum(map(len,edge['closure']['pure_rounds']))
    return dict(node_kinds=dict(counts),logical_node_bytes=dict(sizes),fused_edges=fused,
                closure_json_bytes=traces,unit_trace_entries=units,pure_trace_entries=pure)


def compare_plans(old,new):
    old_index={shape_key(n):n for n in old.values()};new_index={shape_key(n):n for n in new.values()}
    assert len(old_index)==len(old) and len(new_index)==len(new)
    assert {k for k,n in old_index.items() if n['kind']!='simplify'} == {k for k,n in new_index.items() if n['kind']!='simplify'}
    checked = fused = 0;intermediates=set()
    for sk,node in old_index.items():
        if node['kind']!='or':continue
        replacement=new_index[sk]
        assert node['profile']==replacement['profile'] and node['selected']==replacement['selected']
        assert node['summary']==replacement['summary']
        assert len(node['alternatives'])==len(replacement['alternatives'])
        for a,b in zip(node['alternatives'],replacement['alternatives']):
            assert a['variable']==b['variable'] and a['summary']==b['summary']
            for e,f in zip(a['edges'],b['edges']):
                target=old[e['key']]
                if target['kind']=='simplify':
                    assert f['closure']==target['profile']['simplification']['certificate']
                    assert f['names']==[e['names'][v-1] for v in target['edge']['names']]
                    intermediates.add(e['key']);fused+=1
                    target=old[target['edge']['key']]
                else:
                    assert 'closure' not in f and e['names']==f['names']
                assert shape_key(target)==shape_key(new[f['key']])
        checked+=1
    return dict(checked_or_plans=checked,contracted_edges=fused,
                distinct_old_intermediates=len(intermediates),
                retained_intermediates=sum(shape_key(old[k]) in new_index for k in intermediates),
                all_non_simplification_cnf_depth_pairs_preserved=True)


def analyze(directory):
    report=json.loads((directory/'report.json').read_text());pairs=[]
    for old_mode,new_mode in (('frequency','fused_frequency'),('shortest','fused_shortest'),('combined','fused_combined')):
        old=load_nodes(directory,next(a for a in report['archives'] if a['mode']==old_mode))
        new=load_nodes(directory,next(a for a in report['archives'] if a['mode']==new_mode))
        pairs.append(dict(baseline=old_mode,fused=new_mode,old_stats=statistics(old),new_stats=statistics(new),
                          exact_plan_check=compare_plans(old,new)))
    aggregates={}
    for mode in report['modes']:
        rows=[r for r in report['records'] if r['mode']==mode]
        aggregates[mode]=dict(lifting_seconds=sum(r['lifting_seconds'] for r in rows),
            metrics=dict(sum((Counter(r['discovery']['metrics']) for r in rows if r['discovery']),Counter())))
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),pairs=pairs,aggregates=aggregates,
                limitations=['Exact plan comparison is corpus evidence, not a universal implementation proof',
                             'Root/source and pre-existing intermediate records are retained',
                             'Fused trace copies and reconstruction remain charged; no general constant-space claim'])


if __name__=='__main__':
    directory=Path(sys.argv[1])
    (directory/'mechanisms.json').write_text(json.dumps(analyze(directory),indent=2)+'\n')
