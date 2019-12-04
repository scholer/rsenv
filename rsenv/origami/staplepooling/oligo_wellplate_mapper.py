# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module for finding the wellplates and positions for each oligo sequence.


Instructions:



Run with

```
> python -m rsenv.seq.staplepooling.oligo_wellplate_mapper
```


Examples:
---------

### Example 1:

* Situation and objective:
    * You have a cadnano CSV export file, `cadnano-staples.csv`.
    * You have a csv file that assigns a pool name to each hex-color, `pool-color-names.colormap.txt`.
    * You have three csv files containing the oligo sequences and positions for three wellplates:
        `plate1.csv`, `plate2.csv`, `plate3.csv`.
    * We would like to create a pool pipetting scheme, i.e. a table that lists which
        wellplate and positions to pipet for each color in the cadnano design.

1. First, use `cadnano_color_name_mapper_cli()` to give each color a name (optional):

    > cadnano-color-name-mapper cadnano-staples.csv -m pool-color-names.colormap.txt

    This will create a file, `cadnano-staples.poolnames.csv`, where the pool name has
    been added to each staple strand.

2. Then, use oligo_sequence_wellplate_mapper_cli() to map each oligo sequence
    to a wellplate name and position:

    > oligo-sequence-wellplate-mapper -s cadnano-staples.poolnames.csv -w plate1.csv -w plate2.csv -w plate3.csv

    This will generate a file where the wellplate name and position for each sequence has
    been added as two additional columns.



Notes:

    1. The program actually expects glob patterns, so the above could also be written as:

    > oligo-sequence-wellplate-mapper -s cadnano-staples.poolnames.csv -w plate?.csv




"""

# import os
import sys
import pandas as pd
from glob import glob
from pathlib import Path
import click

from .utils import read_lines_from_file


@click.command()
@click.option("--wellplate-files", "-w", multiple=True)
@click.option("--seqpool-files", "-s", multiple=True)
@click.option("--seqfile-format", default='csv')
@click.option("--wellpos-colname", default='Pos')
@click.option("--out-cols", default='auto-minimal')
@click.option("--out-sep", default='\t')
def oligo_sequence_wellplate_mapper_cli(
        seqpool_files=("*.pools.csv", "*.poolnames.csv"),
        wellplate_files=("*.wellplate.csv",),
        seqfile_format='csv',
        wellplate_format='idt-xls-order',
        excel_sheet_is_platename=True,  # For wellplate Excel files
        excel_sheet_is_poolname=True,  # For seq-pool Excel files
        add_poolname_if_missing=True,
        pool_colname="Pool-name",
        seq_colname="Sequence",  # For both pools and wellplates
        wellplate_colname='Plate-name',
        wellpos_colname="Pos",
        sort_output_by=None,
        output_poolnames=None,
        output_poolname_filter=None,
        output_pool_filter_file=None,
        # output_individual=False,  # Not implemented.
        # output_merged=True,  # Default and only behavior
        output_file="-",  # '-' indicates stdout.
        out_cols="auto-minimal",
        out_sep="\t",
        missing_wellplate_warning=True,
):
    """ CLI for mapping sequences to well plate positions.

    OBS: The output from this should NOT contain anything specific to the pipetting protocol.
    I.e. no Robot-specific or person-specific stuff; that is added later.
    This means: Do not add info about where to find wellplates or pool-tubes inside the robot.

    Args:
        wellplate_files: CSV files containing wellplate information, i.e. what is in each well.
        seqpool_files: Txt or csv files containing info about which sequences goes into each pool.
        seqfile_format: How to load each seqpool file (i.e. single-column plain text or csv file).
        wellplate_format: Wellplate file format, e.g. csv or xls.
        excel_sheet_is_platename: If True, use sheet-name as plate-name (instead of filename).
        excel_sheet_is_poolname: If True, use sheet-name as pool-name (for seq-pool files)
        add_poolname_if_missing: If True, add a column with pool-name if no column is present.
        pool_colname: The column name to use for pool names.
        seq_colname: The column name containing sequences.
        wellplate_colname: The column name containing the wellplate name.
        wellpos_colname: The column name containing the plate positions.
        sort_output_by: Sort the output by these columns.
        output_poolname_filter: Only output rows for these pool names.
        output_pool_filter_file: Read pool names to output from file.
        output_poolnames: This is an alternative way of controlling the output.
            Will group rows by poolname and list them in the given order.
        out_cols: The columns to include in the output.
        out_sep: Column/field separator to use when writing output.
        output_file: Write output to this file. If None or "-", write to stdout.
        missing_wellplate_warning: Warn if any sequences could not be found in the wellplate table.

    Returns:
        None

    Example usage:

    > oligo-sequence-wellplate-mapper
    """
    if wellplate_files is None:
        wellplate_files = "*.wellplate.csv"
    if seqpool_files is None:
        seqpool_files = "*.pool.txt"
    if out_cols == "auto-minimal":
        out_cols = (pool_colname, seq_colname, wellplate_colname, wellpos_colname)
    elif out_cols in ("None", "none", "all"):
        out_cols = None
    # Perform glob expansions (which is not automatically done by Windows-CMD)
    wellplate_files = [fn for pat in wellplate_files for fn in glob(pat)]
    seqpool_files = [fn for pat in seqpool_files for fn in glob(pat)]

    print("\nUsing seqpool files:", "".join(f"\n - {fn}" for fn in seqpool_files), "\n", file=sys.stderr)
    print("\nUsing wellplate files:", "".join(f"\n - {fn}" for fn in wellplate_files), "\n", file=sys.stderr)

    wellplate_dfs = {}
    # Add wellplate names to wellplate_df:
    for fn in wellplate_files:
        fn = Path(fn)
        platename = fn.stem.rsplit(".wellplate")[0]
        if wellplate_format == 'idt-xls-order' or fn.suffix == '.xls':
            with pd.ExcelFile(fn) as excel_file:
                for sheet_name in excel_file.sheet_names:
                    wellplate_df = pd.read_excel(excel_file, sheet_name)
                    if excel_sheet_is_platename:
                        platename = sheet_name
                    if wellplate_colname not in wellplate_df:
                        wellplate_df[wellplate_colname] = sheet_name
                    # Perform IDT column renames:
                    if "Well Position" in wellplate_df and wellpos_colname not in wellplate_df:
                        wellplate_df.rename(columns={"Well Position": wellpos_colname})
                    wellplate_dfs[platename] = wellplate_df  # Add to dict
        else:
            wellplate_df = pd.read_csv(fn)
            wellplate_df[wellplate_colname] = platename
            wellplate_dfs[platename] = wellplate_df  # Add to dict
            if wellpos_colname not in wellplate_df:
                print(f"Warning: The wellplate table from {fn} does not contain a column named '{wellpos_colname}'. "
                      f"Available column are: {wellplate_df.columns}. "
                      f"Please use the `wellpos_colname` parameter to explicitly specify which column to use.")

    # Make a single df with all wellplates:
    wellplates_df = pd.concat(wellplate_dfs.values())

    # Next, read sequence/staple pools files:
    seqpool_dfs = {}
    for fn in seqpool_files:
        fn = Path(fn)
        pool_name = fn.stem.split(".pool")[0]  # poolname.pool.txt -> poolname
        if seqfile_format.lower() == 'excel' or fn.suffix == '.xls':
            with pd.ExcelFile(fn) as excel_file:
                for sheet_name in excel_file.sheet_names:
                    seqpool_df = pd.read_excel(excel_file, sheet_name)
                    if excel_sheet_is_poolname:
                        pool_name = sheet_name
                    if pool_colname not in seqpool_df:
                        seqpool_df[pool_colname] = pool_name
                    seqpool_df = seqpool_df.merge(wellplates_df, how='left', on=seq_colname, sort=False)
                    seqpool_dfs[pool_name] = seqpool_df  # Add this file to the dict
            continue
        if seqfile_format.lower() == 'single-column' or fn.suffix == '.txt':
            # Each seqfile contains a single pool, and just lists the oligo-sequences as a single column.
            seqpool_df = pd.DataFrame({seq_colname: read_lines_from_file(fn)})
            seqpool_df[pool_colname] = pool_name
        elif seqfile_format.lower() == 'csv' or fn.suffix == '.csv':
            seqpool_df = pd.read_csv(fn)
            if pool_colname not in seqpool_df:
                seqpool_df[pool_colname] = pool_name
        else:
            raise ValueError(
                f"File extension {fn.suffix} not recognized, and `seqfile_format` {seqfile_format!r} is not one of "
                f"the accepted values ('csv' and 'single-column').")

        # Find wellplate and position for each sequence:
        # seqpool_df.join(wellplates_df, on=seq_col_name)  # .join() is when merging using the index.
        seqpool_df = seqpool_df.merge(wellplates_df, how='left', on=seq_colname, sort=False)
        # OBS: how="inner" will drop rows in left that is not found in right.
        # (and can produce multiple rows if right contains multiple matches for left).
        seqpool_dfs[pool_name] = seqpool_df  # Add this file to the dict

    # Make a single, joined seqpools dataframe:
    seqpools_df = pd.concat(seqpool_dfs.values())

    # Filter output by pool name:
    if output_poolname_filter is None and output_pool_filter_file:
        output_poolname_filter = read_lines_from_file(output_pool_filter_file)
    if output_poolname_filter is not None:
        print("Filtering output, including only the following pools:", output_poolname_filter, file=sys.stderr)
        print(" - rows, before:", len(seqpool_df), file=sys.stderr)
        seqpool_df = seqpool_df.loc[seqpool_df[pool_colname] in output_poolname_filter, :]
        print(" - rows, after: ", len(seqpool_df), file=sys.stderr)

    # Group output by pool-name:
    # There are multiple ways of doing this:
    # * Obviously, we can simply sort the output by pool-name.
    #   This can be combined with a separate 'filter' operation to include/exclude specific pool-names (above).
    # * If we want to sort in a custom order, we can use a categorical series or
    #   `df.iloc[df[col].map(custom_dict).argsort()]`
    # * If we only want to output specific pool names and we want to output them in a given order,
    #   we can group by pool-name, and concatenate groups by the given order.
    if output_poolnames:
        grouped_df = seqpools_df.groupby(pool_colname)
        seqpools_df = pd.concat([grouped_df.get_group(poolname) for poolname in output_poolnames])

    # Checks:
    # - Check for missing wellplate (i.e. where the oligo sequence could not be cound)
    if missing_wellplate_warning:
        missing_pos_df = seqpools_df.loc[seqpools_df[wellpos_colname].isnull(), :]
        if len(missing_pos_df) > 0:
            print("\n\nWARNING: Some pool oligo sequences could not be found in the wellplates:", file=sys.stderr)
            print(missing_pos_df, file=sys.stderr)

    # Finally, produce output:
    # - Use `.to_string()` to write a "pretty formatted" table,
    # - Use `to_csv()` to write character-separated text.
    # Maybe just use print - perhaps always writing to stdout
    # print(seqpools_df.to_csv())
    # out_file = sys.stdout if output_file == "-" else output_file
    # Just pass None to write to stdout? - No, this just returns the string.
    output = seqpools_df.to_csv(
        None if output_file in (None, "-") else output_file,
        sep=out_sep,
        index=False,
        columns=out_cols,
        line_terminator='\n',
        # For some reason, Pandas needs to be told to use '\n' as line terminator, otherwise
        # when writing to file on Windows, you will get blank lines interspersed in your output.
        # (Pandas version 0.24.0).
    )
    if output:  # We get if no file or filepath is passed to `to_csv()`.
        print(output)
    else:
        print("Output written to file:", output_file, file=sys.stderr)


if __name__ == '__main__':
    # Run with `> python -m rsenv.seq.staplepooling.oligo_wellplate_mapper`
    oligo_sequence_wellplate_mapper_cli()
