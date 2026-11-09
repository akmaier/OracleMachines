# Checked Horn renaming at exhausted discovery leaves

Implemented 9 November 2026 in `experiments/cnf_polarity_horn.py`. The established
renamable-Horn class provides a concrete extension to structural coverage: all
35 positive certificates in the previous 148-leaf frontier now become checked
terminal edges. Source-level gains and total costs require ancestor recomposition;
they must not be equated with this leaf count.

## Recognition and the exact transformation

Let F be a normalized CNF, with distinct literals within each non-tautological
clause. Associate a Boolean flip variable x_v with each original variable v.
For every pair of literals a,b in a clause, add (a OR b) to an auxiliary 2-CNF,
interpreting its variables as flips. A positive original literal remains positive
exactly when its flip is false; a negative literal becomes positive exactly when
its flip is true. Thus (a OR b) on flips prohibits both original occurrences from
becoming positive. All pair clauses hold if and only if the transformed CNF is
Horn. Unit and empty clauses impose no pair constraint. Variables absent from
pairs can keep their original polarity.

The characterization and efficient recognition of this class are established;
see [Mannila and Mehlhorn (1985)](https://people.mpi-inf.mpg.de/~mehlhorn/ftp/RenamingHorn.pdf).
Our implementation explicitly materializes pairs and uses the existing 2-CNF SCC
solver. It does **not** implement that paper's faster implicit graph algorithm.

The recognizer emits one of three checked outcomes:

- **Recognized:** sorted variable flips. The checker constructs the transformed
  clauses directly, requires at most one positive literal in each, binds the exact
  normalized child and verifies its Horn closure. It never reruns SCC discovery.
- **Excluded:** two implication paths from x_v to its negation and back. Every
  edge names two literal positions in an original source clause. The checker
  verifies those coordinates, signs and path endpoints. These paths refute the
  auxiliary formula and exclude renamable-Horn membership. They say nothing by
  themselves about satisfiability of F.
- **Unresolved:** the pair count exceeds the fixed 65,536-pair limit. The count
  is calculated before quadratic enumeration. A cap is never an exclusion proof.

All earlier recognition, simplification, probing, subsumption and conditioning
priorities are retained. This additional test runs only on exhausted unresolved
nodes. It is a terminal policy extension, not a new globally evaluated coordinate
in every overlap profile. A future whole-profile recognizer must make its extra
recognition and overlap costs explicit. Recursion at the same depth and support
terminates because the transformed child is Horn and closes before fallback.

## Model transport and proof boundary

For a set S of flipped variables, let R_S change their literal signs and T_S
complement those coordinates of a valuation. Evaluation satisfies
`R_S(F)(u) = F(T_S(u))`, and `T_S(T_S(u)) = u`. This bijection proves both SAT
and UNSAT preservation. After normalization, child names first map local variable
indices back to parent names, then T_S restores the original signs. The Python
lift requires a complete Boolean child model and checks the original CNF again.

Lean proves `flipValuation_involutive`, `polarity_rename_eval`,
`satisfiable_polarity_rename` and `unsatisfiable_polarity_rename`, using the existing
signed-substitution semantics. These lemmas establish semantic transport. They
do not verify the pair reduction, Python SCC code, signed-integer encoding,
normalization, SQLite or machine-level resource costs.

## Persistence and invalidation

The configuration contains `terminal_polarity=horn-pair-certificates-v1` and the
pair limit. Both participate in node and source keys. Old policies and rows stay
valid and are preserved; this policy acquires separately keyed rows, including
unchanged structural nodes. Separate new archives are therefore additional
storage while historical archives remain retained. Old/new policy coexistence
is tested on a small database; full combined-database growth needs measurement.

Positive and negative certificates are source-local. A changed clause, sign,
coordinate, policy, edge name or child key must be checked against the new source.
No negative recognition result is reused as an original UNSAT answer. Failed
attempts and cap results persist with the unresolved node. A cold load checks the
old failure obligations before the polarity certificate and child binding.

## Resource account

Write m for clauses, L for literal occurrences, v for distinct variables and
Q = sum_C binomial(|C|,2). With expected constant-time integer maps and sets,
source validation/counting uses O(m+L) work and O(v+max|C|) temporary words.
Below the cap, explicit pair construction and SCC/path discovery use
O(m+L+Q+v log(v+1)) word/comparison operations and O(m+L+Q+v) temporary words,
including transformed output. Sorting occurs in variable enumeration and flip
lists. Above the cap there is no pair allocation. These are conditional word
bounds; long integer, hashing and bit-encoding costs remain additional.

Positive checking uses O(m+L+v log(v+1)) work for source validation, sorted flips
and transformation, plus normalization, family checking and the existing
acquisition stack. Negative checking uses O(m+L+p) work for p supplied path
edges. The discovery routine's two simple paths each have at most 2v-1 edges;
the checker charges the actual p supplied, including longer repeated paths.
Positive certificates contain O(v) identifiers; generated negative certificates
contain O(v) source-coordinate tuples. Bit size includes identifier and index
widths. The full auxiliary pair formula is not persisted. The transformed child,
its key, original source and prior failed attempts still consume space.

Across acquired terminal leaves i, sum these costs over their distinct sources,
plus every replay/check not served by existing validated caches. Earlier failed
search and alternatives are paid first. Neither the 65,536-pair cap nor this
polynomial class recognizer bounds the total number of residuals for arbitrary
SAT. This remains a structural discovery layer alongside the unchanged complete
decision solver; better closure counts alone are not decision-engine speedups.

## Validation

Eight new tests cover 3,816 exhaustive normalized formulas (all two-variable
formulas and all three-variable formulas with at most three clauses), brute-force
flip membership and model equivalence; all 148 saved leaves; every branch of
512 tiny inventory trees; 120 fresh random/edited mixtures; signed and reordered
transfers; cap behavior; malformed certificates and child edges; cold replay and
preservation of prior policy rows. A satisfiable non-renamable example explicitly
checks the distinction between auxiliary UNSAT and original SAT. Monkeypatching
the SCC routine to fail during certificate replay confirms checking is independent
of rediscovery. The complete Python suite passes all 441 tests.

The matched comparison is `experiments/compare_cnf_polarity_horn.py`. It preserves
all 1,497 prior inputs and ordinary answers, computes selected ancestor coverage,
checks every acquired polarity edge against independently solved endpoints,
retains the complete new archive, and measures warm and cold reconstruction.
The [completed full study](../experiments/results/cnf-polarity-horn/README.md)
closes 29 additional sources (869/985 -> 898/985), with 87 sources and 106 selected
leaves remaining. All 106 have checked negative class certificates. Single-run
discovery falls 4.95%, fresh archive size 4.63%, while warm replay regresses. The
full report preserves every counter, root gain, archive and limitation.
