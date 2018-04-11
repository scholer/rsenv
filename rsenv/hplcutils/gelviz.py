# Copyright 2018 Rasmus Scholer Sorensen

"""

Module for visualizing HPLC chromatograms as a synthesized 'pseudo' gel image.

This makes it easier to visualize many chromatograms side by side, as an alternative
to the usual overlayed chromatograms visualization mode.

This is basically the reverse process of creating lane profiles from gel images.



"""
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


def make_gel_from_datasets(
        data,
        baseline_correction='minimum',
        signal_downsampling=None,
        sig_gaussian=1,
        img_gaussian=1,
        lane_width=20, lane_spacing=10, margin_width=30,
        # contrast_percentiles=None,  # Edit, is done in npimg_to_pil
        pyplot_show=True,
        add_lane_annotations=True,
        print_samplenames=False,
        out_params=None, out_signals=None,
        verbose=0,
):
    """ Make a 2D 'pseudogel' image from a list of 1D chromatogram signals.

    Args:
        data: The data to use to create a gel from. Must be either a dict(samplename=(t, y)) or DataFrame.
        baseline_correction: Perform baseline correction using this method (name).
        signal_downsampling: Signal downsampling factor to apply to each signal before creating the gel.
        sig_gaussian: Apply a gaussian blur to the input signals before using them to generate the gel.
        img_gaussian: Apply a gaussian to the final image. This can be used to make the bands appear more natural.
        lane_width: The desired width (in pixels) of each generated lane.
        lane_spacing: The desired space (in pixels) between each generated lane.
        margin_width: The margin (in width) from the right- and leftmost lane to the edge of the gel image.
        pyplot_show: Show the generated gel using pyplot.
        add_lane_annotations: Add lane annotations to the figure shown with pyplot.
        out_params: If you want to capture psuedogel generation parameters, provide a dict and they will be saved here.

    Returns:
        gel_array, 2D numpy array.

    A note about data size and down-sampling:
        HPLC data often have much sharper peaks than gel electrophoresis.
        It is not uncommon for HPLC chromatograms to have very fast sampling frequency,
        and often tens of thousands of time points.
        Visualizing an image more than 10k pixels in height is neither convenient nor necessary.
        It is thus recommended to down-sample the chromatogram (as much
        as possible without degrading signal details), before creating a gel image with it.
        After downs-sampling, bands/peaks are typically only 1-2 pixels high.

    There is a serious risk that naive downsampling (e.g. every 10th point) will not be able to capture the peaks.
    Better ways to downsample should therefore be considered.
    There are two approaches:
        (a) Perform complex calculation during downsampling to determine the value at the downsampled point.
        (b) Perform a filtering of the original image such that naive downsampling "works".
    With most methods, these should be completely equivalent.
    Due to the nature of HPLC chromatograms, where we have a flat but uninportant baseline,
    with important, thin and sharp peaks.
    It may be appropriate to do e.g. a max or percentile90 filter with a window size similar to the downsampling factor,
    to make sure each of the "potentially used" pixel values capture the presence of a peak in the downsampled window.
    Or perhaps `max(val, percentile(window))`?
    This may be somewhat similar to be doing a morphological opening.
    Which is conceptually like having a "rolling ball" on top of the chromatogram.
    Which I had also considered in the context of capturing the "nearest point" for each downsampled window.

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

    # TODO: Automatically detect a suitable signal_downsampling factor if 'auto' (or -1).

    if signal_downsampling and signal_downsampling != 1:
        # A downsampling of factor 1 is a no-op.
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
    if isinstance(out_signals, list):
        out_signals.extend(signals)  # Optionally capture the signals used to create the pseudogel.

    return gel_array


def npimg_to_pil(npimg, mode='L', dr_low=0, dr_high=1.0, verbose=0, **kwargs):
    pilimg = PIL.Image.fromarray(
        adjust_contrast_range(npimg, dr_low=dr_low, dr_high=dr_high, verbose=verbose, **kwargs),
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


def show_gel(
        gel_image,
        outputfn=None,
        verbose=0,
        # Figure, axis and gel image params:
        ax=None,
        figsize_scale=1.0,
        gel_scale=0.5,
        cmap="Greys",
        y_ticks_and_labels=None,  # tuple of (pixel-values, labels)
        x_ticks_and_labels=False,
        # These are generally not recommended, only use for spacial cases:
        tight_layout=False,  # Using tight_layout may interfere with auto-sizing.
        fig_kwargs=None,
        # Lane annotations params:
        annotations_height=200,
        lane_annotations=None,
        lane_width=None, lane_spacing=0, margin_width=0, fontsize='medium',
        **kwargs  # Is just used to capture remaining gel params from make_gel_from_datasets() e.g. lane_height.
):
    """ Show, and optionally annotate and save, pseudogel image with PyPlot.

    Args:
        gel_image: The gel image to show, as 2D numpy array.
        outputfn: Figure output filename.
        verbose: Higher = be more verbose when printing informational messages.
        ax: The axis to plot on. A new figure and axis is created if not provided.
        figsize_scale: Scale the figure, making it smaller or larger. Default is 1.0.
        gel_scale: Scale the gel image. Default is 0.5 meaning a 2x downsampling of original input.
        cmap: The colormap to use when displaying gel image values. Default is grayscale.
        y_ticks_and_labels: Ticks (in pixel units) and labels (strings) for the y-axis.
        x_ticks_and_labels: Ticks (in pixel units) and labels (strings) for the x-axis.
        tight_layout: Invoke tight_layout before returning (not recommended, may interfere with autosizing!)
        fig_kwargs: Custom figure parameters.
        annotations_height: The amount of space to add above the gel for lane annotations, in pixel units.
        lane_annotations: A list of lane annotations.
        lane_width: The width (in pixels) of each lane.
        lane_spacing: Distance between each lane (in pixles).
        margin_width: The distance from the right- and leftmost lanes to the edge of the gel.
        fontsize: Font size for lane annotations.
        **kwargs:

    Returns:
        Pyplot image axis on which the image was plotted/shown.

    """
    # Importing here for now; no reason to import earlier if we don't need matplotlib.
    import matplotlib
    from matplotlib import pyplot
    print("\n\nShowing pyplot image (%s x %s pixels)..." % gel_image.shape)
    if ax is None:
        # fig, ax = pyplot.subplots(1, 1, **fig_kwargs)
        if fig_kwargs is None:
            fig_kwargs = {}
        figsize = fig_kwargs.get('figsize')
        dpi = fig_kwargs.get('dpi', matplotlib.rcParams.get('figure.dpi', 100))
        if not figsize:
            # TODO: Scale figsize according to gel_image size.
            # Remember to add some room for the lane annotations.
            # TODO: Gel image axes is currently placed in the middle. Vertical alignment should be bottom.
            print("gel_image.shape", gel_image.shape)
            annotations_height = annotations_height * bool(lane_annotations)
            figsize = (gel_scale * gel_image.shape[1] + 50*2,  # leave 50 px on each side
                       gel_scale * gel_image.shape[0] + annotations_height + 20)
            image_height_ratio = gel_scale * gel_image.shape[0] / figsize[1]  # ratio of image height to total figure height.
            annotations_height_ratio = annotations_height / figsize[1]
            image_width_ratio = gel_scale * gel_image.shape[1] / figsize[0]
            # Reduce by dpi to get figsize in inches:
            figsize = tuple(val * figsize_scale / dpi for val in figsize)  # dpi = 100.
            print("figsize:", figsize)
            fig_kwargs['figsize'] = figsize  # w, h - e.g. (12, 14)
            fig = pyplot.figure(**fig_kwargs)
            print("image_height_ratio:", image_height_ratio)
            print("image_widht_ratio:", image_width_ratio)
            # [0.05, 0.05, 0.90, image_height_ratio]  # [left, bottom, width, height], in relative figure coordinates.
            # 1-(1-image_width_ratio)/2 == (image_width_ratio + 1)/2
            # width, height: size of the axes, NOT positions. left+width <= 1, bottom+height <= 1
            # ax_pos = [(1-image_width_ratio)/2, 0.05, image_width_ratio, image_height_ratio]
            ax_pos = [(1-image_width_ratio)/2, 1.-image_height_ratio-annotations_height_ratio, image_width_ratio, image_height_ratio]
            print("ax_pos:", ax_pos)
            ax = fig.add_axes(ax_pos)
            print("ax.get_position():", ax.get_position())
        else:
            # Adjust gel image to figure:
            fig, ax = pyplot.subplots(1, 1, **fig_kwargs)
    else:
        fig = ax.figure
    # Pyplot has two built-in ways to plot images: `imshow` and `matshow`.
    imaxes = ax.imshow(gel_image, cmap=cmap)
    assert fig == imaxes.figure
    # fig.subplots_adjust(top=0.8)  # absolute coordinates in relative coordinates (0..1)
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
    if y_ticks_and_labels:
        y_ticks, y_labels = y_ticks_and_labels
        print("y_ticks:", y_ticks)
        print("y_labels:", y_labels)
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
    if x_ticks_and_labels is False:
        ax.set_xticks([])
        ax.set_xticklabels([])
    if tight_layout:
        fig.tight_layout()  # kwargs: pad=0.4, w_pad=0.5, h_pad=1.0, rect,
    if outputfn:
        if verbose:
            print("\nSaving pyplot figure to file:", outputfn)
        fig.savefig(outputfn)
    return imaxes

