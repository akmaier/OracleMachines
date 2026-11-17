#!/usr/bin/env python3
"""Run the frozen comparison/checker with reusable, exclusively owned temp loads.

The original runner reuses initial/final/arm names after closing their readers;
the frozen restore helper opens destinations exclusively. Preserve the incomplete
run, and refresh only paths successfully restored earlier in this invocation.
No previously existing destination or preserved experiment file is removed.
"""
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_terminal_first as study
from experiments.validate_cnf_terminal_first import validate


@contextmanager
def owned_restores():
    restore=study.base.restore_archive;owned=set()
    def refresh(entry,path):
        path=Path(path)
        if path in owned and path.exists():path.unlink()
        result=restore(entry,path);owned.add(path);return result
    with patch.object(study.base,'restore_archive',refresh):yield


if __name__=='__main__':
    mode=sys.argv[1];out=Path(sys.argv[2]);assert mode in ('compare','validate')
    with owned_restores():
        if mode=='compare':
            study.FILES=study.FILES+('experiments/run_cnf_terminal_first.py',)
            study.run(out)
        else:validate(out)
