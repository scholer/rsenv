import os
from collections import OrderedDict
import numpy as np
import pandas as pd
# import scipy
# import netCDF4
import xarray
xr = xarray

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
    data = OrderedDict()
    xs = None
    interval = None
    for fn in (fn for fn in os.listdir(aia_dir) if fn.lower().endswith(".cdf")):
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
    datasets = []
    if use_dask:
        datasets = xr.open_mfdataset([os.path.join(aia_dir, fn) for fn in os.listdir(aia_dir)])
        return datasets
    for fn in os.listdir(aia_dir):
        fpath = os.path.join(aia_dir, fn)
        print(f"\n{fn}:")
        with xr.open_dataset(fpath) as ds:
            ds.load()  # So we can access data after closing the file.

            datasets.append(ds)
    datasets = xr.concat(datasets, dim='sample-runs')
    return datasets


def load_hplc_aia_xr_dataframe(
        aia_dir, convert_to_actual_time=False, convert_seconds_to_minutes=True, verbose=0,
        nan_correction='dropna', nan_fill_value=0, nan_interpolation_method='linear',
        runname_fmt="{i:02} {ds.sample_name}",
):
    """

    Notes:
        http://xarray.pydata.org/en/stable/pandas.html

    Args:
        aia_dir:
        convert_to_actual_time:

    Returns:

    """
    series = OrderedDict()
    for i, fn in enumerate(os.listdir(aia_dir)):
        fpath = os.path.join(aia_dir, fn)
        if verbose:
            print(f"\n{fn}:")
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
    df = pd.DataFrame(data=series)
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
