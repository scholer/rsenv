"""
Module for resampling signals.
It turns out that just doing a "every Nth value" downsampling is by far the easiest and
generally produces the nicest result.

NOTE: This is all pretty nice, yes, you can find an optimal scaling factor for a given signal.
But that doesn't mean that that same scaling factor works for other signals!


IrfanView uses the following filters for resampling:
* Lanczos (slowest, best quality)
* B-Spline
* Mitchell
* Bell
* Triangle
* Hermite (fastest)

Irfanview has an option to "Use fast resample filter for image shrinking"

TODO: Make a better function that for each sampling point finds the "best/nearest" value.
I think this may just be equivalent to be doing some gaussian/median filtering, but not sure.


"""

import numpy as np
from functools import partial


def rolling_window(a, window):
    """

    Args:
        a:
        window:

    Returns:

    Refs:
    * From http://www.rigtorp.se/2011/01/01/rolling-statistics-numpy.html
    * Numpy sliding window function, proposal: https://github.com/numpy/numpy/issues/7753
    * However, the suggestion was to use Pandas, bottleneck, or scipy.ndimage.
    * http://pandas.pydata.org/pandas-docs/version/0.17.0/generated/pandas.rolling_mean.html
    """
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def downsample_signal(arr, factor, method='point'):
    """

    Args:
        arr:
        factor:
        method:

    Returns:

    Refs:
    * https://docs.obspy.org/_modules/obspy/signal/interpolation.html
        "If used for downsampling, make sure to apply an appropriate anti-aliasing lowpass filter first."
    * https://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.interpolate.html
        > The Trace object has three different methods to change the sampling rate of its data:
        >     resample(), decimate(), and interpolate().
        > Make sure to choose the most appropriate one for the problem at hand.
    * https://stackoverflow.com/questions/30755536/image-2x-downsampling-with-lanczos-filter

    * https://github.com/mubeta06/python/blob/master/signal_processing/sp/multirate.py
        Downsampling is just `s[phase::n]`.

    * https://stackoverflow.com/questions/384991/what-is-the-best-image-downscaling-algorithm-quality-wise
    * http://www.imagemagick.org/Usage/filter/
    * http://www.bvdwolf.nl/foto/resample/example1.html
    * http://www.bvdwolf.nl/foto/resample/down_sample.html
    * https://se.mathworks.com/help/signal/ug/filtering-before-downsampling.html?s_tid=gn_loc_drop
    * http://www.microchip.com/forums/m962175.aspx
    * https://stackoverflow.com/questions/13236983/whats-the-best-filter-for-downsampling-text

    """
    assert len(arr) % factor == 0

    if method == 'point':
        # Sample single points along the signal array:
        return arr[::factor]
    if method == 'box-mean':
        # Average all values in a `factor`-sized window:
        chunks_mean = [np.mean(chunk) for chunk in np.split(arr, factor)]
        return np.array(chunks_mean)
    if method == 'box-median':
        # Average all values in a `factor`-sized window:
        return np.array([np.median(chunk) for chunk in np.split(arr, factor)])
    if method == 'box-max':
        # Average all values in a `factor`-sized window:
        return np.array([np.max(chunk) for chunk in np.split(arr, factor)])


def calc_downsampled_residuals(downsampled, original, xorg=None, xdown=None, factor=None):
    assert len(downsampled) <= len(original)
    assert len(original) % len(downsampled) == 0
    if xorg is None:
        xorg = range(len(original))
    if factor is None:
        factor = len(original) // len(downsampled)
    if xdown is None:
        # Assume regular intervals, e.g. for 10x downsampled, take every 10th x-value.
        xdown = xorg[::factor]
    assert len(xdown) == len(downsampled)
    yinterp = np.interp(x=xorg, xp=xdown, fp=downsampled)
    return np.array(original) - yinterp


def calc_downsampled_rsquared(downsampled, original, xorg=None, xdown=None, factor=None):
    """ Return the sum of squared residuals, effectively the error between a downsampled signal and the original. """
    residuals = calc_downsampled_residuals(
        downsampled=downsampled, original=original, xorg=xorg, xdown=xdown, factor=factor)
    # return errors: root-mean-square of residuals.
    return np.sum(residuals ** 2)


def calc_downsampled_error(downsampled, original, xorg=None, xdown=None, factor=None, mean=True):
    residuals = calc_downsampled_residuals(
        downsampled=downsampled, original=original, xorg=xorg, xdown=xdown, factor=factor)
    if mean:
        error = np.mean(np.sum(residuals ** 2) / len(original))
    else:
        error = np.mean(np.sum(residuals ** 2))
    return error


def calc_downsampling_range_errors(ys, xs, search_range, downsampling_function, normalize=True):
    """
    Args:
        ys:
        xs:
        search_range:
        downsampling_function: Must take two args, `x` and `q`,
            where `x` is the original signal, and `q` is the downscaling factor.
        normalize:
    """
    # Remove downscaling factors that does not factor the length of ys:
    if normalize:
        # normalize the values array:
        ys = ys / np.max(ys)
    is_good = np.mod(len(ys), search_range) == 0
    search_range = search_range[is_good]

    errors = np.array([
        calc_downsampled_error(
            downsampled=downsampling_function(ys, dsf),
            original=ys,
            xorg=xs,
            factor=dsf, mean=True)
        for dsf in search_range])
    return search_range, errors


def score_downsamplings(factors, errors, acceptable_error=0.0001):
    # TODO: Find consistent scoring function!
    return factors / (errors + acceptable_error)


def find_optimal_downsampling(ys, func, xs=None, search_range=None):
    if search_range is None:
        search_range = np.arange(0, 100)
    if isinstance(search_range, tuple):
        search_range = np.arange(*search_range)

    # Calculate errors:
    factors, errors = calc_downsampling_range_errors(ys, xs, search_range, downsampling_function=func)
    # Normalize sum by length of input values array:
    # score: add 1 to errors to prevent division by zero.
    scores = score_downsamplings(factors, errors)
    bestchoice = np.argmax(scores)
    return bestchoice, factors[bestchoice], scores[bestchoice]
