"""Recheck the publication snapshot against its immutable research checkpoint.

Run from the repository root. Visual and mathematical reviews are recorded
separately below; hashes and counts alone do not establish those reviews.
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
REV = 'a6495e3d302ebf5f1557a7ae20c09b0da6c813fc'
RESEARCH = ROOT / 'experiments/results/cnf-watched-learning'
OLD = OUT.parent / '2026-11-27'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bind(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def main():
    source_path = 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    source = subprocess.check_output(['git', 'show', REV + ':' + source_path], cwd=ROOT).decode()
    snapshot = (OUT / 'oraclemachines.tex').read_text()
    old = (OLD / 'oraclemachines.tex').read_text()
    intro = r'\section{Introduction}'
    assert snapshot.split(intro, 1)[1] == source.split(intro, 1)[1]
    assert (ROOT / source_path).read_text() == source
    pattern = r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs = re.findall(pattern, snapshot, re.S)
    previous_proofs = re.findall(pattern, old, re.S)
    assert len(proofs) == 92 and len(previous_proofs) == 72
    assert proofs == re.findall(pattern, source, re.S)
    assert proofs[:72] == previous_proofs
    marker = r'\section{System 1, System 2, and the reuse of computation}'
    old_body, new_body = old.split(intro, 1)[1], snapshot.split(intro, 1)[1]
    old_prefix, old_tail = old_body.split(marker, 1)
    new_prefix, new_tail = new_body.split(marker, 1)
    assert new_prefix.startswith(old_prefix) and old_tail == new_tail
    added = new_prefix[len(old_prefix):]
    assert added.count(r'\subsection{') == 23
    assert (OUT / 'ai-disclosure.json').read_bytes() == (OLD / 'ai-disclosure.json').read_bytes()
    for required in (
        'publication revision 28 November 2026', r'\author{Andreas Maier \and GPT Astra',
        'OpenAI AI research assistant', 'https://github.com/akmaier/OracleMachines',
        'a6495e3d', 'not a proof of unrestricted',
    ):
        assert required in snapshot, required

    checkpoint = read(RESEARCH / 'checkpoint.json')
    validation = read(RESEARCH / 'validation.json')
    checks = read(RESEARCH / 'checks.json')
    assert validation['passed'] and checks['passed']
    assert checks['full_tests'] == 2679 and checks['focused_tests'] == 20
    for kind, count in [('full', 2679), ('focused', 20)]:
        log = (RESEARCH / f'{kind}-tests.log').read_text()
        assert f'Ran {count} tests' in log and log.rstrip().endswith('OK')
    assert checkpoint['source_fingerprints'] == validation['source_fingerprints']
    cache = {}

    def check(path, expected):
        if path not in cache:
            cache[path] = digest(ROOT / path)
        assert cache[path] == expected, path

    for path, expected in checkpoint['source_fingerprints'].items():
        check(path, expected)
    manifests = dict(validation['parent_manifests'])
    current_manifest = RESEARCH / 'manifest.json'
    manifests[str(current_manifest.relative_to(ROOT))] = dict(sha256=digest(current_manifest), artifacts_checked=125)
    artifact_count = 0
    for path, metadata in manifests.items():
        check(path, metadata['sha256'])
        artifacts = read(ROOT / path)['artifacts']
        assert len(artifacts) == metadata['artifacts_checked']
        for artifact, expected in artifacts.items():
            check(artifact, expected)
        artifact_count += len(artifacts)
    assert len(manifests) == 253 and artifact_count == 84766
    assert len(checkpoint['source_fingerprints']) == 1377
    previous_publications = {}
    for date in ['2026-11-26', '2026-11-27']:
        path = OUT.parent / date / 'manifest.json'
        artifacts = read(path)['artifacts']
        for artifact, expected in artifacts.items():
            check(artifact, expected)
        previous_publications[str(path.relative_to(ROOT))] = dict(sha256=digest(path), artifacts_checked=len(artifacts))
    assert sum(item['artifacts_checked'] for item in previous_publications.values()) == 56

    for path in sorted(OUT.glob('build-*.log')):
        raw = path.read_bytes()
        archive = path.with_suffix(path.suffix + '.raw.gz')
        if not archive.exists():
            archive.write_bytes(gzip.compress(raw, mtime=0))
        path.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip() + '\n')
    for tag in ['reviewed', 'final']:
        log = (OUT / f'build-{tag}.log').read_text()
        assert not re.search(r'Warning|Overfull|Underfull|^!', log, re.M)
        assert 'Output written on' in log and '375 pages' in ' '.join(log.split())
    pdf = OUT / 'oraclemachines.pdf'
    assert pdf.read_bytes().startswith(b'%PDF-') and pdf.stat().st_size <= 50 * 1024 * 1024
    info = subprocess.check_output(['pdfinfo', str(pdf)]).decode()
    assert re.search(r'Pages:\s+375\b', info)
    assert 'Andreas Maier and GPT Astra (OpenAI AI research assistant)' in info
    pages = [1, 2, *range(323, 369)]
    images = sorted((OUT / 'rendered').glob('*.png'))
    assert len(images) == 56
    assert all((OUT / 'rendered' / f'page-{page:03}.png').is_file() for page in pages)
    subprocess.run(['git', 'check-ignore', '-q', 'alphaxiv.org'], cwd=ROOT, check=True)
    result = dict(
        passed=True, research_checkpoint=REV, scientific_body_matches_committed_source=True,
        research_source=bind(ROOT / source_path), research_manifest=bind(current_manifest),
        verified_research_checks=bind(RESEARCH / 'checks.json'),
        full_research_tests=2679, focused_research_tests=20,
        research_proof_blocks_preserved=92, published_proof_blocks_preserved=72,
        added_since_previous_publication=20, added_subsections=23,
        scientific_delta_is_single_insertion=True,
        audited_research_manifests=253, audited_research_artifact_entries=artifact_count,
        audited_scientific_sources=1377, previous_publication_unchanged=True,
        previous_publication_manifests=previous_publications,
        submitted_source=bind(OUT / 'oraclemachines.tex'), submitted_pdf=bind(pdf),
        pages=375, latex_warnings=0, ai_disclosure_unchanged=True,
        authors=['Andreas Maier', 'GPT Astra (OpenAI AI research assistant)'],
        repository_url='https://github.com/akmaier/OracleMachines',
        front_pages_visually_reviewed=[1, 2], added_research_pages_visually_reviewed=list(range(323, 369)),
        rendered={str(path.relative_to(ROOT)): digest(path) for path in images},
        visual_observations='Inspected title/byline, disclosure, evidence checkpoint and introduction at full size; reviewed every added research page plus adjacent boundaries in eight contact sheets. No clipping, overlap or displaced formulas observed.',
        proof_review='Read all 20 added mathematical proof blocks against their stated assumptions and retained experimental evidence. This text review does not constitute new Lean formalization of these propositions.',
        limitations='Restricted guarantees and costs remain explicit; no uniform polynomial-time arbitrary-SAT or P=NP claim.',
    )
    (OUT / 'checks.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key in ('passed', 'pages', 'audited_research_manifests', 'audited_research_artifact_entries', 'audited_scientific_sources', 'added_since_previous_publication')}, sort_keys=True))


if __name__ == '__main__':
    main()
