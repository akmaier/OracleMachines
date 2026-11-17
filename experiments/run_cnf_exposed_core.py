#!/usr/bin/env python3
"""Bind the unit-exposed acquisition policy while preserving the narrow trial."""
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditioned_core as study
from experiments.cnf_exposed_core import acquire_core
from experiments.validate_cnf_exposed_core import validate


def compare(out):
    study.FILES=study.FILES+('experiments/cnf_exposed_core.py','solver/test_cnf_exposed_core.py','experiments/validate_cnf_exposed_core.py','experiments/run_cnf_exposed_core.py')
    write=study.base.write
    def bind_policy(path,value):
        if Path(path)==out/'protocol.json':
            value['cofactor_acquisition']='unit-propagation-to-two-CNF-v1'
            value['limitations']=[line.replace('or acquire a missing two-CNF certificate','or acquire a missing certificate from a unit-conflict/two-CNF residual') for line in value['limitations']]
            value['limitations'][-1]='A missing cofactor is acquired only if unit propagation refutes it or leaves a two-CNF residual. Saved traces are reused and separately charged; wider unexposed residuals are rejected. No new native proof schema or unrestricted-SAT bound.'
        return write(path,value)
    with patch.object(study,'acquire_core',acquire_core),patch.object(study.base,'write',bind_policy):study.run(out)


if __name__=='__main__':
    mode=sys.argv[1];out=Path(sys.argv[2]);assert mode in ('compare','validate')
    compare(out) if mode=='compare' else validate(out)
