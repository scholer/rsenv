
import click
import numpy as np
import yaml
from matplotlib import pyplot
import logging
logger = logging.getLogger(__name__)
try:
    import click_log
    click_log.basic_config(logger)
except ImportError:
    logging.basicConfig()

from .io import load_hplc_aia_xr_dataframe
from .gelviz import make_gel_from_datasets, npimg_to_pil, show_gel
from .chromviz import plot_chromatograms_df


@click.command()
@click.argument('aia_dir', type=click.Path(exists=True))
@click.option('--outputfn', default="{aia_dir}.png")
@click.option('--pyplot-fontsize', default="medium")
@click.option('--pyplot-fn', default="{aia_dir}_pyplot.png")
@click.option('--pyplot-show/--no-pyplot-show', default=True)
@click.option('--print-samplenames/--no-print-samplenames', default=True)
@click.option('--save-annotations/--no-save-annotations', default=True)
@click.option('--save-gaml/--no-save-gaml', default=True)
@click.option('--verbose', '-v', count=True)
@click.option('--plot-chromatogram/--no-plot-chromatogram', default=False)
@click.option('--chromatogram-outputfn', default="{aia_dir}.chrom-overlay.png")
@click.option('--convert-to-actual-time/--no-convert-to-actual-time', default=False)
def hplc_to_pseudogel_cli(
        aia_dir,
        signal_filter=None,
        signal_scaling=None,
        signal_downsampling=20,
        baseline_correction='minimum',
        gel_blur=None,
        flip_v=False,
        outputfn="{aia_dir}.png",
        pyplot_fn="{aia_dir}_pyplot.png",
        pyplot_fontsize='medium',
        pyplot_show=True,
        plot_chromatogram=False,
        chromatogram_outputfn="{aia_dir}.chrom-overlay.png",
        print_samplenames=True,
        save_annotations=True,
        save_gaml=True,
        convert_to_actual_time=False,
        verbose=2,
):
    """ Create a "pseudo" gel image from HPLC chromatograms (exported as AIA/CDF format).

    Args:
        aia_dir: The .AIA directory containing the chromatograms as .CDF files.
        signal_filter:
        signal_scaling:
        signal_downsampling:
        baseline_correction:
        gel_blur:
        flip_v:
        outputfn:
        pyplot_fn:
        pyplot_fontsize:
        pyplot_show:
        print_samplenames:
        save_annotations:
        save_gaml:
        verbose:

    Returns:

    """
    try:
        pyplot_fontsize = int(pyplot_fontsize)
    except ValueError:
        try:
            pyplot_fontsize = float(pyplot_fontsize)
        except ValueError:
            pass
    df = load_hplc_aia_xr_dataframe(aia_dir, verbose=verbose, convert_to_actual_time=convert_to_actual_time)
    if plot_chromatogram:
        ax = plot_chromatograms_df(df)
        if chromatogram_outputfn:
            chromatogram_outputfn = chromatogram_outputfn.format(aia_dir=aia_dir)
            ax.figure.savefig(chromatogram_outputfn)
        else:
            pyplot.show()
    params = {}
    gel_array = make_gel_from_datasets(
        data=df,
        signal_downsampling=signal_downsampling,
        baseline_correction=baseline_correction,
        lane_width=0.10, lane_spacing=0.04, margin_width=0.12,
        gaussian=gel_blur,
        out_params=params,
        pyplot_show=False,
        print_samplenames=print_samplenames,
        verbose=verbose,
    )
    print("\nParams:")
    print(params)

    if pyplot_show:
        if pyplot_fn:
            pyplot_fn = pyplot_fn.format(aia_dir=aia_dir)
        show_gel(
            gel_image=gel_array, outputfn=pyplot_fn, verbose=verbose,
            lane_annotations=params.get('samplenames'), fontsize=pyplot_fontsize,
            **params
        )
    if verbose:
        print("Converting numpy array to Pillow image...")
    # pil_img = npimg_to_pil(gel_array, output_dtype=np.float64, invert=False, mode='F')
    # pil_img = npimg_to_pil(gel_array, output_dtype=np.uint8, invert=False, mode='L')
    pil_img = npimg_to_pil(gel_array, output_dtype=np.uint8, invert=True, mode='L', verbose=verbose)

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
        outputfn = outputfn.format(aia_dir=aia_dir)
        print("\nSaving gel image to file:", outputfn)
        pil_img.save(outputfn)

    # if print_samplenames:
    #     print("\nSample Names:")
    #     print("\n".join(f"  {n}" for n in params['samplenames']))

    if save_annotations:
        annotations_fn = aia_dir + '.annotations.txt'
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
        gaml_fn = aia_dir + '.gaml'
        print("Saving GelAnnotator GAML configuration to file:", gaml_fn)
        with open(gaml_fn, 'w') as fd:
            yaml.dump(gaml, fd)
