import os
from collections import OrderedDict
import numpy as np
import pandas as pd
# import scipy
# import netCDF4
import xarray
xr = xarray
import glob

from rsenv.utils.query_parsing import get_cand_idxs_matching_expr, translate_all_requests_to_idxs


"""
# Note: If all data have the same point_number and same actual_sampling_interval,
# then we can just collect all data in a single dataframe with the same index.
# We can even convert the row index to an actual time.

NOTE: If you want to merge HPLC data with different sampling intervals, 
you should convert `point_number` axis to proper time:  
    `time = ds['actual_sampling_interval'] * ds['point_number']`
and then use the time as index.

"""


def load_hplc_aia_xr_dict(
        aia_dir, verbose=2, convert_to_actual_time=False, convert_seconds_to_minutes=True,
        runname_fmt="{i:02} {ds.sample_name}",
):
    """ Returns an ordered dict with {runname: (xs, ys) for each cdf file in aia_dir}.

    Args:
        aia_dir: The AIA directory to load.
        verbose: Verbosity to print information.
        convert_to_actual_time: Instead of xs being a simple range, convert to actual seconds.
        convert_seconds_to_minutes: If True and convert_to_actual_time is specified, convert seconds to minutes.
        runname_fmt: Python format string used to generate runname. Can includes variables, e.g. `i` and `ds`,
            where `ds` is the xarray dataset containing attributes such as `ds.sample_name`
            (as specified by ChemStation).

    Returns:
         OrderedDict with {runname: (xs, ys) for each cdf file in aia_dir}

    Note: This version uses `xarray`, hence the 'xr' specifier in the function name.
    There are several alternatives to xarray for reading CDF files, but xarray seems to work well.
    Behind the scene, xarray is just using one of the usual CDF or netCDF libraries.
    """
    data = OrderedDict()
    xs = None
    interval = None
    for i, fn in enumerate(fn for fn in os.listdir(aia_dir) if fn.lower().endswith(".cdf")):
        fpath = os.path.join(aia_dir, fn)
        print(f"\n{fn}:")
        with xr.open_dataset(fpath) as ds:
            ds.load()  # So we can access data after closing the file.
            if xs is not None and bool((xs == ds['point_number']).all()) is False:
                print(f"WARNING: The dataset ({fpath}) does not have the same time point numbers as the first dataset!")
            if interval and interval != ds['actual_sampling_interval']:
                print(f"WARNING: The dataset ({fpath}) does not use the same sampling interval as the first dataset!")
            xs = ds['point_number']  # or just ds.point_number
            ys = ds['ordinate_values']  # or just ds.ordinate_values
            interval = ds['actual_sampling_interval']
            if convert_to_actual_time:
                xs = xs * float(interval)
                if convert_seconds_to_minutes:
                    xs /= 60
            if verbose:
                print("- Sample name, ID  :", ds.sample_name, ", ", ds.sample_id)
                if verbose > 1:
                    print("- Sampling interval: {:0.03f} s".format(float(ds['actual_sampling_interval'])))
                    print("- Run length       : {:0.02f} min".format(float(ds['actual_run_time_length'])/60))
                    print("- Number of points :", len(ds.point_number))
            # Attributes: ds.attrs, e.g. ds.attrs['sample_name'] - also available directly as ds.sample_name
            data[runname_fmt.format(i=i, fn=fn, ds=ds, samplename=ds.sample_name)] = (xs, ys)
    return data


load_hplc_aia_data = load_hplc_aia_xr_dict


def load_hplc_aia_xr_datasets(aia_dir, concat=True, use_dask=False):
    """ Return a list of xarray datasets, one dataset for each file in the aia dir. """
    datasets = []
    if use_dask:
        datasets = xr.open_mfdataset([os.path.join(aia_dir, fn) for fn in os.listdir(aia_dir)])
        return datasets
    for fn in os.listdir(aia_dir):
        fpath = os.path.join(aia_dir, fn)
        print(f"\n{fn}:")
        with xr.open_dataset(fpath) as ds:
            ds.load()  # Load data into memory, so we can access data after closing the file.
            datasets.append(ds)
    datasets = xr.concat(datasets, dim='sample-runs')
    return datasets


def load_hplc_aia_xr_dataframe(
        cdf_files_or_aia_dir, convert_to_actual_time=False, convert_seconds_to_minutes=True, verbose=0,
        nan_correction='dropna', nan_fill_value=0, nan_interpolation_method='linear',
        runname_fmt="{i:02} {ds.sample_name}",
        signal_range_crop=None,
        selection_query=None,
        selection_method="glob"
):
    """ Load ChemStation HPLC .AIA (.CDF) exported data files into a Pandas DataFrame.

    Args:
        cdf_files_or_aia_dir: Either (a) AIA directory containing the exported HPLC .cdf files,
            or (b) a list of individual CDF files to load.
        convert_to_actual_time: Convert x-axis index to actual time (seconds). Otherwise is just range 0..N.
        convert_seconds_to_minutes: Convert time axis from seconds to minutes.
        verbose: Higher = more verbose information printing during data loading.
        nan_correction: How and whether to correct NaN values.
            Must be one of: None, 'dropna', 'interpolate', 'fill'.
            NaN values typically occur when the input cdf files did not have the same time information,
            i.e. the data was recorded with different sampling frequency.
        nan_fill_value: The NaN fill value to use, if `nan_correction='fill'`.
        nan_interpolation_method: The NaN interpolation method, if `nan_correction='interpolate'`.
        runname_fmt: How to format each column name.
            Available variables include: `i` and `ds`, where `ds` is the xarray dataset,
            with all attributes provided by the ChemStation export.
        signal_range_crop: Crop the time axis to this range. Must be either None, slice, tuple (start, end, [step]).
        selection_query: Filter datasets by runname/column name according to this selection expression.
            In brief, filter_selection must be a list of selection queries,
            where a sample is included if it matches any one of the selection queries (OR set join).
            each selection query can be e.g. a search string "RS123", an index (e.g. 3), or a range (e.g. '2-5').
        selection_method: How to match column names against the selection queries. E.g. 'glob', 'contains', or 'eq'.
            See also: `rsenv.utils.query_parsing.get_cand_idxs_matching_expr()`.

    Returns:
        df: Pandas DataFrame with one column for each cdf file in the AIA directory.

    Regarding selection query / method, see also:
    * `rsenv.utils.query_parsing.translate_all_requests_to_idxs()`  (combines the queries)
    * `rsenv.utils.query_parsing.get_cand_idxs_matching_expr()`  (used for individual queries)
    * `nanodrop_cli`  (uses translate_all_requests_to_idxs to select data sample names)

    Notes and refs:
    * http://xarray.pydata.org/en/stable/pandas.html

    """
    # TODO: Implement signal cropping.
    # TODO: Filter signals by query (using the `query_parsing` module).
    series = OrderedDict()
    cdf_files = []
    for path in cdf_files_or_aia_dir:
        # If a path argument is a directory, e.g. a .AIA export, load all contained cdf files:
        if os.path.isdir(path):
            print(glob.glob(os.path.join(path, '*.cdf')))
            cdf_files += glob.glob(os.path.join(path, '*.cdf'))
        else:
            cdf_files.append(path)

    # Load all CDF files and create Pandas Series for each dataset.
    # (Each ChemStation exported CDF file contain only a single chromatogram.)
    for i, fpath in enumerate(cdf_files):
        # fpath = os.path.join(cdf_files_or_aia_dir, fn)
        fn = os.path.basename(fpath)
        if verbose:
            print(f"\n{fpath}:")
        with xr.open_dataset(fpath) as ds:
            ds.load()  # So we can access data after closing the file.
            if verbose:
                print("- Sample name, ID  :", ds.sample_name, ", ", ds.sample_id)
                if verbose > 1:
                    print("- Sampling interval: {:0.03f} s".format(float(ds['actual_sampling_interval'])))
                    print("- Run length       : {:0.02f} min".format(float(ds['actual_run_time_length'])/60))
                    print("- Number of points :", len(ds.point_number))
            ts = ds['ordinate_values'].to_series()
            if convert_to_actual_time:
                ts.index *= float(ds.actual_sampling_interval)
                ts.index.name = "Time / seconds"
                if convert_seconds_to_minutes:
                    ts.index /= 60
                    ts.index.name = "Time / minutes"
            series[runname_fmt.format(i=i, fn=fn, ds=ds, samplename=ds.sample_name)] = ts
    # Create DataFrame:
    df = pd.DataFrame(data=series)

    # Crop signal range (time axis), and select columns if we have a query selection request.
    if signal_range_crop:
        if not isinstance(signal_range_crop, int):
            signal_range_crop = slice(*signal_range_crop)  # (start, stop)
        df = df.loc[signal_range_crop, :]
    if selection_query:
        # If you need more complexity than this, just filter the DataFrame after it is returned...
        if isinstance(selection_query, (str, int)):
            col_idxs = get_cand_idxs_matching_expr(
                expr=selection_query, candidates=df.columns, match_method=selection_method)
        else:
            # Use multi-selection request, e.g.
            # ['all', '-RS531*', 'RS531b*'] to select all except starting with RS531, although include RS531b.
            col_idxs = translate_all_requests_to_idxs(
                requests=selection_query, candidates=df.columns, match_method=selection_method)
        df = df.iloc[:, col_idxs]  # Using positional indices, not labels, so using iloc[].

    # Remove/fill/interpolate NaN values:
    if nan_correction and np.any(np.isnan(df.values)):
        print(f"\nDataFrame contains NaN values, correcting these using '{nan_correction}'...")
        print(np.where(np.isnan(df.values.T)))
        if nan_correction == 'dropna':
            df = df.dropna()
        elif nan_correction == 'interpolate':
            # https://pandas.pydata.org/pandas-docs/stable/missing_data.html
            # https://stackoverflow.com/questions/34693079/python-pandas-dataframe-interpolate-missing-data
            df = df.interpolate(method=nan_interpolation_method, axis=0).bfill()
        elif nan_correction == 'fill':
            df = df.fillna(nan_fill_value)

    return df
