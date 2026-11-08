#!/usr/bin/env python3
"""Adopt every archived affine version by replaying original source equations."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from solver.persistent import PersistentSolver,DEFAULT_CACHE


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=DEFAULT_CACHE)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve earlier evidence; choose a new output')
    versions=[]
    with PersistentSolver(args.cache,native_affine_versions=4,query_timeout=60) as s:
        old=list(s.db.execute('SELECT DISTINCT id,answer,steps FROM affine_states WHERE engine!=? ORDER BY id',(s.engine_id,)))
        before=s.db.execute('SELECT count(*) FROM affine_states').fetchone()[0]
        for token,answer,steps in old:
            result=s.affine_grow(base=token)
            assert result['answer']==bool(answer) and result['steps']==steps
            assert result['affine_updates']['resident_versions']<=4
            versions.append(dict(state=token,answer=result['answer'],steps=steps,updates=result['affine_updates']))
        after=s.db.execute('SELECT count(*) FROM affine_states').fetchone()[0]
        native=s._request(dict(mode='affine_stats')) if old else None
    # Restart checks both positive and negative old versions, including ones
    # certainly evicted from the tiny resident set during the first pass.
    with PersistentSolver(args.cache,native_affine_versions=2,query_timeout=60) as s:
        for answer in (True,False):
            sample=next((row for row in versions if row['answer']==answer),None)
            if sample:
                result=s.affine_grow(base=sample['state'])
                assert result['answer']==answer
                sample['restart_updates']=result['affine_updates']
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                before=before,after=after,revalidated=len(versions),native_final=native,versions=versions)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='versions'}))


if __name__=='__main__':main()
