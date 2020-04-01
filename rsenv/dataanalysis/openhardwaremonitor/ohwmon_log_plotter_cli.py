# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

CLI tool to plot temperature CSV log files from Open Hardware Monitor.


"""


from pathlib import Path
import glob
import re
import click
import pandas as pd
import matplotlib


@click.command()
def ohm_csv_plotter_cli(directory=None, files=None, globpat="*.csv", col_match_regex=".*cpu.*temperature.*", label_fmt="{label} °C"):
    col_match_regex = re.compile(col_match_regex)
    if files is None:
        files = []
    if directory is not None:
        # directory = "."
        directory = Path(directory)
        files.extend(directory.glob(globpat))

    dfs = []
    identifiers = ""
    for file in files:
        print("Processing file:", file)
        with open(file) as f:
            identifiers = f.readline().strip().split(",")
            legends = f.readline().strip().split(",")
            legends = [l.strip('"') for l in legends]
            assert identifiers[0] == ""
            identifiers[0] = "Time"
        df = pd.read_csv(file, skiprows=2, header=None, names=identifiers, index_col=0)
        dfs.append(df)

    df = pd.concat(dfs, axis=0)
    # Aargh, pandas.concat below version 0.23 will sort by default with no option to disable.
    df = df.reindex(columns=dfs[0].columns)

    cols_and_labels_to_plot = [
        (col, label_fmt.format(col=col, label=label))
        for col, label in zip(df.columns, legends[1:])
        if col_match_regex.fullmatch(col)
    ]
    cols_to_plot, labels_to_plot = zip(*cols_and_labels_to_plot)

    ax = df[list(cols_to_plot)].plot()
    ax.figure.show()
    return df



