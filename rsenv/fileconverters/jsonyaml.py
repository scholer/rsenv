
import os
import json
import yaml
import click
import sys
import glob


@click.command()
# OBS: `help` parameter not available for click arguments.
@click.argument(
    'jsonfiles', nargs=-1,
    type=(click.STRING if sys.platform == 'win32' else click.Path(file_okay=True, dir_okay=False, exists=True))
)
@click.option(
    '-f', '--outputfnfmt', default="{inputfn}.yaml",
    help="Format spec for output filenames. Default '{inputfn}.yaml' will simply append '.yaml' to the input filename."
)
@click.option(
    '-v', '--verbose', count=True, help="Increase verbosity. Default (0) means don't print anything.")
@click.option(
    '--overwrite/--no-overwrite',
    help="If specified, overwrite existing output files without prompting. "
         "(Default is to ask before overwriting existing files).")
@click.option('--ignore-errors/--no-ignore-errors', default=None, help="If specified, ignore errors.")
@click.option('--wildcards/--no-wildcards', default=None, help="If specified, expand bash-style wildcards with glob.")
def json_files_to_yaml_cli(
        jsonfiles, outputfnfmt="{inputfn}.yaml", overwrite=False,
        verbose=0, wildcards=None, ignore_errors=False,
):
    """CLI for converting JSON formatted text files to YAML formatted text files.

    Arguments:

        jsonfiles: One or more input files to convert.

    """
    # Rest of parameters documented by click.option help
    return json_files_to_yaml(
        jsonfiles=jsonfiles, outputfnfmt=outputfnfmt, overwrite=overwrite,
        verbose=verbose, wildcards=wildcards, ignore_errors=ignore_errors
    )


def json_files_to_yaml(
            jsonfiles, outputfnfmt="{inputfn}.yaml", overwrite=False,
            verbose=0, wildcards=None, ignore_errors=False,
    ):
    """Convert JSON formatted text files to YAML formatted text files.

    Args:
        jsonfiles:
        outputfnfmt:
        overwrite:
        verbose:
        wildcards:
        ignore_errors:

    Returns:

    """
    if wildcards is True or (sys.platform == 'win32' and wildcards is None):
        # Expand wildcards:
        jsonfiles = [fn for pat in jsonfiles for fn in (glob.glob(pat) if ("*" in pat or "?" in pat) else [pat])]
        print(jsonfiles)
        for fn in jsonfiles:
            if not (os.path.exists(fn) and os.path.isfile(fn)):
                print(f"\nERROR: jsonfile argument `{fn}` is not a file, aborting!")
                return
    outputfiles = []
    for inputfn in jsonfiles:
        if verbose:
            print(f"\nReading data from json file: {inputfn}")
        try:
            with open(inputfn) as fdin:
                data = json.load(fdin)
        except IOError as exc:
            print(" - IOError:", exc)
            if ignore_errors:
                continue
            else:
                print("(note: use `--ignore-errors` argument to ignore errors and just skip to next file.")
                raise exc
        except (UnicodeDecodeError,) as exc:
            print(f" - ERROR opening json file! {exc.__class__.__name__}: {exc}")
            if ignore_errors:
                continue
            else:
                print("(note: use `--ignore-errors` argument to ignore errors and just skip to next file.")
                raise exc
        inputfnbase, inputfnext = os.path.splitext(inputfn)
        outputfn = outputfnfmt.format(inputfn=inputfn, inputfnbase=inputfnbase, inputfnext=inputfnext)
        if os.path.exists(outputfn) and not overwrite:
            if not (input(f"ATTENTION: File {outputfn} already exists.\nOverwrite? [y/N] ") or "No")[0].lower() == "y":
                print(f" - OK, skipping conversion of {inputfn}.")
                continue
        if verbose:
            print(f" - writing data to file: {outputfn}")
        with open(outputfn, 'w') as fdout:
            yaml.dump(data, stream=fdout)
        outputfiles.append(outputfn)

    return outputfiles


