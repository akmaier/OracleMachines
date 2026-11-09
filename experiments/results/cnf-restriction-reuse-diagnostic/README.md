# Restriction reuse diagnostic before implementation

Collected against `ac3434ac88a4f946333d7b126f23fafc0d49f746`, using the ordered
propagation inventory on twelve fixed sources. This is instrumented acquisition,
not a runtime or memory comparison: the observer retains source objects to rule
out object-ID recycling while counting repeated identities.

On source 1194 there are 3,399 restrictions, 1,187,922 input literal visits and
426,393 input clauses. Only 40,939 clauses / 109,956 literals are touched by the
assignments. There are 3,044 repeated identical source-object calls, 277 distinct
source values, 355 distinct source objects, and 1,788 repeated source/assignment
pairs. Every observed source is an exact tuple of tuples. All twelve sources have
only immutable tuple containers in these calls.

An offline structural-key LRU with 32,768 logical units predicts 3,122 source hits
and 98,040 preparation literals for source 1194, but this is not an implementation
or timing claim. The subsequent implementation deliberately uses validated
immutable object identity, so distinct equal objects prepare separately. It also
must charge validation, output assembly and cache maintenance. The diagnostic
script and input report hashes are saved in `report.json`.
