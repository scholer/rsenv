# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Simple module and CLI to generate `.oligoset.txt` files from a Cadnano-exported `.staples.csv` file.

This is one of the first steps in the "oligoset registration" pipeline:

1. Generate `.oligoset.txt` file from Cadnano exported CSV using `extract-oligoset-from-cadnano-csv` CLI.
    * You can generate both a "Complete origami" pool (name should be title-cased),
      and/or pools for individual staple pools/modules.
2. Generate oligoset hash and add this to filename(s) using `oligoset-file-hasher-cli`.
3. Move the renamed ` (hash).oligoset.txt` file(s) to the central `Oligo-pools-registry` folder.

It is now pretty easy to compare the oligosets against other oligosets:

* The order-independent sequence hash can be used directly
    to compare see if any staple strand sequences has changed.
    * There may also be a "seq+mod" hash, if any of the oligo sequences include modifications.

* The oligosets can be diff'ed to see exact changes between files.
    * `oil-diff` can be used for order-independent comparison of lines in files.
    * The oligoset.txt files should also be sorted by default, so you should be
      able to just use regular `diff` between two oligoset files.


For general CSV / table manipulation, including sorting and filtering rows and creating and deleting columns,
either use a general-purpose CLI tool, e.g. Miller or my own dataframe-action-cli,
or just create adhoc scripts as needed (this is often more explicit and easier to explain and reproduce).


Issues with Miller:

* Hard to use, a bit verbose.
* Doesn't give an error if you specify the column-name wrong, e.g.:
    $ mlr --csv --opprint sort -f Sequences TR.ZZ-LetterR.csv.smmc
  doesn't sort anything because the column name is "Sequence" not "Sequences".


"""

import sys
from typing import Optional
import pandas as pd
import typer


def extract_oligoset_from_cadnano_csv(
        csvfile,
        sort_sequences: bool = True,
        sort_by_poolname: bool = False,
        select_poolname: Optional[str] = None,
        seqs_colname: str = "Sequence",
        pools_colname: str = "Pool-name",
):
    """ Extract oligo sequences from a cadnano exported csv file.

    CLI entry-point: extract-oligoset-from-cadnano-csv

    This is useful for generating a file containing just the oligo sequences,
    which again can be used to generate an order-independent hash of the set of staple strand sequences used
    in a particular cadnano design.
    Regular file-hashes will also work, since the oligo sequences are sorted by default.

    OBS: The sequences are sorted by default, so traditional diff-tools can easily be used to check the differences
    between two .oligoset.txt files (which is definitely not the case  for the raw cadnano csv file).

    You can also use the custom `oil-diff` CLI, which compares lines in a text file in an order-independent manner.

    Args:
        csvfile: The csv file to load.
        sort_sequences:
        seqs_colname:
        pools_colname:
        select_poolname:
        sort_by_poolname:

    Returns:
        None


    ## Examples and comparison with other CLI alternatives e.g. Miller:

    Basic example:

        $ extract-oligoset-from-cadnano-csv staples.csv
        $ extract-oligoset-from-cadnano-csv staples.csv --seqs-colname "Seqs"

        $ mlr --csv cut -f Sequence then sort -f Sequence staples.csv

    Sort by poolname:

        $ extract-oligoset-from-cadnano-csv staples.csv --sort-by-poolname
        $ extract-oligoset-from-cadnano-csv staples.csv --sort-by-poolname --pools-colname "Modulename"

        $ mlr --csv sort -f Modulename,Sequence then cut -f Sequence TR.ZZ-LetterR.csv.smmc

    Only output oligos for the "Left-column" pool:

        $ extract-oligoset-from-cadnano-csv staples.csv --select-poolname "Left-column"

        $ mlr --csv filter '$Modulename == "Left-column"' then sort -f Sequence then cut -f Sequence staples.csv

    As you can see, Miller can obviously do the same as extract-oligoset-from-cadnano-csv,
    but the general-purpose Miller is harder and more verbose to use compared to this specialized CLI.
    However, it might be good to use Miller as well, since Miller is more known and has a more stable API.

    Running as a module:

        $ python -m rsenv.origami.cadnano.oligoset_from_cadnano_csv_cli

    """
    staples_df = pd.read_csv(csvfile)

    if select_poolname:
        staples_df = staples_df.loc[staples_df[pools_colname == select_poolname], :]

    # Sort:
    if sort_sequences:
        if sort_by_poolname:
            print("sort_by_poolname:", sort_by_poolname)
            # Two approaches, either use DataFrame.groupby(col), which returns a groupings object,
            # or just sort first by column, then by sequence.
            staples_df = staples_df.sort_values([pools_colname, seqs_colname])
        else:
            staples_df = staples_df.sort_values(seqs_colname)

    print("\n".join(staples_df[seqs_colname]))


def extract_oligoset_from_cadnano_csv_cli():
    typer.run(extract_oligoset_from_cadnano_csv)


if __name__ == '__main__':
    extract_oligoset_from_cadnano_csv_cli()
