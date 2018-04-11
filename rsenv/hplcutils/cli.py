
import click
import os
import pathlib
import numpy as np
import yaml
from matplotlib import pyplot
import PIL.ImageOps
import logging
logger = logging.getLogger(__name__)
try:
    import click_log
    click_log.basic_config(logger)
except ImportError:
    logging.basicConfig()

from .io import load_hplc_aia_xr_dataframe
from .gelviz import make_gel_from_datasets, show_gel, adjust_contrast_range  # npimg_to_pil,
from .chromviz import plot_chromatograms_df


# CLI, available as `hplc-to-pseudogel`
@click.command()
@click.argument('cdf_files_or_dir', nargs=-1, type=click.Path(exists=True))  # Use nargs=-1 for many / '*'.
@click.option('--runname-fmt', default='{i:02} {ds.sample_name}')
@click.option('--selection-query', '-q', multiple=True)
@click.option('--selection-method', default='glob')
@click.option('--sort-columns/--no-sort-columns')
@click.option('--convert-to-actual-time/--no-convert-to-actual-time', default=True)
@click.option('--convert-seconds-to-minutes/--no-convert-seconds-to-minutes', default=True)
@click.option('--crop-range', '-r', default=None, nargs=2, type=float)  # Defaults to empty tuple, not None.
@click.option('--nan-correction', default='dropna')
@click.option('--nan-fill-value', default=0)
@click.option('--nan-interpolation-method', default='linear')
@click.option('--baseline-correction', default='minimum')
@click.option('--gel-blur', default=None, type=float)
@click.option('--flip-v/--no-flip-v', default=False, help="Flip image, so the earliest peaks are at the bottom.")
@click.option('--invert-image/--no-invert-image', default=True, help="Use inverted image (black bands on white).")
@click.option('--contrast-percentiles', default=None, nargs=2, type=float,
              help="Contrast range, values in 0.0--1.0. Default is (0.0, 1.0). Upper limit of 0.995 is usually good.")
@click.option('--fnprefix', default=None, help="A common prefix to use when creating filenames.")
@click.option('--outputfn', default="{fnprefix}-ds{downsampling}.png", help="The plain pseudogel png image.")
@click.option('--pyplot-show/--no-pyplot-show', default=True, help="Show and annotate gel with pyplot.")
@click.option('--pyplot-show-adjusted/--no-pyplot-show-adjusted', default=True, help="Pyplot show contrast-adjusted image.")
@click.option('--pyplot-show-colorbar/--no-pyplot-show-colorbar', default=False, help="Add colorbar to the pyplot figure.")
@click.option('--pyplot-show-colormap', default=None, help="The colormap to use for the pyplot figure.")
@click.option('--pyplot-gel-fn', default="{fnprefix}-ds{downsampling}_pyplot.png")
@click.option('--pyplot-fontsize', default="medium", help="Font size for annotated psuedogel made with pyplot.")
@click.option('--plot-chromatograms/--no-plot-chromatograms', default=True)
@click.option('--chromatograms-outputfn', default="{fnprefix}-ds{downsampling}_chromatograms.png")
@click.option('--print-samplenames/--no-print-samplenames', default=True)
@click.option('--save-annotations/--no-save-annotations', default=True)
@click.option('--save-gaml/--no-save-gaml', default=True)
@click.option('--verbose', '-v', count=True)
def hplc_to_pseudogel_cli(
        cdf_files_or_dir,
        runname_fmt="{i:02} {ds.sample_name}",
        selection_query=None,
        selection_method='glob',
        sort_columns=False,
        signal_downsampling=20,
        crop_range=None,
        convert_to_actual_time=True,
        convert_seconds_to_minutes=True,
        nan_correction='dropna', nan_fill_value=0, nan_interpolation_method='linear',
        baseline_correction='minimum',
        gel_blur=None,
        flip_v=False,
        invert_image=True,
        contrast_percentiles=None,
        fnprefix='',
        outputfn="{fnprefix}-ds{downsampling}.{ext}",  # Filename for plain pseudogel PNG image.
        pyplot_show=True,  # TODO: This actually toggles whether to create the annotated gel plot, now just show it.
        pyplot_show_adjusted=True,
        pyplot_show_colormap=None,
        pyplot_show_colorbar=False,
        pyplot_gel_fn="{fnprefix}-ds{downsampling}_pyplot.png",  # Pseudogel, annotated with pyplot.
        pyplot_fontsize='medium',  # Annotation font size.
        plot_chromatograms=True,
        chromatograms_outputfn="{fnprefix}-ds{downsampling}_chromatograms.png",
        print_samplenames=True,
        save_annotations=True,
        save_gaml=True,
        verbose=2,
):
    """ Create a "pseudo" gel image from HPLC chromatograms (exported as AIA/CDF format).
        nan_correction=nan_correction, nan_fill_value=nan_fill_value, nan_interpolation_method=nan_interpolation_method,
        runname_fmt=runname_fmt,
        signal_range_crop=crop_range,
        selection_query=selection_query, selection_method=selection_method

    Args:
        cdf_files_or_dir: The .AIA directory containing the chromatograms as .CDF files.
        runname_fmt: How to name each dataset / lane. Formatting variables include `i`, and `ds`,
            where ds has all the dataset attributes available from ChemStation AIA export.
        selection_query:
        selection_method:
        sort_columns: Whether to sort columns (lexicographically, using column names produced by `runname_fmt`).
        signal_downsampling: Downsample the signal by this factor.
            The time resolution of HPLC chromatograms is often very high, typically tens of Hz.
            Without downsampling or cropping, the gel image would be very big, e.g. 18000 x 10000 pixels.
        crop_range: Crop the signal to this time range before using it to create a lane for the gel image.
        convert_to_actual_time: Convert the signal index to seconds. If False, the index is just a range 0..N.
        convert_seconds_to_minutes:
        nan_correction:
        nan_fill_value:
        nan_interpolation_method:
        baseline_correction: Perform this baseline correction to the signal before creating a lane from it.
        gel_blur:
        flip_v:
        invert_image: Invert the gel. True means black bands on a white gel.
            For pyplot_show, this can also be controlled by specifying a reversed/inverted colormap, e.g. greys_r.
            But obviously that doesn't change the "clean", un-annotated pseudogel.
        fnprefix: A constant prefix that can be used for filename formats.
        outputfn: Save the generated pseudogel to this filename.
        pyplot_show: Show and annotate gel with pyplot.
        pyplot_show_adjusted: Use contrast-adjusted image when showing values with pyplot (is NOT quantitative).
        pyplot_gel_fn: Save pyplot annotated gel figure under this filename.
        pyplot_fontsize: Font size to use when annotating gel with pyplot.
        plot_chromatograms: Plot chromatograms, as traditional line plots. Good for QA.
        chromatograms_outputfn: Save plotted chromatograms to this filename.
        print_samplenames: Print samplenames.
        save_annotations: Save the generated sample names to this file.
        save_gaml: If specified, will save an initial .gaml file with margin etc, for use with GelUtils/GelAnnotator.
        verbose: Controls the verbosity with which informational messages are printed during process.

    Returns:
        None

    """
    # TODO: Implement plotting downsampled signals using `out_signals`.
    if len(cdf_files_or_dir) == 0:
        print("No CDF files or AIA directories given, aborting pseudogel creation...")
        return
    try:
        pyplot_fontsize = int(pyplot_fontsize)
    except ValueError:
        try:
            pyplot_fontsize = float(pyplot_fontsize)
        except ValueError:
            pass
    if isinstance(cdf_files_or_dir, (str, pathlib.Path)):
        cdf_files_or_dir = [cdf_files_or_dir]

    if fnprefix is None:
         fnprefix = cdf_files_or_dir[0] if len(cdf_files_or_dir) == 1 else "hplc-pseudogel"

    # '_pseudogel-ds{signal_downsampling}.png'
    # not including 'ds', since it is also used as a variable name for datasets:
    fmt_params = dict(fnprefix=fnprefix, ext='png', downsampling=signal_downsampling)
    outputfn = outputfn.format(**fmt_params)
    pyplot_gel_fn = pyplot_gel_fn.format(**fmt_params)
    chromatograms_outputfn = chromatograms_outputfn.format(**fmt_params)
    annotations_fn = "{fnprefix}-ds{downsampling}.annotations.txt".format(**fmt_params)
    gaml_fn = "{fnprefix}-ds{downsampling}.gaml".format(**fmt_params)
    print(f"cdf_files_or_dir:", cdf_files_or_dir)
    print(f"outputfn:", outputfn)
    print(f"pyplot_gel_fn:", pyplot_gel_fn)

    # Load CDF files in AIA dir as a Pandas DataFrame:
    df = load_hplc_aia_xr_dataframe(
        cdf_files_or_dir,
        runname_fmt=runname_fmt,
        selection_query=selection_query, selection_method=selection_method, sort_columns=sort_columns,
        convert_to_actual_time=convert_to_actual_time, convert_seconds_to_minutes=convert_seconds_to_minutes,
        nan_correction=nan_correction, nan_fill_value=nan_fill_value, nan_interpolation_method=nan_interpolation_method,
        signal_range_crop=crop_range,
        verbose=verbose,
    )
    # print("df.index[0], df.index[-1]:", df.index[0], df.index[-1])  # Yes, is in minutes.
    if plot_chromatograms:
        ax = plot_chromatograms_df(df)
        if chromatograms_outputfn:
            chromatograms_outputfn = chromatograms_outputfn.format(
                aia_dir=cdf_files_or_dir, signal_downsampling=1, ds=1)
            ax.figure.savefig(chromatograms_outputfn)
        else:
            pyplot.show()
    params = {}
    out_signals = []
    if verbose:
        print("Making gel from datasets...")
    gel_array = make_gel_from_datasets(
        data=df,
        signal_downsampling=signal_downsampling,
        baseline_correction=baseline_correction,
        lane_width=0.10, lane_spacing=0.04, margin_width=0.12,
        img_gaussian=gel_blur,
        out_params=params,  # Store information about pseudogel parameters, for e.g. GelAnnotator .gaml file.
        out_signals=out_signals,  # Capture downsampled signals for QA/debugging.
        pyplot_show=False,
        print_samplenames=print_samplenames,
        verbose=verbose,
    )
    assert gel_array.shape[0] * signal_downsampling == len(df)  # len(df) is number of rows.
    if plot_chromatograms and signal_downsampling not in (None, 0, 1):
        # Plot downsampled chromatograms, QA ensuring downsampled signals capture essence of original chromatograms.
        # ax = plot_chromatograms_df(df)
        # if chromatograms_outputfn:
        #     chromatograms_outputfn = chromatograms_outputfn.format(
        #         aia_dir=cdf_files_or_dir, signal_downsampling=1, ds=1)
        #     ax.figure.savefig(chromatograms_outputfn)
        # else:
        #     pyplot.show()
        pass
    # print("\nAnnotated gel visualization params:")
    # print(params)

    if contrast_percentiles:
        if isinstance(contrast_percentiles, (int, float)):
            dr_low, dr_high = 0, contrast_percentiles
        elif len(contrast_percentiles) == 1:
            dr_low, dr_high = 0, contrast_percentiles[0]
        else:
            dr_low, dr_high = contrast_percentiles
    else:
        dr_low, dr_high = 0, 1

    # Contrast-, type-, and value-range adjusted numpy array:
    gel_array_adj = adjust_contrast_range(
        gel_array, output_dtype=np.uint8,
        dr_low=dr_low, dr_high=dr_high, percentiles=True, invert=invert_image,
        verbose=verbose
    )
    if pyplot_show:
        # y-axis ticks (in pixel units) and corresponding labels (in minutes):
        y_ticks = np.linspace(0, gel_array.shape[0], 9)  # in gel pixel units
        y_labels = [f"{lbl:0.01f}" for lbl in np.linspace(df.index[0], df.index[-1], 9)]
        if pyplot_show_colormap is None:
            pyplot_show_colormap = 'Greys_r' if (invert_image and pyplot_show_adjusted) else 'Greys'
        show_gel(
            gel_image=(gel_array_adj if pyplot_show_adjusted else gel_array),
            outputfn=pyplot_gel_fn, verbose=verbose,
            y_ticks_and_labels=(y_ticks, y_labels),
            lane_annotations=params.get('samplenames'), fontsize=pyplot_fontsize,
            cmap=pyplot_show_colormap, colorbar=pyplot_show_colorbar,
            **params
        )

    if verbose:
        print("Converting numpy array to Pillow image...")
    pil_img = PIL.Image.fromarray(gel_array_adj, mode='L')  # # Did not work: mode='F' with output_dtype=np.float64

    if flip_v:
        pil_img = PIL.ImageOps.flip(pil_img)  # Not to be confused with 'mirror', which is flip-h.

    # DEBUG:
    print("pil_img.dtype:", np.array(pil_img).dtype)
    print("pil_img mean :", np.array(pil_img).mean())
    print("pil_img max  ", np.array(pil_img).max())
    # from matplotlib import pyplot
    # fig, (ax1, ax2) = pyplot.subplots(1, 2, figsize=(12, 14))
    # ax1.imshow(gel_array, cmap='Greys')
    # ax2.imshow(np.array(pil_img), cmap='Greys')
    # pyplot.show()

    if outputfn:
        outputfn = outputfn.format(aia_dir=cdf_files_or_dir)
        print("\nSaving gel image to file:", outputfn)
        pil_img.save(outputfn)

    # if print_samplenames:
    #     print("\nSample Names:")
    #     print("\n".join(f"  {n}" for n in params['samplenames']))

    if save_annotations:
        print("\nSaving lane annotations to file:", annotations_fn)
        with open(annotations_fn, 'w') as fd:
            fd.write("\n".join(params['samplenames']))
    else:
        annotations_fn = None
    if save_gaml:
        # GelAnnotator gaml (YAML) configuration
        gaml = {
            'xmargin': params['margin_width'],
            'xspacing': params['lane_width'] + params['lane_spacing'],
            'gelfile': outputfn,
            'pngfile': outputfn,
            'reusepng': True,  # Do not use the gel input file, disables all transformation.
            'annotationsfile': annotations_fn,
            'dynamicrange': [0, 255],
            'linearize': False,
        }
        print("Saving GelAnnotator GAML configuration to file:", gaml_fn)
        with open(gaml_fn, 'w') as fd:
            yaml.dump(gaml, fd)


