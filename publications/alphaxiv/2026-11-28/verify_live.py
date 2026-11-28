"""Read-only verification of the published version and exact submitted PDF."""
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.request

OUT = Path(__file__).resolve().parent
URL = 'https://www.alphaxiv.org/abs/2611.bounded-domain-sat-compiled-knowledge-amortized-reasoning'


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'OracleMachines/1.0 publication verifier'})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read(), response.url


def main():
    page, final_url = get(URL)
    text = page.decode()
    version = max(map(int, re.findall(r'versionOrder:(\d+)', text)))
    assert version == 3, f'Expected v3, observed v{version}; do not resubmit.'
    authors = [html.unescape(name) for name in re.findall(r'<meta name="author" content="([^"]+)"', text)]
    assert authors == ['Andreas Maier', 'GPT Astra (OpenAI AI research assistant)']
    remote_pdf, pdf_final_url = get(URL + '.pdf')
    local_pdf = (OUT / 'oraclemachines.pdf').read_bytes()
    assert remote_pdf == local_pdf, 'Published PDF does not yet match snapshot; do not resubmit.'
    sha = lambda data: hashlib.sha256(data).hexdigest()
    now = datetime.now(timezone.utc)
    result = dict(
        url=URL, final_url=final_url, checked_date=now.date().isoformat(), verified_at=now.isoformat(),
        version=version, version_label='v3', authors=authors, status='published',
        passed=True, page_sha256=sha(page), pdf_url=URL + '.pdf', pdf_final_url=pdf_final_url,
        local_pdf_sha256=sha(local_pdf), remote_pdf_sha256=sha(remote_pdf), pdf_byte_identical=True,
    )
    (OUT / 'live-verification.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
