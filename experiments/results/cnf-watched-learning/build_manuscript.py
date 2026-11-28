"""Build in scratch space and preserve all four compiler passes."""
from pathlib import Path
import subprocess
out=Path('experiments/results/cnf-watched-learning')
build=Path('/private/tmp/oracle-watched-learning-latex');build.mkdir(exist_ok=True)
source='paper/bounded_domain_sat_and_amortized_reasoning.tex'
for tag in ('first','second','reviewed','final'):
 with (out/f'latex-{tag}.log').open('w') as log:
  subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(build),source],stdout=log,stderr=subprocess.STDOUT,check=True)
 print('Completed LaTeX pass:',tag,flush=True)
