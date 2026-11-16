#!/usr/bin/env python3
"""Separate remaining-cost diagnostic, excluded from benchmark timing means."""
import cProfile
from pathlib import Path
import pstats
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_split_registry as study
base = study.base


def run(out, parent):
    out.mkdir(exist_ok=False);protocol=base.load(parent/'protocol.json')
    seed=base.load(protocol['seed']['path']);expected=base.load(protocol['expected']['path'])
    profile=cProfile.Profile();profile.enable()
    result=study.worker(out/'incremental',protocol,seed,expected,'incremental')
    profile.disable();profile.dump_stats(str(out/'profile.pstats'))
    functions=[]
    for (path,line,name),(primitive,total,own,cumulative,callers) in pstats.Stats(profile).stats.items():
        if path.endswith('.py') and ('/experiments/' in path or name in ('dumps','loads')):
            functions.append(dict(path=path,line=line,name=name,primitive_calls=primitive,calls=total,
                                  self_seconds=own,cumulative_seconds=cumulative))
    functions.sort(key=lambda row:-row['cumulative_seconds'])
    report=dict(parent_report_sha256=base.sha(parent/'report.json'),source_sha256=base.sha(__file__),
        sample_sha256=base.sha(out/'incremental/report.json'),same_graph_pairs_proof_and_database=True,
        functions=functions,notes=['Profiler overhead excludes these times from main benchmark means.',
                                  'Cumulative times overlap and must not be added. Profile includes setup, queries, cold replay and compression.'])
    base.write(out/'report.json',report)
    print(base.encode(dict(verify_calls=result['verify_calls'],covered=result['covered'],top_functions=functions[:10])))


if __name__ == '__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
