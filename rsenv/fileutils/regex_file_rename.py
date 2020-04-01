# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

CLI tool for renaming files using regular expressions (regex),
including a "dry-run" option.

Usage:

    regex-file-rename <input-regex> <{output}-{naming}-{format}>


Examples:

Example 1: Rename

```
> dir

20200330_actionista-pypi.yml  20200330_hplc.yml            20200330_rsenv.yml
20200330_actionista.yml       20200330_nanoimager.yml      20200330_snakemake.yml
20200330_base.yml             20200330_openchrom-py27.yml  20200330_st3-mimic.yml
20200330_cadnano2-pyqt4.yml   20200330_pdf-py2.yml         20200330_webdl.yml
20200330_cadnano2-pyqt5.yml   20200330_pdf.yml             20200330_youtube-dl.yml
20200330_cadnano25_up.yml     20200330_picasso.yml         20200330_zepto-eln-dev-cf.yml
20200330_datelibs.yml         20200330_pipenv.yml          20200330_zepto-lims-dev.yml
20200330_eln-server.yml       20200330_pipx.yml            20200330_zepto-lims.yml
20200330_gelutils-py27.yml    20200330_qpaint.yml          base_20200330.yml
20200330_gelutils-py34.yml    20200330_rsenv-py35.yml      rsenv_20200330.yml
20200330_hg-py27.yml          20200330_rsenv-py38-cf.yml

> regex-file-rename "20200330_(\w+).yml" "{0}.yml"

Renaming 20200330_actionista.yml -> actionista.yml
Renaming 20200330_base.yml -> base.yml
Renaming 20200330_cadnano25_up.yml -> cadnano25_up.yml
Renaming 20200330_datelibs.yml -> datelibs.yml
Renaming 20200330_hplc.yml -> hplc.yml
Renaming 20200330_nanoimager.yml -> nanoimager.yml
Renaming 20200330_pdf.yml -> pdf.yml
Renaming 20200330_picasso.yml -> picasso.yml
Renaming 20200330_pipenv.yml -> pipenv.yml
Renaming 20200330_pipx.yml -> pipx.yml
Renaming 20200330_qpaint.yml -> qpaint.yml
Renaming 20200330_rsenv.yml -> rsenv.yml
Renaming 20200330_snakemake.yml -> snakemake.yml
Renaming 20200330_webdl.yml -> webdl.yml

# Since the regex `\w` symbol does not match hyphens, files with hyphens are not included.

```

Example 2: Rename, and create a sub-folder:

```

> python -m rsenv.fileutils.regex_file_rename "(\d{8})_([-\w]+).yml" "{0}/{1}.yml"

Renaming 20200330_actionista-pypi.yml -> 20200330/actionista-pypi.yml
Renaming 20200330_actionista.yml -> 20200330/actionista.yml
Renaming 20200330_base.yml -> 20200330/base.yml
Renaming 20200330_cadnano2-pyqt4.yml -> 20200330/cadnano2-pyqt4.yml
Renaming 20200330_cadnano2-pyqt5.yml -> 20200330/cadnano2-pyqt5.yml
Renaming 20200330_cadnano25_up.yml -> 20200330/cadnano25_up.yml
Renaming 20200330_datelibs.yml -> 20200330/datelibs.yml
Renaming 20200330_eln-server.yml -> 20200330/eln-server.yml
Renaming 20200330_gelutils-py27.yml -> 20200330/gelutils-py27.yml
Renaming 20200330_gelutils-py34.yml -> 20200330/gelutils-py34.yml
Renaming 20200330_hg-py27.yml -> 20200330/hg-py27.yml
Renaming 20200330_hplc.yml -> 20200330/hplc.yml
Renaming 20200330_nanoimager.yml -> 20200330/nanoimager.yml
Renaming 20200330_openchrom-py27.yml -> 20200330/openchrom-py27.yml
Renaming 20200330_pdf-py2.yml -> 20200330/pdf-py2.yml
Renaming 20200330_pdf.yml -> 20200330/pdf.yml
Renaming 20200330_picasso.yml -> 20200330/picasso.yml
Renaming 20200330_pipenv.yml -> 20200330/pipenv.yml
Renaming 20200330_pipx.yml -> 20200330/pipx.yml
Renaming 20200330_qpaint.yml -> 20200330/qpaint.yml
Renaming 20200330_rsenv-py35.yml -> 20200330/rsenv-py35.yml
Renaming 20200330_rsenv-py38-cf.yml -> 20200330/rsenv-py38-cf.yml
Renaming 20200330_rsenv.yml -> 20200330/rsenv.yml
Renaming 20200330_snakemake.yml -> 20200330/snakemake.yml
Renaming 20200330_st3-mimic.yml -> 20200330/st3-mimic.yml
Renaming 20200330_webdl.yml -> 20200330/webdl.yml
Renaming 20200330_youtube-dl.yml -> 20200330/youtube-dl.yml
Renaming 20200330_zepto-eln-dev-cf.yml -> 20200330/zepto-eln-dev-cf.yml
Renaming 20200330_zepto-lims-dev.yml -> 20200330/zepto-lims-dev.yml
Renaming 20200330_zepto-lims.yml -> 20200330/zepto-lims.yml

```



Alternative names:

* re-rename
* re-renamer
* regex-file-rename
* regex-file-renamer
* regular-rename
* regular-renamer


### Output format types:

str.format: Uses Python's curly-braced

%-interpolation: Uses Python's old %-style "string interpolation" formatting.

regex: Uses \1 and \g<name> as placeholder names.


## Prior art:

Alternative Python CLI tools:

* rename
* prename
* mass_rename
* mass-renamer
* ren
* bulk-renamer
* batch-renamer
* Poly-rename
* Renamer
* rexmv
* mvstd
* renamebyreplace
* namemod
* rename_files

...and maybe a dozen more - plenty to go around.


"""

import pathlib
import fnmatch
import re
import shutil
import click


@click.command("regex-file-rename")
@click.argument("input_pattern")
@click.argument("output_fnfmt")
@click.option("--recursive/--no-recursive", "-r")
@click.option("--dryrun/--no-dryrun", "-n")
@click.option("--basepath")
@click.option("--verbose", "-v", count=True)
# @click.option("--output-format", default="str.format")  # Options: "str.format", "%-interp", "regex"
def regex_file_rename_cli(
        input_pattern,
        output_fnfmt,
        recursive=False,
        basepath=None,
        include_dirs=False,
        pattern_type="regex",  # One of "regex", "glob", or "fixed"
        dryrun=True,
        create_dirs=True,
        verbose=0,
):
    if basepath is None:
        basepath = "."
    cwd = pathlib.Path(basepath)
    input_pattern = re.compile(input_pattern)
    for path in cwd.iterdir():
        if path.is_dir() and not include_dirs:
            continue
        match = input_pattern.match(path.as_posix())
        if not match:
            continue
        renamed_path = pathlib.Path(output_fnfmt.format(*match.groups(), **match.groupdict()))
        print("(DRYRUN) " if dryrun else "", f"Renaming {path.as_posix()} -> {renamed_path.as_posix()}", sep="")
        # print("- match.groups():", match.groups())
        # print("- match.groupdict():", match.groupdict())
        if not renamed_path.parent.exists() and create_dirs:
            if verbose:
                print("(DRYRUN) " if dryrun else "",
                      f"Creating parent dir (including parent dirs): {renamed_path.parent}", sep="")
            if not dryrun:
                renamed_path.parent.mkdir(parents=True, exist_ok=True)
        if not dryrun:
            path.rename(renamed_path)


if __name__ == '__main__':
    regex_file_rename_cli()
