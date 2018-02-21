


def plot_chromatograms_df(df, ax=None, figsize=(14, 10), **kwargs):
    """

    Args:
        df:
        ax:
        figsize:
        colors:
        **kwargs:

    Returns:


    Refs:
    * https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.plot.html
    * https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.plot.html

    """
    from matplotlib import pyplot
    if ax is None:
        fig, ax = pyplot.subplots(1, 1, figsize=figsize, **kwargs)
    df.plot(ax=ax)
    return ax


