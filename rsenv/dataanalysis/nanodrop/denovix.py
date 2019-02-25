# Copyright 2017-2018 Rasmus Scholer Sorensen

"""

Denovix vs Nanodrop data:

* Denovix exports in


"""

import csv
import numpy as np
import pandas as pd
from itertools import cycle, product
from pprint import pprint
import matplotlib
import matplotlib.style
import matplotlib.figure


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
        df, selected_columnnames=None,
        nm_range=None, xlim=None, ylim=None,
        normalize=False, normalize_to=None, normalize_range=None,
        linestyles=None, colors=None, markers=None, style_combination_order=('linestyle', 'color', 'marker'),
        use_seaborn=False, mpl_style=None,
        fig_kwargs=None,
        axes_kwargs=None,
        plot_kwargs=None,
        tight_layout=True, add_legend=True, ylabel='AU/cm', xlabel='nm',
        ax=None,
        showplot=False, savetofile=None, saveformat='png',
        user_vars=None,
        verbose=0
):
    """ Reference example of how to plot a nanodrop dataframe after reading it with `denovix.csv_to_dataframe()`.

    This is mostly meant as a user reference for how to select and plot data from a dataframe.

    Args:
        df:
        selected_columnnames:
        nm_range:
        xlim:
        ylim:
        normalize: If set to True, normalize each column against the column maximum value.
        normalize_to: Normalize each column the the column's value at this index.
        normalize_range: Normalize each column the the column's average value in this index range.
        linestyles:
        colors:
        markers:
        style_combination_order:
        use_seaborn:
        mpl_style:
        fig_kwargs:
        axes_kwargs:
        plot_kwargs: Dict with figsize, xlim, ylim, etc. Can also pass `ax` to use an existing axes.
            Passed directly as df.plot(**plot_kwargs).
        tight_layout: Adjust figure to use tight layout.
        add_legend:
        ylabel:
        xlabel:
        ax:
        showplot: If True, will invoke pyplot.show() before continuing.
        savetofile: A filename (or list of filenames). If given, will save figure to this/these files.
        saveformat:
        user_vars:
        verbose: The verbosity with which informational messages are printed during function execution.

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
        user_vars['nm_range_str'] = '_all-nm'
    else:
        if not isinstance(nm_range, slice):
            nm_range = slice(*nm_range)
        user_vars['nm_range_str'] = f'_{nm_range.start}-{nm_range.stop}nm'
    if normalize_range and not isinstance(normalize_range, slice):
        print("Normalize_range:", normalize_range)
        normalize_range = slice(*normalize_range)
    if fig_kwargs is None:
        fig_kwargs = {}
    if axes_kwargs is None:
        axes_kwargs = {}
    if plot_kwargs is None:
        plot_kwargs = {}
    if user_vars is None:
        user_vars = {}

    df = df.loc[nm_range, selected_columnnames]

    if mpl_style:
        matplotlib.style.use(mpl_style)

    if use_seaborn:
        import seaborn

    if linestyles or colors or markers:
        parts = {
            'linestyle': linestyles or ('-', ),
            'color': colors or get_default_colors(),
            'marker': markers or ('',),
        }
        print("style parts:")
        pprint(parts)
        print("style_combination_order:", style_combination_order)
        # Need to create list of [
        import itertools
        styles = cycle(product(*[parts[k] for k in style_combination_order]))
        # TODO: We need to have the style specs in the right order, e.g. '--b.' (line, color, marker). Or is it 'b*-' ?
        # TODO: Consider manual plotting instead of using df.plot()
        # styles = [''.join(style) for style, col in zip(styles, df.columns)]
        # Edit: Using pandas.plot(style=styles) is really in-flexible, so I'll plot manually using keywords:
        styles = [dict(zip(style_combination_order, style)) for style, col in zip(styles, df.columns)]
        # raise NotImplementedError("linestyles, colors, and markers have not been implemented!")
        print(f"Using styles:")
        pprint(styles)
    else:
        styles = None

    # We use the dataframe axes index to specify rows and columns.
    # For rows, the index corresponds to the wavelengths, i.e. from 190 nm to 500 nm.
    # For columns, the index corresponds to column headers, e.g. sample names (formatted with header_fmt).
    if normalize_range:
        df = df / df.loc[normalize_range, :].average()
        ylabel = f'Normalized to avg in range {normalize_range!r} nm'
        user_vars['normstr'] = f'_norm{normalize_range.start}-{normalize_range.stop}'
    elif normalize_to:
        print(f"Normalizing each spectrogram to its value at {normalize_to!r} nm.")
        df = df / df.loc[normalize_to, :]
        ylabel = f'Normalized to value at {normalize_to!r} nm'
        user_vars['normstr'] = f'_norm{normalize_to}'
    elif normalize:
        df = df / df.max()
        ylabel = 'Normalized to max'
        user_vars['normstr'] = f'_normalized'
    else:
        user_vars['normstr'] = f'_absorbance'

    # The `style` argument to pandas.plot() is a list of "b-" matplotlib "line style" strings, one string per column.
    # However, matplotlib style strings doesn't support hex colors, only single-letter "rgbcmykw".
    # For that reason, if `styles` is given, we plot manually, rather than using df.plot().
    if styles:
        if ax is None:
            # fig = matplotlib.figure.Figure()  # If you do this, you need to hook up the backend manually :-/
            from matplotlib import pyplot  # Use pyplot API instead..
            print("Creating new figure using fig_kwargs:")
            print(fig_kwargs)
            fig = pyplot.figure(**fig_kwargs)
            print("new figure:", fig)
            print("Adding new axes/subplot using axes_kwargs:")
            print(axes_kwargs)
            ax = fig.add_subplot(111, **axes_kwargs)
            print("new axes:", ax)
        for col, style in zip(df, styles):
            s = df[col].dropna()
            style.update(plot_kwargs)
            ax.plot(s.index, s.values, label=col, **style)  # style: dict with 'linestyle',
    else:
        # Differentiating between "plot_kwargs", "fig_kwargs", and "axes_kwargs" is a paint...
        # Make a combined "plot_kwargs" for df.plot:
        dfplot_kwargs = plot_kwargs.copy()
        for d in (axes_kwargs, fig_kwargs):
            for k, v in d.items():
                if v is not None:
                    dfplot_kwargs.setdefault(k, v)
        # Convert the styles from dict to matplotlib style strings:
        # styles = [f"{d[color]}{d[line]}{d[marker]}" for d in styles]
        # Oh, but colors are often in hex form, not just "b" or "r", which makes it impossible to specify properly.
        # So, for this reason, if we need to use styles, we have to go the route above.
        print("Plotting dataframe using df.plot dfplot_kwargs:")
        print(dfplot_kwargs)
        ax = df.plot(**dfplot_kwargs)

    if ylim:
        ax.set_ylim(*ylim)
        user_vars['ylim_str'] = f'_{ylim[0]}-{ylim[1]}'
    else:
        user_vars['ylim_str'] = f'_full-y'
    if xlim:
        ax.set_xlim(*xlim)
        user_vars['xlim_str'] = f'_{ylim[0]}-{ylim[1]}'
    else:
        user_vars['xlim_str'] = f'_full-y'
    if ylabel:
        ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)
    if add_legend:
        ax.legend()
    if tight_layout is not False:  # Apply by default if unspecified/None
        ax.figure.tight_layout()

    if showplot:
        if verbose > -1:
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
        if saveformat is None:
            saveformat = 'png'
        if isinstance(saveformat, str):
            saveformat = (saveformat,)
        print("\nsavetofile:", savetofile)
        print("\nsaveformat:", saveformat)
        for plotfn in savetofile:
            for ext in saveformat:
                # if verbose:
                user_vars['ext'] = ext
                outputfn = plotfn.format(**user_vars)
                print("Saving plot to file:", outputfn)
                ax.figure.savefig(outputfn)

    return ax


def get_default_colors(default='bgrcmyk'):
    try:
        colors = [c['color'] for c in list(matplotlib.rcParams['axes.prop_cycle'])]
    except KeyError:
        colors = list(matplotlib.rcParams.get('axes.color_cycle', list(default)))
    if isinstance(colors, str):
        colors = list(colors)
    return colors
