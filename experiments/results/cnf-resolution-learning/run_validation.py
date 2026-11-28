"""Create the audit output directory before invoking the frozen validator.

The first attempt completed matched-search reproduction, then failed to write
its first transport record because the destination directory was absent. Its
log is retained as validation-missing-output-directory.log. No search policy,
measured workflow, frozen scientific source, or paired observation changed.
"""
from pathlib import Path
import subprocess,sys
out=Path(__file__).parent
(out/'transport').mkdir(exist_ok=True)
subprocess.run([sys.executable,'experiments/validate_cnf_resolution_learning.py','validate',str(out)],check=True)
