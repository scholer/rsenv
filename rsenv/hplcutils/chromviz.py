# Copyright 2017-2018 Rasmus Scholer Sorensen

"""

Module for plotting and visualizing HPLC chromatograms.

"""


def plot_chromatograms_df(df, ax=None, figsize=(14, 10), **kwargs):
    """ Plot chromatograms from a DataFrame. Simple, reference function.

    Args:
        df:
        ax:
        figsize:
        **kwargs: All other arguments are passed to the `df.plot()` function.

    Returns:
        Pyplot axis where the dataframe chromatograms series were plotted on.
        A new figure and axis is created if no axis were provided.

    Refs:
    * https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.plot.html
    * https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.plot.html

    """
    from matplotlib import pyplot
    if ax is None:
        fig, ax = pyplot.subplots(1, 1, figsize=figsize, **kwargs)
    df.plot(ax=ax)
    return ax


