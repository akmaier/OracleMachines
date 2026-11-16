#!/usr/bin/env python3
"""Fresh-process lifecycle control, including bookkeeping and cold archiving."""
from pathlib import Path
import resource
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_nested_refinement as study
base=study.base


def run(parent,mode):
    if mode not in study.MODES:raise ValueError('Unknown workflow')
    out=parent/'lifecycle'/mode;out.mkdir(parents=True,exist_ok=False)
    protocol=base.load(parent/'protocol.json');expected=base.load(parent/f'{mode}-0/report.json')
    started=time.perf_counter();summary=study.stream(out/'run',protocol,mode)
    stream_seconds=time.perf_counter()-started
    actual=base.load(out/'run/report.json')
    for key in ('closed','covered','entered','stored','probes','assumptions','pattern_digest','pair_digest'):
        assert summary[key]==expected['summary'][key],key
    for a,b in zip(actual['samples'],expected['samples'],strict=True):
        current=base.load(a['path']);old=base.load(b['path'])
        assert current['archive']['database_sha256']==old['archive']['database_sha256']
        assert current['coverage']==old['coverage']
        assert current['operations']==old['operations']
    accounted=sum(summary[k] for k in ('startup_seconds','operation_seconds','cold_seconds','compression_seconds'))
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result=dict(parent_report_sha256=base.sha(parent/'report.json'),source_sha256=base.sha(__file__),mode=mode,
        stream_report=dict(path=str(out/'run/report.json'),sha256=base.sha(out/'run/report.json')),
        stream_wall_seconds=stream_seconds,phase_seconds={k:summary[k] for k in
            ('startup_seconds','operation_seconds','cold_seconds','compression_seconds')},
        other_bookkeeping_seconds=stream_seconds-accounted,peak_rss_raw=peak,
        peak_rss_unit='bytes' if sys.platform=='darwin' else 'KiB' if sys.platform.startswith('linux') else 'platform-dependent',
        platform=sys.platform,identical_batch_databases_proofs_and_operations=True,
        notes=['One supplemental run per fresh process, not included in the paired local timing means.',
               'Stream timer includes restoring/checking history, planning, acquisition, graph proofs, row audits, serializing reports, every archive and cold replay.',
               'Interpreter/import startup and this final resource report are outside the stream timer. Peak RSS includes imports and all phases.',
               'The residual time contains other bookkeeping and timer boundaries; it is not inferred recognition work.',
               'This is peak process memory, not isolated live-cache overhead or an asymptotic space bound.'])
    base.write(out/'resources.json',result)
    print(base.encode({k:result[k] for k in ('mode','stream_wall_seconds','other_bookkeeping_seconds','peak_rss_raw','peak_rss_unit')}),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]),sys.argv[2])
