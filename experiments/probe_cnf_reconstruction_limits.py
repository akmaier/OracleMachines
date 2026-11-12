#!/usr/bin/env python3
"""Reproduce isolated reconstruction-cache controls into a new output file."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_indexed_check import IndexedCheckInventory
from experiments.cnf_shared_reconstruction import SharedReconstructionInventory
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_retained_plans import sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('budget','sharing'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    source=Path('experiments/results/cnf-prepared-probes-full/report.json')
    report=json.loads(source.read_text());rows=[];reference=None
    modes=([(IndexedCheckInventory,dict(checked_reconstruction_units=n)) for n in (32768,1048576)]
           if args.mode=='budget' else [(cls,{}) for cls in
               (PreparedProbeInventory,IndexedCheckInventory,SharedReconstructionInventory)])
    with tempfile.TemporaryDirectory() as tmp:
        seed=Path(tmp)/'seed.db'
        with gzip.open(report['seed']['path'],'rb') as src,seed.open('wb') as dst:
            shutil.copyfileobj(src,dst)
        assert sha(seed)==report['seed']['database_sha256']
        for i,(cls,extra) in enumerate(modes):
            path=Path(tmp)/str(i);shutil.copyfile(seed,path)
            h=cls(path,**report['options'],**extra);found=h.inspect(report['cases'][1194]['source'])
            signature=encode([found['root'],found['profile'],found['summary']])
            if reference is None:reference=signature
            assert signature==reference
            rows.append(dict(mode=cls.__name__,options=extra,seconds=found['seconds'],
                             metrics=found['metrics'],prepared_metrics=found['prepared_metrics'],
                             summary=found['summary'],
                             state=h.sharing_state() if cls is SharedReconstructionInventory else
                                   h.reconstruction_state() if cls is IndexedCheckInventory else None))
            h.close()
    args.output.write_text(json.dumps(dict(case=1194,input_report_sha256=sha(source),rows=rows,
        limitations=['One isolated cold-cache source; ordered diagnostic, not a full performance comparison',
                     'Old preparation remains charged; source index and memo limits are logical slots, not bytes']),indent=2)+'\n')


if __name__=='__main__':main()
