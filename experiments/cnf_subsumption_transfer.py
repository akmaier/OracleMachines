"""Propose exact reuse after signed subsumption, before fresh recognition.

This index proves an equivalence to a supplied template, not its tractability or
SAT value. A caller must separately check the template's complete positive proof.
The only renamings recognized are those exposed by sorted-variable normalization.
"""
from collections import Counter
import json

from experiments.cnf_anchored_subsets import anchored_certificate, check_anchored_subsumption
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import normalize, holds

FORMAT = 'signed-subsumption-transfer-v1'


def minimal(source, counts):
    normalized, outer = normalize(source, counts)
    certificate = anchored_certificate(normalized, counts)
    core, names = normalize([normalized[i] for i in certificate['kept']], counts)
    return core, certificate, [outer[v-1] for v in names]


def checked_minimal(source, certificate, counts):
    normalized, outer = normalize(source, counts)
    kept = check_anchored_subsumption(normalized, certificate, counts)
    core, names = normalize(kept, counts)
    return core, [outer[v-1] for v in names]


class CoreIndex:
    """Immutable candidate data; successful lookup still needs proof checking."""
    def __init__(self, templates, counts=None):
        self.counts = Counter() if counts is None else counts
        self._templates = {}
        self._by_core = {}
        for key, source in templates.items():
            if type(key) is not str:
                raise ValueError('Template identity must be explicit')
            # A value snapshot prevents subsequent caller mutation of the index.
            source = json.loads(encode(source))
            core, certificate, names = minimal(source, self.counts)
            identity = encode(core)
            self.counts['template_core_key_bytes'] += len(identity.encode())
            self._templates[key] = source
            self._by_core.setdefault(identity, []).append((key, certificate, names))

    def lookup(self, source, counts=None):
        counts = Counter() if counts is None else counts
        core, certificate, names = minimal(source, counts)
        identity = encode(core)
        counts['query_core_key_bytes'] += len(identity.encode())
        counts['core_lookups'] += 1
        candidates = self._by_core.get(identity, ())
        if not candidates:
            counts['core_misses'] += 1
            return None
        key, target_certificate, target_names = candidates[0]
        counts['core_hits'] += 1
        return json.loads(encode(dict(format=FORMAT, target=key,
            query_subsumption=certificate, template_subsumption=target_certificate,
            query_names=names, template_names=target_names)))


def check_transfer(source, template, expected_key, certificate, counts=None):
    """Check both reductions and exact name maps; a similarity hit is insufficient."""
    counts = Counter() if counts is None else counts
    if (type(certificate) is not dict or set(certificate) !=
            {'format', 'target', 'query_subsumption', 'template_subsumption',
             'query_names', 'template_names'} or certificate['format'] != FORMAT
            or certificate['target'] != expected_key or type(expected_key) is not str):
        raise ValueError('Invalid subsumption transfer fields or target')
    a, a_names = checked_minimal(source, certificate['query_subsumption'], counts)
    b, b_names = checked_minimal(template, certificate['template_subsumption'], counts)
    if (a != b or encode(certificate['query_names']) != encode(a_names)
            or encode(certificate['template_names']) != encode(b_names)):
        raise ValueError('Different reduced formulas or incorrect variable transport')
    counts['verified_subsumption_transfers'] += 1
    return list(zip(b_names, a_names, strict=True))


def lift_transfer(source, template, expected_key, certificate, template_model):
    mapping = check_transfer(source, template, expected_key, certificate)
    support = {abs(l) for c in template for l in c}
    if (type(template_model) is not dict
            or any(type(template_model.get(v)) is not bool for v in support)
            or not holds(template, template_model)):
        raise ValueError('Invalid model of the proved template')
    result = {abs(l): False for c in source for l in c}
    result.update((target, template_model[old]) for old, target in mapping)
    if not holds(source, result):
        raise ValueError('Subsumption transfer model does not satisfy source')
    return result
