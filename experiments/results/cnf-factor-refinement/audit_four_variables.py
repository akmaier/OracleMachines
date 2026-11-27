"""Reproduce the exhaustive four-variable relation/width-three audit."""
from pathlib import Path
from collections import Counter
import gzip,json,hashlib,time
from experiments import cnf_factor_clause_width as f


def main(out):
    start=time.perf_counter();counts=Counter();digest=hashlib.sha256()
    with gzip.GzipFile(filename=str(out/'exhaustive-four-certificates.jsonl.gz'),mode='wb',mtime=0) as stream:
        for bits in range(65536):
            factor=dict(scope=[1,2,3,4],bits=bits);proof,diag=f.discover(factor,3);status=f.check(factor,proof)
            isolated=[row for row in range(16) if not bits>>row&1 and all(bits>>(row^(1<<i))&1 for i in range(4))]
            assert (status=='obstruction')==bool(isolated) and status in ('cover','obstruction')
            counts[status]+=1;counts['certificates']+=1
            data=(json.dumps(proof,sort_keys=True,separators=(',',':'))+'\n').encode();stream.write(data);digest.update(data)
    (out/'exhaustive-four-audit.json').write_text(json.dumps(dict(passed=True,counts=dict(counts),uncompressed_sha256=digest.hexdigest(),compressed_sha256=hashlib.sha256((out/'exhaustive-four-certificates.jsonl.gz').read_bytes()).hexdigest(),seconds=time.perf_counter()-start,scope='Every four-variable Boolean relation, classified at width three. Independent criterion: an excluded hypercube vertex with all four neighbors included is exactly the obstruction to covering the zero set by codimension-at-most-three subcubes. All 65536 complete certificates retained; outside stage timings.'),sort_keys=True,indent=2)+'\n')


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
