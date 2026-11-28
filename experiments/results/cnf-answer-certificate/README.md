# Answer certificate projection

This is a fixed-trace representation experiment, not a new SAT search run.
`protocol.json` freezes the preceding transfer panel, its 32 fresh/reuse traces,
the policy sources and two reversed replay orders. No historical archive is
replaced. See `research/answer-certificate-projection.md` for the proof,
measurements and limitations.

Files:

- `construction.json`: per-case projection, checking counters, separately charged
  preparation/transcode phases, certificate hashes and matched byte counts.
- `full/`, `answer/`: full and projected controls, both compact JSON with per-case
  gzip. Each answer is checked against the original target CNF.
- `comparisons.json`, `replay-*.json`: four fresh-process replays; no discovery,
  transport or projection is permitted in replay. OS caches are not flushed.
- `analysis.json`: timings and storage by original search mode and verdict.
  Its `archive_plus_answer_*` fields describe matched representations, not the
  physical size of historical indented archives. The research note separately
  accounts for those unchanged historical files and added gzip sidecars.
- `semantic-audit*.json`: reproduced independent model/ancestry audit on 7,760
  projections. `shared-ancestor-audit.json` retains a separate converging-DAG case.
- `validation.json`, `checkpoint.json`, `manifest.json`: preservation and resume
  records. The latest checkpoint key is `answer_certificate`.
- Test and LaTeX logs: the full 2,708-test suite, 11 focused tests and manuscript
  builds. The first build log is retained; final builds resolve its references.

To repeat without overwriting this immutable checkpoint, use a new directory
from the repository root and copy the frozen protocol there:

```sh
mkdir /private/tmp/oraclemachines-answer-replay
cp experiments/results/cnf-answer-certificate/protocol.json /private/tmp/oraclemachines-answer-replay/
python3 experiments/compare_cnf_answer_certificate.py construct /private/tmp/oraclemachines-answer-replay
python3 experiments/compare_cnf_answer_certificate.py run /private/tmp/oraclemachines-answer-replay
python3 experiments/validate_cnf_answer_certificate.py semantic /private/tmp/oraclemachines-answer-replay
python3 experiments/validate_cnf_answer_certificate.py semantic /private/tmp/oraclemachines-answer-replay semantic-audit-reproduced.json
python3 experiments/validate_cnf_answer_certificate.py validate /private/tmp/oraclemachines-answer-replay
```

Source fingerprints intentionally reject changed scientific code. Construction
validates the full archive even when the answer only needs its model. The
historical search/acquisition costs and storage remain additional. The primary
sixteen reused answers are unchanged; the seven unknown fresh traces stay
unknown and must not be credited as solved queries.
