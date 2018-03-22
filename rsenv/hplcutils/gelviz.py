
import numpy
import numpy as np
import pandas
import pandas as pd
from scipy.ndimage.filters import gaussian_filter
import PIL
import logging

from .io import load_hplc_aia_xr_dataframe


def get_logger():
    return logging.getLogger(__name__)

from itertools import cycle

# lane_signals = [ys50, ys50, ys50]


def make_gel_from_lane_signals(
        lane_signals,
        lane_width=20, lane_spacing=10, margin_width=40,
        gaussian=1,
        pyplot_show=True
):
    """ Re-create a 2D pseudo gel from 1D lane signals ("profiles").

    A note about data size and down-sampling:
        HPLC data often have much sharper peaks than gel electrophoresis.
        It is not uncommon for HPLC chromatograms to have very fast sampling frequency,
        and often tens of thousands of time points.
        Visualizing an image more than 10k pixels in height is neither convenient nor necessary.
        It is thus recommended to down-sample the chromatogram (as much
        as possible without degrading signal details), before creating a gel image with it.
        After downs-sampling, bands/peaks are typically only 1-2 pixels high.

    Args:
        lane_signals: The lane signals/profiles used to create each lane in the gel.
        lane_width: How wide to make the lanes, in pixels.
        lane_spacing: How much empty space to put between the lanes, in pixels.
        margin_width: How much empty space to put to the left and right of the first and last lanes.
        gaussian: If set and >0, apply a gaussian blur/filter before returning the gel array.
        pyplot_show: If True, show the gel with `pyplot.imshow` before returning.

    Returns:
        gel_array, a 2D array comprising the pseudo-gel.

    """
    lane0_signal = lane_signals[0]
    lane_height = len(lane0_signal)
    assert all(len(signal) == lane_height for signal in lane_signals)

    # Use np.tile() or np.vstack([signal]**width)
    #     lane = np.vstack([ys50]*lane_width)
    assert lane_width > 0
    assert lane_spacing >= 0
    assert margin_width >= 0

    lane_spacer = np.zeros((lane_spacing, lane_height))
    margin = np.zeros((margin_width, lane_height))  # cols, rows

    print("signals shapes:", [s.shape for s in lane_signals])
    print("margin.shape:", margin.shape)
    print("lane_spacer.shape:", lane_spacer.shape)

    first_lane = [np.vstack([lane_signals[0]] * lane_width)]
    # other_lanes = list(*zip(cycle([lane_spacer]), [np.vstack([signal]*lane_width) for signal in lane_signals[1:]]))
    other_lanes = [l for signal in lane_signals[1:] for l in (lane_spacer, np.vstack([signal] * lane_width))]
    # print([a.shape for a in first_lane])
    # print([a.shape for a in other_lanes])

    gel_lanes = np.vstack(first_lane + other_lanes)

    gel_image = np.vstack([margin, gel_lanes, margin]).T

    if gaussian:
        gel_image = gaussian_filter(gel_image, sigma=gaussian)

    return gel_image


def show_gel(
        gel_image, ax=None, cmap="Greys",
        lane_annotations=None,
        lane_width=None, lane_spacing=0, margin_width=0, fontsize='medium',
        outputfn=None,
        verbose=0,
        fig_kwargs=None,
        **kwargs
):
    from matplotlib import pyplot
    print("Showing pyplot image (%s x %s pixels)..." % gel_image.shape)
    if fig_kwargs is None:
        # TODO: Scale figsize according to gel_image size.
        fig_kwargs = {'figsize': (12, 14)}  # w, h
    if ax is None:
        fig, ax = pyplot.subplots(1, 1, **fig_kwargs)
    else:
        fig = ax.figure
    imaxes = ax.imshow(gel_image, cmap=cmap)
    assert fig == imaxes.figure
    fig.subplots_adjust(top=0.8)  # absolute coordinates in relative coordinates (0..1)
    if lane_annotations:
        if verbose:
            print("Adding lane annotations to plot...")
        if lane_width is None:
            print("ERROR: `lane_annotations` provided without providing `lane_width`, cannot add lane annotations.")
        else:
            offset_x = margin_width
            for samplename in lane_annotations:
                text = pyplot.text(
                    x=offset_x + int(0.5 * lane_width), y=-10, s=samplename,
                    fontsize=fontsize, rotation=60, rotation_mode='anchor'
                )
                offset_x += lane_width + lane_spacing
    if outputfn:
        if verbose:
            print("\nSaving pyplot figure to file:", outputfn)
        fig.savefig(outputfn)
    return imaxes


def make_gel_from_datasets(
        data,
        baseline_correction='minimum',
        signal_downsampling=None,
        lane_width=20, lane_spacing=10, margin_width=30,
        gaussian=1,
        pyplot_show=True,
        add_lane_annotations=True,
        print_samplenames=False,
        out_params=None,
        verbose=0,
):
    """

    Args:
        data:
        baseline_correction:
        signal_downsampling:
        lane_width:
        lane_spacing:
        margin_width:
        gaussian:
        pyplot_show:
        add_lane_annotations:
        out_params:

    Returns:
        gel_array, 2D numpy array.

    """
    logger = logging.getLogger(__name__)
    if out_params is None:
        out_params = {}
    # data: dict, OrderedDict, or dataframe.
    if isinstance(data, dict):
        # data[samplename] = (xs, ys)
        samplenames = list(data.keys())
        timeaxes, signals = zip(*data.values())
        # Check that all data uses the same time points (sampling frequency):
    elif isinstance(data, pd.DataFrame):
        print(data.head())
        samplenames = data.columns
        timeaxes = data.index
        if np.any(np.isnan(data.values)):
            if np.all(np.isnan(data.values)):
                logger.warning("data.values for contains only NaN values!")
                print(f"WARNING: Only NaN values in data.values!")
            else:
                logger.warning("data.values for sample %s contains NaN values!")
                print(f"WARNING: NaN values in data.values!")
                print(np.where(np.isnan(data.values)))
            input("Continue?")
        signals = data.values.T
        print("signals.shape:", signals.shape)
    else:
        raise TypeError("Unexpected type of `data` ({}).".format(type(data)))
    # pprint("signals:")
    # print(signals)
    lane_height = len(signals[0])
    assert np.all(np.all(ts == timeaxes[0] for ts in timeaxes[1:]))
    # Check that all signals have the same length:
    assert all(len(signal) == lane_height for signal in signals[1:])
    # Note: You can also use numpy.equal.reduce for the above cases of comparing if all are equal.

    for samplename, signal in zip(samplenames, signals):
        if np.any(np.isnan(signal)):
            if np.all(np.isnan(signal)):
                logger.warning("signal for sample %s contains only NaN values!", samplename)
                print(f"WARNING: Only NaN values in signal for sample {samplename}!")
            else:
                logger.warning("signal for sample %s contains NaN values!", samplename)
                print(f"WARNING: NaN values in signal for sample {samplename}!")
                print(np.where(np.isnan(signal)))

    if baseline_correction:
        baseline_method = np.min
        print(f"\nPerforming '{baseline_correction}' baseline correction...")
        signals = [s - baseline_method(s) for s in signals]

    if signal_downsampling:
        downsampling_remainder = lane_height % signal_downsampling
        try:
            assert downsampling_remainder == 0
        except AssertionError as exc:
            print(f"ERROR, unable to downsample signal of length {lane_height} by factor {signal_downsampling}!"
                  f" (remainder: {downsampling_remainder})""")
            do_trim = input(f"Trim signals by {downsampling_remainder} to nearest multiple of {signal_downsampling}? [Y/n]")
            if do_trim and do_trim.lower()[0] == 'n':
                raise exc
            else:
                lane_height = lane_height - downsampling_remainder
                signals = [s[:lane_height] for s in signals]
        # timeaxes = [t[::signal_downsampling] for t in timeaxes]
        signals = [s[::signal_downsampling] for s in signals]
        lane_height = len(signals[0])

    for samplename, signal in zip(samplenames, signals):
        if np.any(np.isnan(signal)):
            logger.warning("gel_array contains NaN values!")
            print(f"WARNING: NaN values in signal for sample {samplename}!")
            print(np.where(np.isnan(signal)))

    if lane_width < 1:
        lane_width = int(lane_height * lane_width)
        print(" - Calculated lane_width:", lane_width)
    if lane_spacing < 1:
        lane_spacing = int(lane_height * lane_spacing)
        print(" - Calculated lane_spacing:", lane_spacing)
    if margin_width < 1:
        margin_width = int(lane_height * margin_width)
        print(" - Calculated margin_width:", margin_width)

    gel_array = make_gel_from_lane_signals(
        lane_signals=[np.array(s) for s in signals],
        lane_width=lane_width, lane_spacing=lane_spacing, margin_width=margin_width
    )
    if np.any(np.isnan(gel_array)):
        logger.warning("gel_array contains NaN values!")
        print("WARNING: NaN values in gel_array!")
        print(np.where(np.isnan(gel_array)))

    if print_samplenames:
        print("\nSample names:")
        print("\n".join(f" - {n}" for n in samplenames))

    if pyplot_show:
        show_gel(
            gel_image=gel_array, lane_annotations=list(samplenames),
            lane_width=lane_width, lane_spacing=lane_spacing, margin_width=margin_width,
            verbose=verbose,
        )

    out_params.update({
        'lane_height': lane_height,
        'lane_width': lane_width,
        'lane_spacing': lane_spacing,
        'margin_width': margin_width,
        'samplenames': list(samplenames),  # In case we have a pd.Index, convert to list
    })

    return gel_array


def npimg_to_pil(npimg, mode='L', dr_high=1.0, verbose=0, **kwargs):
    pilimg = PIL.Image.fromarray(
        adjust_contrast_range(npimg, dr_high=dr_high, verbose=verbose, **kwargs),
        mode=mode
    )
    return pilimg


def adjust_contrast_range(
        npimg,
        dr_low=0, dr_high=None, percentiles=True,
        minval=0, maxval=255, invert=True,
        out=None, output_dtype=np.uint8, output_mode=None,
        verbose=0,
):
    logger = logging.getLogger(__name__)
    logger.debug("Output minval, maxval: %s, %s", minval, maxval)
    logger.debug("Dynamic range (dr_low, dr_high): %s, %s", dr_low, dr_high)
    if dr_high is None:
        dr_high = 0.995
        percentiles = True
    elif percentiles is None:
        percentiles = (0 <= dr_low <= 1) and (0 <= dr_high <= 1)
    if percentiles:
        print(f"\nDynamic range percentiles: {dr_low} - {dr_high}")
        if np.any(np.isnan(npimg)):
            logger.warning("npimg array contains NaN values!")
            print("WARNING: NaN values in npimg array!")
            print(np.where(np.isnan(npimg)))
        if 0 < dr_low < 1:
            dr_low = np.percentile(npimg, dr_low*100)
        if 0 < dr_high <= 1:
            dr_high = np.percentile(npimg, dr_high*100)
        if verbose:
            print(f"Dynamic range: {dr_low} - {dr_high}")
    npimg = np.clip(npimg, dr_low, dr_high)
    if out is None:
        out = np.ndarray(npimg.shape, dtype=output_dtype)
    if invert:
        out[:] = (maxval * (dr_high - npimg)) / (dr_high - dr_low)
    else:
        out[:] = (float(maxval) * (npimg - dr_low) / (dr_high - dr_low) + minval)
    return out


def adjust_contrast_range_vec(npimg, dr_low=0, dr_high=None, minval=0, maxval=255, invert=True, output_mode=None):
    logger = logging.getLogger(__name__)
    logger.debug("Output minval, maxval: %s, %s", minval, maxval)
    logger.debug("Dynamic range (dr_low, dr_high): %s, %s", dr_low, dr_high)
    # This implementation uses a vectorized function to perform value conversion.
    # It could probably also be done by first doing a np.clamp and then a normal operation.
    # Define closure to adjust the values, depending on whether to invert the image:
    if invert:
        def adjust_fun(val):
            """ Function to adjust dynamic range of image, inverting the image in the process. """
            if val <= dr_low:
                return maxval  # This is correct when we are inverting the image.
            elif val >= dr_high:
                return minval  # This is correct when we are inverting the image.
            # This might also be an issue: maxval*70000 > 2**32 ??
            return (maxval * (dr_high - val)) / (dr_high - dr_low)

        logger.debug('Using adjust_fun that will invert the pixel values...')
    else:
        def adjust_fun(val):
            """ Function to adjust dynamic range of image. """
            if val <= dr_low:
                return minval
            elif val >= dr_high:
                return maxval
            else:
                # return maxval*(val-dr_low)/(dr_high-dr_low)+minval
                return int(float(maxval) * (val - dr_low) / (dr_high - dr_low) + minval)
    # Numpy adjustment:
    # Note: This seems correct when I try it manually and plot it.
    adjust_vec = numpy.vectorize(adjust_fun)
    npimg = adjust_vec(npimg)

    return npimg
