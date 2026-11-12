#!/usr/bin/env python3
"""Count exact-equal immutable sources across different reconstruction objects."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_indexed_check import CheckedReconstruction, IndexedCheckInventory
from experiments.compare_cnf_retained_plans import sha


class ObservedReconstruction(CheckedReconstruction):
    def __init__(self):
        super().__init__(16777216)
        self.by_value={}
        self.identities=set()
        self.calls=0

    def __call__(self,cnf,assigned,counts,*,units):
        result=super().__call__(cnf,assigned,counts,units=units)
        entry=self._entries.get(id(cnf))
        if entry is not None and entry.cnf is cnf:
            self.calls+=1
            self.identities.add(id(cnf))
            self.by_value.setdefault(cnf,set()).add(id(cnf))
        return result


def main(output):
    if output.exists():raise FileExistsError(output)
    source=Path('experiments/results/cnf-prepared-probes-full/report.json')
    report=json.loads(source.read_text());observer=ObservedReconstruction()
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'seed.db'
        with gzip.open(report['seed']['path'],'rb') as src,path.open('wb') as dst:
            shutil.copyfileobj(src,dst)
        assert sha(path)==report['seed']['database_sha256']
        h=IndexedCheckInventory(path,**report['options'])
        h._checked_reconstruction=observer;h.prepared._checked_reconstruction=observer
        r=h.inspect(report['cases'][1194]['source'])
        counts=Counter(r['metrics'])+Counter(r['prepared_metrics'])
        assert not counts['indexed_check_evictions']
        assert len(observer.identities)==observer.state()['entries']
        histogram=Counter(len(ids) for ids in observer.by_value.values())
        data=dict(case=1194,input_report_sha256=sha(source),script_sha256=sha(Path(__file__)),
            calls=observer.calls,distinct_identities=len(observer.identities),
            distinct_structural_values=len(observer.by_value),
            equal_value_new_identities=len(observer.identities)-len(observer.by_value),
            identities_per_value_histogram=dict(sorted(histogram.items())),
            indexed_hits=counts['indexed_check_hits'],evictions=counts['indexed_check_evictions'],
            index_state=observer.state(),root_sha256=hashlib.sha256(r['root']['key'].encode()).hexdigest(),
            summary=r['summary'],instrumented_seconds=r['seconds'],
            limitations=['One isolated prepared source; exact tuple equality, not semantic equivalence or renamed-core matching',
                         'Observer retains values and identities for analysis; its extra space and timing are not an optimization',
                         'No evictions: the retained source objects cannot recycle their identities during the observation',
                         'An interner must still pay hashing, equality, admission and memory costs; potential sharing is not an established speedup'])
        h.close()
    output.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))


if __name__=='__main__':main(Path(sys.argv[1]))
