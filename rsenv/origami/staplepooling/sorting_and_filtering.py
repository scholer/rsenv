# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module for sorting and filtering csv data:

Alternatives:

* I have created a separate `dataframe-action-cli` project for manipulating CSV/data files
  using Pandas DataFrame.
* Miller.
* Awk.
* `sort` (UNIX program).
* `jq` (for JSON data).
* VisiData.
*

See also:

* https://github.com/dbohdan/structured-text-tools - a list of tools for working with structured text.


"""

import pandas as pd


def sort_and_filter_action_cli(
        input_file,
        output_fnfmt="{inputfn.stem}.{operations}{inputfn.suffix}",
        sort_by=None,
        sort_order="ascending",
        include=None,  # I'm not actually sure what the API should be for this include, i.e. how to specify which column to use, etc.
        query=None,
):
    """ A simple CLI to sort and select data from csv file. """
    df = pd.read_csv(input_file)
    # if include:
    #     # df.loc[rows, cols]
    #     row_selection = df[]
    #     df = df.loc[]
    if query:
        queries = [query] if isinstance(query, str) else query
        for expr in queries:
            df = df.query(expr)


def sort_df_cli(
        input_file,
        output_fnfmt="{inputfn.stem}.{operations}{inputfn.suffix}",
        sort_by=None,
        select=None,
        select_from_file=None,
        select_type="regex",
        exclude=None, exclude_from_file=None,
):
    """ Another CLI to sort and select data from csv file, .

    """






