#!/usr/bin/env python3
"""Run the frozen binary-path protocol against an early direct-only control."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_paths as protocol
from experiments.cnf_binary_direct import BinaryDirectInventory
from experiments.cnf_binary_paths import BinaryPathInventory


if __name__=='__main__':
    if '--suite' in sys.argv and sys.argv[sys.argv.index('--suite')+1]=='full':
        raise ValueError('This control uses frontier or fresh suites, not retained-full-baseline assertions')
    protocol.MODES=dict(baseline=BinaryDirectInventory,binary_paths=BinaryPathInventory)
    protocol.main()
    out=Path(sys.argv[sys.argv.index('--output')+1]);path=out/'report.json';report=json.loads(path.read_text())
    report['comparison']='early direct-only reduction versus transitive binary paths'
    for p in (Path(__file__),Path('experiments/cnf_binary_direct.py'),Path('solver/test_cnf_binary_direct.py')):
        report['fingerprints'][str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    report['limitations'].append('Mode baseline in this report means BinaryDirectInventory, not the retained PolarityHornInventory')
    path.write_text(json.dumps(report,separators=(',',':'))+'\n')
