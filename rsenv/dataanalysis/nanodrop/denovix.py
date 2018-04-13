# Copyright 2017-2018 Rasmus Scholer Sorensen

"""

Denovix vs Nanodrop data:

* Denovix exports in


"""

import csv
import numpy as np
import pandas as pd
import matplotlib


def str_arr_to_int(str_arr):
    # return [int(v) for v in str_arr]
    return np.array(str_arr, dtype=np.int)


def str_arr_to_float(str_arr):
    # return [float(v) for v in str_arr]
    return np.array(str_arr, dtype=np.float)


def str_is_int(s):
    try:
        v = int(s)
    except ValueError:
        return False
    else:
        return True


def csv_to_dataframe(filename, header_fmt="{Sample Name}-{Sample Number}",
                     values_start_idx=None, include_only=None, verbose=0):
    """Create a Pandas DataFrame from Denovix csv export file.
    
    Args:
        filename: The filename to read into a dataframe.
        header_fmt: Valid placeholder names are all meta data headers, plus "lineidx" (the row from the input file).
        values_start_idx: Which column the measurement values begin at.
            For current Denovix software, this is 24. (Edit: No? Maybe depends on the number of reported wavelength?)
        include_only: Can be used to filter which rows to import from the data file.

    Returns:
        2-tuple of (dataframe, metadata)

    """

    # Using Pandas?
    # csv_data = pd.read_csv(filename)
    # x_index = csv_data.columns.values[csv_data]

    # Or just use csv module directly?
    with open(filename) as fd:
        csvreader = csv.reader(fd)  # , delimiter=',', quotechar='"')
        header = next(csvreader)
        # sample_num_hdr_idx = header.index('Sample Number')
        # sample_name_hdr_idx = header.index('Sample Name')
        # datetime_hdr_idx = header.index('Sample Name')
        if values_start_idx is None:
            values_start_idx = next(idx for idx, fieldname in enumerate(header) if str_is_int(fieldname))
            print(f"Wavelength values detected starting at column idx {values_start_idx}")
        x_vals = str_arr_to_int(header[values_start_idx:])
        # measurements = [{
        #     'metadata': dict(*zip(header[:values_start_idx], row[:values_start_idx])),
        #     'y_vals': str_arr_to_int(row[values_start_idx:])
        #    } for row in csvreader]
        metadata, y_vals = zip(*[
            (dict(zip(header[:values_start_idx], row[:values_start_idx])), str_arr_to_float(row[values_start_idx:]))
            for num, row in enumerate(csvreader)
            if (include_only is None or num in include_only)
            and len(row) > values_start_idx  # If row only has 24 fields, then it is a blank.
        ])
    if verbose:
        print("len(y_vals):", len(y_vals))
        print("len(metadata):", len(metadata))

    # Let's just assume unique column names:
    # data = {header_fmt.format(**m['metadata']): m['y_vals'] for m in measurements}
    # df = pd.DataFrame(data=data, index=x_vals)
    # # alternatively:
    # df = pd.DataFrame(data=[m['y_vals'] for m in measurements],
    #                   columns=[header_fmt.format(**m['metadata']) for m in measurements],
    #                   index=x_vals)
    # Edit: Column names (indices in general) do not have to be unique.
    # And the user may actually want to have identically named columns.
    for i, mdict in enumerate(metadata):
        mdict['lineidx'] = i
    columns = [header_fmt.format(**m) for i, m in enumerate(metadata)]

    # data is a list of columns, each column matching up with index, so orient must be 'index' (default: 'columns').
    # df = pd.DataFrame(data=y_vals, columns=columns, index=x_vals, orient='index')
    # However, DataFrame.__init__ doesn't support 'orient' keyword, and from_item constructor doesn't support index keyword.
    # df = pd.DataFrame.from_items(items=y_vals, columns=columns, index=x_vals, orient='index')
    # Sigh. Just convert y_vals to numpy array and transpose:
    y_vals = np.array(y_vals)
    if verbose:
        print("len(columns):", len(columns))
        print("len(x_vals):", len(x_vals))
        print("y_vals.shape", y_vals.shape)
    df = pd.DataFrame(data=y_vals.T, columns=columns, index=x_vals)

    # if isinstance(metadata, list):
    #     if not keep_yvals:
    #         for d in measurements:
    #             d.pop('y_vals')
    #     metadata.extend[measurements]
    return df, metadata


def plot_nanodrop_df(
        df, selected_columnnames=None, nm_range=None,
        plot_kwargs=None, tight_layout=True,
        savetofile=None, showplot=False, verbose=0
):
    """ Reference example of how to plot a nanodrop dataframe after reading it with `denovix.csv_to_dataframe()`.

    This is mostly meant as a user reference for how to select and plot data from a dataframe.

    Args:
        df:
        selected_columnnames:
        nm_range:
        plot_kwargs: Dict with figsize, xlim, ylim, etc. Can also pass `ax` to use an existing axes.
            Passed directly as df.plot(**plot_kwargs).
        tight_layout: Adjust figure to use tight layout.
        savetofile: A filename (or list of filenames). If given, will save figure to this/these files.

    Returns:
        ax: Matplotlib Axes object. Use `ax.figure` to get the corresponding figure.
    """
    # Three different ways to get DataFrame cols and rows:
    # 1. Use df[cols] to get columns
    # 2. Use df.loc[rows, cols] to use the axes indices, e.g. the first row has index 190.
    # 3. Use df.iloc[rows, cols] to get by absolute integer indices, e.g. first row/col has index 0.

    if selected_columnnames is None:
        selected_columnnames = slice(None)
    if nm_range is None:
        nm_range = slice(None)
    elif not isinstance(nm_range, slice):
        nm_range = slice(*nm_range)
    if plot_kwargs is None:
        plot_kwargs = {}

    # We use the dataframe axes index to specify rows and columns.
    # For rows, the index corresponds to the wavelengths, i.e. from 190 nm to 500 nm.
    # For columns, the index corresponds to column headers, e.g. sample names (formatted with header_fmt).
    ax = df.loc[nm_range, selected_columnnames].plot(**plot_kwargs)

    if tight_layout:
        ax.figure.tight_layout()

    if showplot:
        print("\nYou can now customize your plot before it is saved...")
        from matplotlib import pyplot
        # In interactive mode, widgets are shown in non-blocking mode, enabling
        # interaction with the figure from the python code.
        # Interactive mode is controlled by matplotlib.interactive(False), pyplot.ioff(), or pyplot.ion().
        # You can explicitly say if show() should be invoked in blocking or non-blocking mode using `block` arg:
        pyplot.show(block=True)  # Set block=True to stop execution until plot widget is closed.
        # You cannot use Figure.show() to display in blocking mode:
        # ax.figure.show(block=True)  # Figure.show() doesn't support `block` argument

    if savetofile:
        if isinstance(savetofile, str):
            savetofile = (savetofile,)
        for plotfn in savetofile:
            # if verbose:
            print("Saving plot to file:", plotfn)
            ax.figure.savefig(plotfn)

    return ax
