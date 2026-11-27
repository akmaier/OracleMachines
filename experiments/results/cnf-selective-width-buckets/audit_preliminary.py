"""Retain original source hashes and relocated bindings for excluded pilot data."""
from pathlib import Path
from experiments import compare_cnf_selective_width_buckets as s
base=s.base;out=Path(__file__).parent;pilot=out/'preliminary-check-schedule'
snapshots={str(f.relative_to(pilot/'sources')):f for f in (pilot/'sources').rglob('*.py')}


def resolve(path):
    if path in snapshots:return snapshots[path]
    p=Path(path)
    try:return pilot/p.relative_to(out)
    except ValueError:return p


def bound(binding):
    path=resolve(binding['path']);assert base.sha(path)==binding['sha256'];return base.load(path)


protocol=base.load(pilot/'protocol.json')
for name in ('parent','parent_manifest','panel','descriptions','truth','freeze'):bound(protocol[name])
for file,h in protocol['source_fingerprints'].items():assert base.sha(resolve(file))==h,file
reports=[]
for file in sorted(pilot.glob('*-*/report.json')):
    r=base.load(file);bound(r['panel']);archive=resolve(r['archive']['path']);assert base.sha(archive)==r['archive']['sha256']
    for name in r['stored'].values():assert (file.parent/name).is_file()
    reports.append(dict(path=str(file),sha256=base.sha(file),mode=r['mode']))
base.write(out/'preliminary-retention.json',dict(passed=True,excluded=True,reason='Unequal successful-discovery internal final checks; timings are not used in the accepted comparison.',original_result_root=str(out),archived_result_root=str(pilot),source_snapshots={file:dict(path=str(path),sha256=base.sha(path)) for file,path in snapshots.items()},reports=reports,protocol_sources_checked=len(protocol['source_fingerprints']),resolution='For preliminary data only, resolve original result-root paths below the archived root and the listed scientific sources through their exact snapshots. Immutable parent paths are unchanged.'))
print('Preserved excluded reports:',len(reports))
