# Copyright 2017-2018 Rasmus Scholer Sorensen

"""

Module for plotting and visualizing HPLC chromatograms.

"""

import pandas as pd
import xarray
import seaborn
from matplotlib import pyplot


def get_x_y_from_chromatogram_dataset(ds):
    if isinstance(ds, dict):
        # We have a dict with 'metadata', 'timepoints', 'signal_values':
        x, y = ds['timepoints'], ds['signal_values']
    elif isinstance(ds, pd.DataFrame):
        x, y = ds.index, ds.signal_values if 'signal_values' in ds else ds.ordinate_values
    elif isinstance(ds, xarray.Dataset):
        # Assume xarray Dataset directly from CDF file.
        x, y = ds.point_number, ds.ordinate_values
    else:
        # Assume a list/tuple of (x, y, [metadata], ...])
        x, y, *other = ds
    return x, y


def plot_chromatograms(
        chromatograms,
        ax=None, figsize=(14, 10), tight_layout=True, subplots_kwargs=None,
        plotting_kwargs=None,
        colors=None,
        ylabel='mAU',
        fractions=None,
        fractions_label_column='well',
        fractions_label_height='80%',
        fractions_labels_kwargs=None, fractions_labels_enabled=True,
        fractions_vspan_kwargs=None, fractions_vspan_enabled=True,
        fractions_vlines_kwargs=None, fractions_vlines_enabled=True,
):
    """ Plot chromatograms from a DataFrame. Simple, reference function.

    Args:
        chromatograms: DataFrame, dict, or list of chromatogram data to plot.
        ax: The axis to plot on. If None, a new figure and axis will be created.
        figsize: The figure size, if creating a new figure and axis.
        tight_layout: If true, apply tight layout to the figure after plotting.
        **kwargs: All other arguments are passed to the plotting function.

    Returns:
        Pyplot axis where the dataframe chromatograms series were plotted on.
        A new figure and axis is created if no axis were provided.

    Refs:
    * https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.plot.html
    * https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.plot.html

    """
    from matplotlib import pyplot
    if subplots_kwargs is None:
        subplots_kwargs = {}
    if plotting_kwargs is None:
        plotting_kwargs = {}
    if ax is None:
        subplots_kwargs.setdefault('figsize', figsize)
        fig, ax = pyplot.subplots(1, 1, **subplots_kwargs)
    if isinstance(chromatograms, pd.DataFrame):
        chromatograms.plot(ax=ax, **plotting_kwargs)
    elif isinstance(chromatograms, dict):
        for label, ds in chromatograms.items():
            x, y = get_x_y_from_chromatogram_dataset(ds)
            pyplot.plot(x, y, label=label)
    else:
        raise ValueError(f"Datatype `{type(chromatograms)}` for `chromatograms` argument not recognized.")
    # Pandas doesn't have great support for units, see https://github.com/pandas-dev/pandas/issues/10349
    if ylabel:
        ax.set_ylabel(ylabel)
    if fractions is not None:
        if fractions_vlines_kwargs is None:
            fractions_vlines_kwargs = {}
        fractions_vlines_kwargs.setdefault('linewidth', 1.0)
        fractions_vlines_kwargs.setdefault('alpha', 0.5)
        fractions_vlines_kwargs.setdefault('color', 'k')
        if fractions_vspan_kwargs is None:
            fractions_vspan_kwargs = {}
        fractions_vspan_kwargs.setdefault('alpha', 0.1)
        fractions_vspan_kwargs.setdefault('color', 'b')
        if fractions_labels_kwargs is None:
            fractions_labels_kwargs = {}
        fractions_labels_kwargs.setdefault('fontsize', 'medium')
        fractions_labels_kwargs.setdefault('rotation', 60)
        fractions_labels_kwargs.setdefault('rotation_mode', 'anchor')
        if isinstance(fractions_label_height, str):
            if fractions_label_height.endswith('%'):
                fractions_label_height = float(fractions_label_height.strip('%')) * 0.01 * ax.get_ylim()[1]
            else:
                fractions_label_height = float(fractions_label_height)
        # Assume fractions DataFrame for now:
        for rowidx, row in fractions.iterrows():
            if fractions_vlines_enabled is not False:
                ax.axvline(x=row.start, **fractions_vlines_kwargs)  # axvline(), but vlines(), notice singular/plural.
                ax.axvline(x=row.end, **fractions_vlines_kwargs)
            if fractions_vspan_enabled is not False:
                ax.axvspan(xmin=row.start, xmax=row.end, **fractions_vspan_kwargs)
            if fractions_labels_enabled is not False:
                ax.text(
                    # This should be in axis units, right:
                    x=row.start + 0.1 * (row.end - row.start),
                    y=fractions_label_height,
                    s=row[fractions_label_column],
                    **fractions_labels_kwargs
                )
    if tight_layout:
        ax.figure.tight_layout()
    return ax


