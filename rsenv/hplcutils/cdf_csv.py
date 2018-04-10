

import os
import glob
import pathlib
import click

from rsenv.hplcutils.io import load_hplc_aia_xr_dataframe


@click.command()
@click.argument('cdf_files_or_dir', type=click.Path(exists=True), nargs=-1)
@click.option('--outputfn', default=None)
@click.option('--runname-fmt', default='{i:02} {ds.sample_name}')
@click.option('--selection-query', '-q', multiple=True)
@click.option('--selection-method', default='glob')
@click.option('--convert-to-actual-time/--no-convert-to-actual-time', default=True)
@click.option('--convert-seconds-to-minutes/--no-convert-seconds-to-minutes', default=True)
@click.option('--crop-range', '-c', default=None, nargs=2, type=float)  # Doesn't seem to default to None
@click.option('--nan-correction', default='dropna')
@click.option('--nan-fill-value', default=0)
@click.option('--nan-interpolation-method', default='linear')
@click.option('--sort-columns/--no-sort-columns')
@click.option('--csv-sep', '-s', default=',')
@click.option('--verbose', '-v', count=True)
def cdf_csv_cli(
        cdf_files_or_dir,
        outputfn=None,
        selection_query=None,  # Is actually a list of "selection/query requests"
        selection_method="glob",
        sort_columns=False,
        nan_correction='dropna', nan_fill_value=0, nan_interpolation_method='linear',
        runname_fmt="{i:02} {ds.sample_name}",
        crop_range=None,
        csv_sep=',',
        verbose=0,
):
    """ CLI to convert a list of CDF files to a single csv file.
    Basically just a wrapper around `rsenv.hplcutils.io.load_hplc_aia_xr_dataframe()`
    with a `df.to_csv()` afterwards.

    Args:
        cdf_files_or_dir:
        outputfn:
        verbose:
        nan_correction:
        nan_fill_value:
        nan_interpolation_method:
        runname_fmt:
        crop_range:
            Which name is better?
            'signal_crop_range', 'signal_range_crop', 'crop_signal_range'?
            'crop_range', 'crop_signal', 'signal_range' ?
        selection_query:
        selection_method:

    Returns:

    """

    # We can provide either cdf files directly, or directories containing cdf files (e.g. AIA data exports).
    if outputfn is None:
        # If a single file/directory is given, use that as filename basis, otherwise use a generic output filename.
        if len(cdf_files_or_dir) == 1:
            outputfn = cdf_files_or_dir[0] + '.csv'
        else:
            outputfn = "converted_cdf_files.csv"

    df = load_hplc_aia_xr_dataframe(
        cdf_files_or_dir,
        runname_fmt=runname_fmt,
        selection_query=selection_query, selection_method=selection_method, sort_columns=sort_columns,
        convert_to_actual_time=True, convert_seconds_to_minutes=True,
        nan_correction=nan_correction, nan_fill_value=nan_fill_value, nan_interpolation_method=nan_interpolation_method,
        signal_range_crop=crop_range,
        verbose=verbose,
    )
    if os.path.exists(outputfn):
        answer = input(f"Output filename {outputfn!r} already exists! Overwrite? [Y/n] ")
        if answer and answer.lower()[0] == 'n':
            print("Aborting...")
            return
    df.to_csv(outputfn)


if __name__ == '__main__':
    cdf_csv_cli()
