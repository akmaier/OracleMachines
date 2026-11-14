"""Positive graph replay, separate from historical-policy validation.

Direct rules establish the selected semantic reduction, not the completeness or
ranking of the archive's proposals. Never populate the inventory's checked maps:
those maps promise the stronger historical contract. External routes and the
unconverted subsumption rule still use their original validators and caches.
"""
import json

from experiments.cnf_pattern_inventory import encode, classify
from experiments.cnf_residual_dag import components, normalize, restrict
from experiments.cnf_expanded_coverage import FORMAT, INTERNAL, owner, children
from experiments.cnf_selected_routes import SelectedRoutes
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_affine_projection import check_projection, check_boundary
from experiments.cnf_simplification import check_simplification, simplification_reconstruction
from experiments.cnf_single_pass_check import reconstruct_single_pass
from experiments.cnf_variable_elimination import check_elimination
from experiments.cnf_clause_bound_elimination import check_clause_elimination
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_binary_paths import check_binary_paths
from experiments.cnf_polarity_horn import check_polarity


class PositiveReplay:
    def __init__(self, h, evidence, counts):
        self.h, self.counts = h, counts
        self.routes = SelectedRoutes(h, evidence)
        self.justified = set()

    def read(self, source):
        """Read one untrusted row. Only its exact CNF identity is established."""
        view = owner(self.h, source)
        row = view.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (source,)).fetchone()
        self.counts['positive_sql_lookups'] += 1
        if row is None:
            raise ValueError('Missing positive source')
        self.counts['positive_node_read_bytes'] += len(row[0].encode())
        node = json.loads(row[0])
        if (type(node) is not dict or type(node.get('kind')) is not str or
                type(node.get('depth')) is not int or
                not 0 <= node['depth'] <= view.config['max_depth'] or
                type(node.get('cnf')) is not list or
                any(type(c) is not list or any(type(l) is not int or not l for l in c)
                    for c in node['cnf'])):
            raise ValueError('Invalid positive source fields')
        cnf, _, actual = view._canonical(node['cnf'], node['depth'])
        if actual != source or encode(cnf) != encode(node['cnf']):
            raise ValueError('Invalid positive source identity')
        return view, node, cnf

    def edge(self, view, edge, target, depth, outer_names=None):
        """Exact source-to-child renaming; the child needs its own earlier proof."""
        _, names, key = view._canonical(target, depth)
        if outer_names is not None:
            names = [outer_names[v-1] for v in names]
        if encode(edge) != encode(dict(key=key, names=names)):
            raise ValueError('Incorrect positive edge or variable binding')
        return key

    def simplified(self, view, cnf, certificate):
        return check_simplification(cnf, certificate, self.counts,
            units=view.config.get('simplify_units', True),
            pure=view.config.get('simplify_pure', False))[0]

    def direct_children(self, view, node, cnf, rule):
        kind, depth = node['kind'], node['depth']
        if rule == dict(kind='family') and kind == 'family':
            profile = classify(cnf, view.config['parity_width'], self.counts)
            if not any(v == 'recognized' for v in profile['outcomes'].values()):
                affine = check_affine(cnf, node['profile']['evidence']['explicit_affine'], self.counts)
                if not (affine['pure'] or affine['inconsistent']):
                    raise ValueError('No positive terminal family')
            return []
        if rule == dict(kind='retained_plan') and kind == 'retained_plan':
            if getattr(view, 'prepared', None) is None:
                raise ValueError('Missing retained policy')
            expected = view.prepared._canonical(cnf, depth)[2]
            if node['reference'] != expected:
                raise ValueError('Foreign retained source, depth or policy')
            return [expected]
        if rule == dict(kind='components') and kind == 'and':
            groups = components(cnf, self.counts)
            if len(groups) <= 1 or len(node['edges']) != len(groups):
                raise ValueError('Invalid positive component partition')
            return [self.edge(view, e, g, depth) for e, g in zip(node['edges'], groups)]
        if (rule.get('kind') == 'conditioning' and kind == 'or' and
                set(rule) == {'kind', 'index'} and type(rule['index']) is int and
                depth > 0 and 0 <= rule['index'] < len(node['alternatives'])):
            attempt = node['alternatives'][rule['index']]
            variable = attempt['variable']
            if (type(variable) is not int or variable not in {abs(l) for c in cnf for l in c}
                    or type(attempt['edges']) is not list or len(attempt['edges']) != 2):
                raise ValueError('Invalid positive conditioning variable or branches')
            result = []
            for edge, value in zip(attempt['edges'], (False, True)):
                target = restrict(cnf, {variable:value}, self.counts)
                if 'closure' in edge:
                    if set(edge) != {'key', 'names', 'closure'}:
                        raise ValueError('Invalid fused positive edge')
                    intermediate, names = normalize(target, self.counts)
                    target = self.simplified(view, intermediate, edge['closure'])
                    result.append(self.edge(view, {k:v for k,v in edge.items() if k!='closure'},
                                            target, depth-1, names))
                else:
                    result.append(self.edge(view, edge, target, depth-1))
            return result
        if rule != dict(kind='edge'):
            raise ValueError('Invalid positive internal rule')
        if kind == 'eliminate':
            limit = view.config['elimination_pair_limit']
            if 'additive_elimination' in node:
                target = check_additive_elimination(cnf, node['additive_elimination'], self.counts,
                    pair_limit=limit, clause_growth_limit=view.config['clause_growth_limit'])
            elif 'clause_elimination' in node:
                target = check_clause_elimination(cnf, node['clause_elimination'], self.counts, pair_limit=limit)
            else:
                target = check_elimination(cnf, node['elimination'], self.counts, pair_limit=limit)
            if target is None:
                raise ValueError('Missing positive elimination witness')
        elif kind == 'binary_paths':
            target = check_binary_paths(cnf, node['binary_paths'], self.counts,
                                        root_limit=view.config['binary_path_root_limit'])
            if len(target) >= len(cnf):
                raise ValueError('No positive binary deletion')
        elif kind == 'polarity':
            target = check_polarity(cnf, node['polarity'], self.counts,
                                   pair_limit=view.config['polarity_pair_limit'])
            if target is None:
                raise ValueError('No positive polarity witness')
        elif kind == 'simplify':
            target = self.simplified(view, cnf, node['profile']['simplification']['certificate'])
        elif kind == 'probe':
            # This retains all original and learned antecedent reasons and the
            # policy-specific source reconstruction, without unrelated profiles.
            probe = node['profile']['probing']
            if not view._uses_probe(dict(probing=probe)):
                raise ValueError('No positive probe rewrite')
            target, _ = view._check_probes(cnf, probe)
        elif kind == 'project':
            affine = node['profile']['evidence']['explicit_affine']
            check_affine(cnf, affine, self.counts)
            projection = node['profile']['projection']
            keep = sorted({abs(l) for i in affine['leftovers'] for l in cnf[i]})
            if encode(projection['keep']) != encode(keep):
                raise ValueError('Projection drops a coupling variable')
            check_projection(affine['equations'], keep, projection['certificate'], self.counts)
            check_boundary(projection['certificate'], projection['blocks'], self.counts)
            target = [cnf[i] for i in affine['leftovers']] + [c for b in projection['blocks'] for c in b]
        elif kind == 'subsumption':
            return None  # Keep the complete original checker for this rule.
        else:
            raise ValueError('Unsupported positive edge kind')
        return [self.edge(view, node['edge'], target, depth)]

    def verify(self, certificate, claimed_roots):
        if (type(certificate) is not dict or set(certificate) != {'format', 'roots', 'steps'} or
                certificate['format'] != FORMAT or certificate['roots'] != claimed_roots or
                type(certificate['steps']) is not list):
            raise ValueError('Invalid positive graph')
        for step in certificate['steps']:
            if (type(step) is not dict or set(step) != {'source', 'rule', 'children'} or
                    type(step['source']) is not str or type(step['children']) is not list or
                    type(step['rule']) is not dict or type(step['rule'].get('kind')) is not str):
                raise ValueError('Invalid positive step')
            source, rule = step['source'], step['rule']
            if source in self.justified:
                raise ValueError('Repeated positive step')
            view, node, cnf = self.read(source)
            if rule['kind'] in INTERNAL:
                actual = self.direct_children(view, node, cnf, rule)
                if actual is None:
                    actual = children(self.h, source, rule, self.routes)
                    self.counts['positive_legacy_internal_steps'] += 1
                else:
                    self.counts['positive_direct_internal_steps'] += 1
            else:
                if rule['kind'] == 'base' or view is not self.h:
                    raise ValueError('Invalid positive external policy or implicit base')
                self.routes.select(self.h, source, rule)
                # External validators keep their historical contract intact.
                actual = children(self.h, source, rule, self.routes)
                self.counts['positive_external_steps'] += 1
            if encode(actual) != encode(step['children']) or any(k not in self.justified for k in actual):
                raise ValueError('Missing, reordered or unproved positive premise')
            self.justified.add(source)
            self.counts['verified_positive_steps'] += 1
        if any(root not in self.justified for root in claimed_roots):
            raise ValueError('Missing positive root')


def verify_positive(h, certificate, claimed_roots, evidence, counts):
    """A sufficient hybrid positive checker, never a complete archive audit."""
    replay = PositiveReplay(h, evidence, counts)
    try:
        with simplification_reconstruction(reconstruct_single_pass):
            replay.verify(certificate, claimed_roots)
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ValueError('Malformed or missing positive evidence') from exc
    return replay
