# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Export all conda environments.

"""


import subprocess
from datetime import datetime
import shlex
import click
import sys

NO_CONDA_ERR_MSG = (
    "Could not find conda executable. "
    "You probably don't have conda executable on your PATH environment variable. "
    "It could be that you only have the batch file on your PATH. "
    "Please locate the folder containing your conda.exe (if on Windows) and add that to your PATH. "
    "Or run this script from within the Conda Prompt/terminal, which should have the exe correctly set. "
    "Or maybe just run `conda activate base`. "
    "Or pass the path to your conda executable using the `--condaexe <path/to/conda.exe>` parameter."
)
# DEFAULT_FNFMT = "{now:%Y%m%d}_{env}.yml"
DEFAULT_FNFMT = "{env}.yml"  # This is better; use git version control to track changes.


def list_conda_envs(from_file=None, name_only=True, condaexe=None):
    """ Get a list of conda environments.
    If you have already run `conda env list > file.txt`, then you can give that filename as `from_file`.
    Otherwise, this function will run `conda env list` as a subprocess to get the envs.
    """
    if condaexe is None:
        condaexe = 'conda'
    if from_file:
        output = open(from_file).read()
    else:
        proc = subprocess.run([condaexe, "env", "list"], capture_output=True)
        output = proc.stdout.decode('utf8')
    envs = [line.split()[0] if name_only else line
            for line in output.split("\n")
            if line.strip() and not line.startswith("#")]
    return envs


@click.command(
    name="export-all-conda-envs",
    help="""
Export all conda environments to separate environment .yml files (by default named by date and env name).
""")
@click.option("--exclude", multiple=True)
@click.option("--fnfmt", default=DEFAULT_FNFMT)
@click.option("--condaexe", help="Path to your conda executable, e.g. /path/to/conda.exe")
def export_all_conda_envs_cli(
        exclude=None,
        fnfmt=DEFAULT_FNFMT,
        condaexe=None
):
    if condaexe is None:
        condaexe = 'conda'
    try:
        envs = list_conda_envs(name_only=True, condaexe=condaexe)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}.")
        print(NO_CONDA_ERR_MSG)
        return
    if exclude:
        exclude = set(exclude)
        envs = [env for env in envs if env not in exclude]
    print("Exporting conda environments:")
    print("\n".join(f" - {env}" for env in envs))
    now = datetime.now()
    for env in envs:
        fn = fnfmt.format(env=env, now=now, dt=now, datetime=now, time=now, date=now, iso8601=now.isoformat())
        print(f"Exporting {env} to file {fn} ...")
        with open(fn, 'wb') as file:
            try:
                proc = subprocess.run(
                    [condaexe, "env", "export", "-n", env],
                    # capture_output=True,  # Do not use capture_output together with stdout/stdin args
                    stdout=file, stderr=sys.stderr
                )
            except FileNotFoundError as exc:
                print(f"ERROR: {exc}.")
                print(NO_CONDA_ERR_MSG)
                return
        # print(proc.stderr)
        # with open(fn, 'w') as file:
        #     file.write(proc.stdout.decode('utf8'))


if __name__ == '__main__':
    export_all_conda_envs_cli()
