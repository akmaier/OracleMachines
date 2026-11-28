"""Build the exact approved daily snapshot in scratch space."""
from pathlib import Path
import subprocess,shutil
out=Path(__file__).resolve().parent;build=Path('/private/tmp/oracle-alphaxiv-20261128');build.mkdir(exist_ok=True)
for tag in ('first','second','reviewed','final'):
 with (out/f'build-{tag}.log').open('w') as log:
  subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(build),str(out/'oraclemachines.tex')],stdout=log,stderr=subprocess.STDOUT,check=True)
 print('Completed publication build',tag,flush=True)
shutil.copyfile(build/'oraclemachines.pdf',out/'oraclemachines.pdf')
