# Copyright 2018 Rasmus Scholer Sorensen

"""

A simple module to rename *.cdf files based on their

"""

import os
import click
import inspect
import shutil

from .io import load_cdf_data, get_cdf_files


def rename_cdf_files(
        cdf_files_or_dir,
        rename_fmt=os.path.join("{output_dir}", "{dirpath}", "{i:02} {ds.sample_name}"),
        output_dir=None,
        replace=None,
        overwrite=None,
        dryrun=False,
        copy=False,
        list_attributes=False,
        verbose=0,
):
    """  Batch rename cdf files.

    Args:
        cdf_files_or_dir: One or more cdf files, or directories containing cdf files.
        rename_fmt: How to format the new file name.
        output_dir: The directory to output renamed files to.
        replace: Replace one or more characters in the new filename, e.g. transform spaces to underscore.
        overwrite: Overwrite existing files if they exists.
        dryrun: Do not do any actual operations, just show what would have been done.
        copy: Copy files instead of renaming them.
        list_attributes: List attributes for each CDF dataset. Useful if you can't remember the available attributes.
        verbose: Be more verbose when printing information about the renaming process.

    Returns:
        List of all new file names.
    """
    if verbose >= 3:
        print("Locals:")
        print(locals())
    cdf_files = get_cdf_files(cdf_files_or_dir)
    if verbose >= 2:
        newline = '\n'
        print(f"Renaming CDF files:\n"
              f"{newline.join(cdf_files)}\n"
              f"according to rename_fmt {rename_fmt!r}.{' (DRYRUN)' if dryrun else ''}\n")
    new_names = []
    for i, filename in enumerate(cdf_files):
        ds = load_cdf_data(filename)
        if list_attributes:
            print_cdf_attributes(filename, ds=ds)
        basename = os.path.basename(filename)
        fnroot, ext = os.path.splitext(basename)  #
        dirname = dirpath = os.path.dirname(filename)
        cwd = os.getcwd()
        if output_dir is None:
            output_dir = cwd
        elif not os.path.exists(output_dir):
            print(f"Creating output directory {output_dir!r} ...")
            os.makedirs(output_dir, exist_ok=True)
        fmt_params = locals()
        new_name = rename_fmt.format(**fmt_params)
        if replace:
            for oldstr, newstr in replace:
                new_name.replace(oldstr, newstr)
        if os.path.exists(new_name):
            if overwrite is False:
                print(f" - File {new_name!r} already exists (old filename: {filename}), "
                      f"and overwrite is  False; skipping...")
                continue
            elif overwrite is None:
                answer = input(f"New filename {new_name!r} already exists. Overwrite? [Y/n] ")
                skip = answer and answer.lower().startswith('n')
            else:
                skip = False
            if skip:
                print(f" - SKIPPING file rename: {filename} --> {new_name}")
                continue
        op_name = "COPYING" if copy else "RENAMING"
        if verbose:
            print(f"{op_name}: {filename!r} --> {new_name!r}")
        if not dryrun:
            if copy:
                shutil.copy2(src=filename, dst=new_name)
            os.rename(src=filename, dst=new_name)
        new_names.append(new_name)
    return new_names


def print_cdf_attributes(filename, ds=None):
    """ Show attributes for a cdf dataset. """
    if filename:
        print(f"\n\nCDF dataset attribuets for: {filename!r}:")
    if ds is None:
        ds = load_cdf_data(filename)
    print("\n".join(f"    {k:<30} {v}" for k, v in ds.attrs.items()), end="\n\n")


# Click CLI for rename_cdf_files():
_sig = inspect.signature(rename_cdf_files)
_argspec = inspect.getfullargspec(rename_cdf_files)
_doc = inspect.getdoc(rename_cdf_files)
rename_cdf_files_cli = click.Command(
    callback=rename_cdf_files,
    name=rename_cdf_files.__name__,
    help=_doc,
    params=[
        # Params and options given directly to click.Option/Argument must be a list (unlike with the decorators)
        click.Option(['--rename-fmt', '-f'], default=_sig.parameters['rename_fmt'].default),
        click.Option(['--output-dir'], default=_sig.parameters['output_dir'].default),
        click.Option(['--replace', '-r'], default=_sig.parameters['replace'].default, multiple=True, nargs=2),
        click.Option(['--overwrite/--no-overwrite'], default=_sig.parameters['replace'].default),
        click.Option(['--dryrun/--no-dryrun'], default=_sig.parameters['dryrun'].default),
        click.Option(['--list-attributes/--no-list-attributes', '-l'], default=_sig.parameters['list_attributes'].default),
        click.Option(['--copy/--no-copy'], default=_sig.parameters['copy'].default),
        click.Option(['--verbose', '-v'], count=True),
        click.Argument(['cdf_files_or_dir'], nargs=-1)
])



