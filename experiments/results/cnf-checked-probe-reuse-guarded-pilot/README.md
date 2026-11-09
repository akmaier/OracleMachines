# Guarded exact-check cache pilot

The original-attempts list guard closes the warm-cache tuple/list type alias;
all **410 tests** pass. Eight selected sources use the same inputs and budgets
as the preserved preliminary pilot. All five modes generate identical database
bytes, source/structural identities and SAT answers; every cold audit starts with
an empty cache and replays all alternatives, sources and solver certificates.

| Mode | Operation seconds | Cold replay seconds | Hits | Peak retained string bytes |
| --- | ---: | ---: | ---: | ---: |
| baseline | 3.73951 | 1.78465 | 0 | 0 |
| cache_32768 | 3.41940 | 1.49649 | 1317 | 32768 |
| cache_262144 | 3.40054 | 1.53908 | 1385 | 262142 |
| cache_1048576 | 3.21463 | 1.46211 | 1387 | 1048569 |
| cache_8388608 | 3.49702 | 1.48669 | 1387 | 2603844 |

There are 2,252 lookups in each cache mode. These selected single samples do not
establish significance or an optimal capacity. Full evaluation keeps the planned
1 MiB cap; the 256 KiB pilot has nearly the same hit count and remains a memory
tradeoff to evaluate. Logical cache bytes exclude allocator/transient memory.

The report is unchanged. Its runner fingerprint resolves to
`runner-before-validation-isolation.py`: the full runner subsequently removes
extra pointwise checks between timed queries, avoiding uncharged cache warmup.
All pilot sources have more than eight variables, so that removed branch never
ran here. Small-fiber tests and the previously checked identical archive preserve
that validation independently. All other fingerprints match current files.
