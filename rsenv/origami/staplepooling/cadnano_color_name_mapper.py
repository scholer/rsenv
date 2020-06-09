# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module for mapping module/pool color to name.




"""


import sys
import pandas as pd
from glob import glob
from pathlib import Path
import click
from collections import Counter

from .utils import read_lines_from_file


def read_colormap_manually(colormap_file, colormap_sep):
    # OBS: '#' is used for colors ('#aa8800'), so cannot use that as comment character:
    colormap_lines = read_lines_from_file(colormap_file, comment_char=None)
    colormap = {color: name
                for color, name, *_ in (
                    line.split(colormap_sep) for line in colormap_lines
                )}
    return colormap


def read_colormap_pandas(colormap_file, colormap_sep):
    df = pd.read_csv(colormap_file, sep=colormap_sep)
    colormap = dict(zip(df["Color"], df["Name"]))
    return colormap


def read_mapfile_manually(map_file, sep=None):
    """ Read a map file consisting of lines with "key value" pairs.

    Args:
        map_file:
        sep: Default None = split on whitespace.

    Returns:
        map (dict).
    """
    map_lines = read_lines_from_file(map_file)
    map_dict = {find_str: replace_str
                for find_str, replace_str, *_ in (
                    line.split(sep) for line in map_lines if line.strip()
                )}
    return map_dict


@click.command()
@click.option("-c", "--colormap-file")
@click.argument('seqpool_files', nargs=-1)  # cadnano csv export with staple strands
@click.option("--out-fn-fmt", default="{fn.stem}.poolnames{fn.suffix}")
@click.option("-s", "--sort-output-by", multiple=True)
@click.option("--use-default-seqmap/--no-use-default-seqmap", default=False)
def cadnano_color_name_mapper_cli(
        colormap_file="*.colormap.txt",
        seqpool_files=("*.export.csv", "*.cadnano-export.csv", "*.staples-export.csv"),
        seqmap_file="*.seqmap.txt",
        use_default_seqmap=True,
        color_colname="Color",
        pool_colname="Pool-name",
        seq_colname="Sequence",
        colormap_sep=None,
        colormap_reader="manual",
        seqpool_sep=",",
        sort_output_by=None,
        sort_poolnames_as=None,
        out_sep=None,
        out_cols="auto-minimal",
        out_fn_fmt="{fn.stem}.poolnames{fn.suffix}",
):
    """ CLI for mapping hex-colors to proper names (e.g. cadnano staple strand exports).

    Uh, how is this different from `cadnano.cadnano_maptransform.cadnano_maptransformer_cli()` (created in 2018)?
    I think I simply forgot about that one, when I re-created this in 2019-Nov.

    Args:
        colormap_file: File containing the name for each cadnano hex-color.
        seqpool_files: One or more cadnano exported csv files with staple strands (sequences and color).
        color_colname: The column name containing the color, default 'Color'.
        pool_colname: The column name containing the mapped pool/color names, default 'Pool-name'.
        seq_colname: The column name containing the sequence, typically 'Sequence'.
        colormap_sep: The field separator used in the colormap file, default is TAB.
        colormap_reader: The named method used to read the colormap file, either "manual" or "pandas".
        seqpool_sep: The field separator used in the cadnano CSV exported file.
        sort_output_by: Sort the output table by these columns.
        sort_poolnames_as: Specify an explicit order of poolnames for the output.
        out_sep: Separator for the output, e.g. comma or tab.
        out_cols: Specify which columns to include in the output.
        out_fn_fmt: Output filename - can contain formatting variables, e.g. {fn.stem}, {fn.suffix},
            where `fn` is the input filename.

    Returns:

    """
    if isinstance(seqpool_files, str):
        seqpool_files = [seqpool_files]
    if out_cols == "auto-minimal":
        out_cols = (pool_colname, seq_colname)
    elif out_cols in ("None", "none", "all"):
        out_cols = None
    colormap_file = glob(colormap_file)[0]
    seqmap_file = next(iter(glob(colormap_file)))
    seqpool_files = [fn for pat in seqpool_files for fn in glob(pat)]
    if out_sep is None:
        out_sep = seqpool_sep

    print("\nUsing colormap file:", colormap_file, file=sys.stderr)
    print("\nUsing seqmap file:", seqmap_file, file=sys.stderr)
    print("\nUsing seqpool files:", "".join(f"\n - {fn}" for fn in seqpool_files), file=sys.stderr)

    if colormap_reader == "manual":
        colormap = read_colormap_manually(colormap_file, colormap_sep)
    elif colormap_reader == "pandas":
        colormap = read_colormap_pandas(colormap_file, colormap_sep)
    else:
        raise ValueError(f"`colormap_reader` parameter value {colormap_reader} not recognized; "
                         f"must be one of 'manual' or 'pandas'.")

    if seqmap_file:
        seqmap = read_mapfile_manually(seqmap_file)
        print("Sequence map:", seqmap)
    else:
        seqmap = {}
    if use_default_seqmap:
        seqmap['?'] = 'T'

    seqpool_dfs = []

    for fn in seqpool_files:
        fn = Path(fn)
        seqpool_df = pd.read_csv(fn, sep=seqpool_sep)
        seqpool_dfs.append(seqpool_df)
        if seqmap:
            for find_str, replace_str in seqmap.items():
                seqpool_df[seq_colname] = seqpool_df[seq_colname].map(
                    lambda seq: seq.replace(find_str, replace_str))
        print(f"\n{fn} contains the following colors:", set(seqpool_df[color_colname]), file=sys.stderr)
        seqpool_df[pool_colname] = seqpool_df[color_colname].map(colormap)
        print(f" - the colors were mapped to pools:", set(seqpool_df[color_colname]), file=sys.stderr)
        print(f" - Color count:", dict(Counter(seqpool_df[color_colname])), file=sys.stderr)
        if sort_output_by:
            seqpool_df = seqpool_df.sort_values(by=sort_output_by)
        # Above equivalent to [colormap[color] for color in seqpool_df[color_colname]]
        if out_fn_fmt in (None, "-"):
            output_fn = None
            print(seqpool_df.to_csv(None, sep=out_sep, index=False, columns=out_cols))
        else:
            output_fn = out_fn_fmt.format(fn=fn)
            print("\nWriting mapped output to file:", output_fn)
            seqpool_df.to_csv(output_fn, sep=out_sep, index=False, columns=out_cols)

    # return seqpool_dfs


if __name__ == '__main__':
    # Run with `> python -m rsenv.seq.staplepooling.pool_color_name_mapper`
    cadnano_color_name_mapper_cli()
