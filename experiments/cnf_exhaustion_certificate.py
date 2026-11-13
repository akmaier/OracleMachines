"""Self-contained source-bound evidence that single-variable UP cannot refute.

This certificate concerns one explicit normalized CNF. It says nothing about
SAT/UNSAT, stronger inference, or coverage of another formula. It contains no
inventory lookups: the formula and both clear traces for each binary variable
are sufficient, because all other variables cannot start unit propagation.
"""
from collections import Counter
import copy
import hashlib

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_exhaustion import no_unit_triggers,certify_exhaustion

FORMAT='source-unit-exhaustion-v1'


def check_certificate(certificate,*,expected_cnf=None,counts=None):
    counts=Counter() if counts is None else counts
    if (type(certificate) is not dict or set(certificate)!={'format','cnf','attempts'}
            or certificate['format']!=FORMAT or type(certificate['cnf']) is not list
            or any(type(c) is not list for c in certificate['cnf'])
            or type(certificate['attempts']) is not list):
        raise ValueError('Invalid exhaustion certificate format')
    cnf=certificate['cnf'];attempts=certificate['attempts']
    no_unit_triggers(cnf,[],counts)
    if expected_cnf is not None and encode(cnf)!=encode(expected_cnf):
        raise ValueError('Exhaustion evidence belongs to another exact source')
    binary=sorted({abs(l) for c in cnf if len(c)==2 for l in c})
    if any(type(a) is not dict or 'variable' not in a or 'value' not in a for a in attempts):
        raise ValueError('Missing exhaustion assumption')
    if [(a['variable'],a['value']) for a in attempts]!=[(v,b) for v in binary for b in (False,True)]:
        raise ValueError('Require exactly two clear traces per binary variable')
    checked,outside=certify_exhaustion(cnf,attempts,counts)
    return dict(cnf_sha256=hashlib.sha256(encode(cnf).encode()).hexdigest(),clauses=len(cnf),
        variables=len(checked)+len(outside),checked_attempts=len(attempts),binary=checked,outside=outside,
        conclusion='No single-variable assignment yields a unit-propagation refutation.')


def make_certificate(cnf,attempts):
    selected={}
    for attempt in attempts:selected.setdefault((attempt['variable'],attempt['value']),attempt)
    binary=sorted({abs(l) for c in cnf if len(c)==2 for l in c})
    needed=[(v,b) for v in binary for b in (False,True)]
    if any(pair not in selected for pair in needed):raise ValueError('Missing binary-variable trace')
    certificate=dict(format=FORMAT,cnf=[list(c) for c in cnf],attempts=copy.deepcopy([selected[pair] for pair in needed]))
    check_certificate(certificate,expected_cnf=cnf)
    return certificate
