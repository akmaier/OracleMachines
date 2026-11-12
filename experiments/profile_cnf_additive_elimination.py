#!/usr/bin/env python3
"""Profile the slowest measured additive discovery source on the paid prefix."""
import cProfile
import gzip
import json
from pathlib import Path
import pstats
import shutil
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_additive_elimination import AdditiveEliminationInventory
from experiments.compare_cnf_retained_plans import sha, check_old_rows


def main(directory):
    target=directory/'discovery-profile.json'
    if target.exists(): raise FileExistsError(target)
    report_path=directory/'report.json'; report=json.loads(report_path.read_text())
    mode=next(r for r in report['results'] if r['mode']=='add_two')
    worst=max(mode['records'],key=lambda r:r['discovery_seconds'])
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'profile.db'; seed=Path(tmp)/'seed.db'
        with gzip.open(report['seed']['path'],'rb') as src,seed.open('wb') as dst: shutil.copyfileobj(src,dst)
        assert sha(seed)==report['seed']['database_sha256']; shutil.copyfile(seed,path)
        h=AdditiveEliminationInventory(path,**mode['configuration'])
        profile=cProfile.Profile(); profile.enable()
        found=h.inspect(report['cases'][worst['case']]['source'])
        profile.disable(); storage=h.storage(); h.close()
        raw=directory/'discovery-profile.pstats'; profile.dump_stats(raw)
        functions=[]
        for (file,line,name),(primitive,calls,own,cumulative,_) in pstats.Stats(profile).stats.items():
            functions.append(dict(file=file,line=line,function=name,primitive_calls=primitive,calls=calls,
                                  own_seconds=own,cumulative_seconds=cumulative))
        preserved=check_old_rows(seed,path)
        archive=directory/'profile-add_two.sqlite3.gz'
        with path.open('rb') as src,archive.open('wb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as dst: shutil.copyfileobj(src,dst)
        result=dict(script_sha256=sha(Path(__file__)), report_sha256=sha(report_path),
            case=worst['case'], original_case=report['cases'][worst['case']]['original_case'],
            matched_query_discovery_seconds=worst['discovery_seconds'],instrumented_discovery_seconds=found['seconds'],
            summary=found['summary'],counts=found['metrics'],prepared_counts=found['prepared_metrics'],storage=storage,
            old_rows_preserved=preserved,archive_path=str(archive),archive_sha256=sha(archive),database_sha256=sha(path),
            database_bytes=path.stat().st_size,raw_profile_sha256=sha(directory/'discovery-profile.pstats'),
            top_own=sorted(functions,key=lambda r:-r['own_seconds'])[:40],
            top_cumulative=sorted(functions,key=lambda r:-r['cumulative_seconds'])[:40],
            total_diagnostic_seconds=time.perf_counter()-started,limitations=[
            'Separate instrumented single-source discovery using the paid prefix, not the acquisition history of the original ordered run.',
            'Profiler overhead is substantial; these timings are attribution evidence, not an end-to-end estimate or speed comparison.',
            'Cumulative function times overlap and must not be added. No ordinary solving is profiled.',
            'Acquired nodes are checked by inspect and retained with all old rows; no additional full cold audit is claimed for this profile archive.'])
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('case','original_case','instrumented_discovery_seconds','top_own')}))


if __name__=='__main__':main(Path(sys.argv[1]))
