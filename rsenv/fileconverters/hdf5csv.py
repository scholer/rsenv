

"""
Module for converting between HDF5 and CSV formats.

Note: The HDF5 package comes with a bunch of HDF tools, e.g.
    h5stat - for displaying stats about a hdf file.
    h5dump - display hdf file information, structure and data.
        `h5dump -H file.hdf5`  # will display dataset headers.

For exploring HDF5 files, see e.g. [HDF Compass](https://github.com/HDFGroup/hdf-compass)

There has been a bunch of critizisms of HDF5, e.g. http://cyrille.rossant.net/moving-away-hdf5/
But also proponents, e.g. http://blog.khinsen.net/posts/2016/01/07/on-hdf5-and-the-future-of-data-management/

Critiques of HDF5 include:
* Fundamentally wrong philosophy: HDF is basically creating a filesystem-within-a-file.
    It may be alluring to have everything combined, but it eventually causes more problems than it is worth.
    1. Creating filesystems is HARD, and modern operating systems have spent many resources perfecting it.
    2. Putting multiple datasets in a single file increases risk of data corruption.
    3. Since all access goes through an extra layer (the HDF5 library),
        performance will always be slower than simple flat files on a disk.
    4. Instead of using a complex HDF file, just use a directory with files and sub-directories,
        which gives you exactly the same but with better performance, support.
* Opaque - all access to a HDF file goes through the HDF library.
    This means that we cannot use basic tools to query or probe the data, e.g. grep or text editors.

HDF5 vs CDF, netCDF, and HDF4:
* Albeit HDF4 and HDF5 are developed by the same organization, the data model of HDF5 is totally different from HDF4
    and their formats are incompatible.
* HDF is a Hierarchical Data Format developed at the National Center for Supercomputing Applications (NCSA) at the University of Illinois.
* CDF was designed and developed in 1985 by the National Space Science Data Center (NSSDC) at NASA/GSFC.
* NetCDF was developed a few years later at Unidata, part of the University Corporation for Atmospheric Research (UCAR).
* Tools for interconversion between formats are available at https://cdf.gsfc.nasa.gov/html/dttools.html
* Wikipedia: netCDF-4 (...) is the HDF5 data format, with some restrictions.
* Unidata.UCAR.edu: HDF5 Files produced by netCDF-4 are perfectly respectable HDF5 files, can be read by any HDF5 app.
* So, modern CDF and HDF are basically the same: Hierarchical organization of data within a single file.

HDF5 vs FITS, ASDF:
* Advanced Scientific Data Format (ASDF), pronounced AZ-diff, from the Space Telescope Science Institute.
* Flexible Image Transport System (FITS), standard astronomy image format, dndorsed by NASA.

Other numerical data storage formats:
* ROOT (https://root.cern.ch/) - more of a framework than just a file format?
* Zarr (https://github.com/zarr-developers/zarr)
* Feather, Arrow, and other columnar data formats.


When to use HDF5 (or CDF/similar):
* Having data and metadata in a single file is desired (e.g. for instrument data export or portability in general).
* You either:
    (a) only have a few datasets in the file, or
    (b) you have many small datasets that are so related that it wound't make sense to have them as individual files.
* In most other cases, having individual data and metadata files in directories on disk is probably better.


Regarding filename parts nomenclature:
* pwd = C:\users\OddThinking\Documents\My Source
* C:\users\OddThinking\Documents\My Source\Widget\foo.src  - path. Alternatively: filepath, "full path", filename
* foo.src - basename. Note: "filename" may or may not contain the path.
* foo     - file root, or file stem, or basestem (stem of the basename).
* .src    - file extension, usually stored without dot.
* Widget\foo.src - relative path.
* C:\users\OddThinking\Documents\My Source\Widget\ - directory, or directory name.
* C:\users\OddThinking\Documents\My Source - base directory, current working directory. `pwd` = print working directory.

Filename refs:
* https://stackoverflow.com/questions/2235173/file-name-path-name-base-name-naming-standard-for-pieces-of-a-path




"""

import os
import pandas as pd
import click
import inspect


def csv_to_hdf5(csvfiles, outputfnfmt="{inputfn}.hdf5", keyfmt="/locs", mode='a', append=True, quiet=False):
    """Convert CSV file(s) to HDF5 file(s).

    Args:
        csvfiles: Input CSV files to convert.
        outputfnfmt: Output filename format, using python {braced} `str.format()`.
        keyfmt: The dataset key or 'path' to write to. Leading '/' is optional.
        mode: File mode to open the hdf file in. 'a' (default) will append to existing file, 'w' will overwrite.
        append: ?
        quiet: Do not print information.

    Returns:
        outputfiles: list of all created HDF output files.

    """
    if isinstance(csvfiles, (str, bytes)):
        csvfiles = [csvfiles]
    outputfiles = []
    for csvfile in csvfiles:
        if not quiet:
            print("Reading CSV file:", csvfile)
        df = pd.read_csv(csvfile)
        dirname = os.path.dirname(csvfile)
        basename = os.path.basename(csvfile)
        basestem, ext = os.path.splitext(basename)  # basename? name? stem?
        outputfn = outputfnfmt.format(inputfn=csvfile, name=basestem, basestem=basestem, dirname=dirname)
        key = keyfmt.format(inputfn=csvfile, name=basestem, basestem=basestem, dirname=dirname)
        if not quiet:
            print(f"Writing CSV data to table '{key}' in file: {outputfn}")
        df.to_hdf(outputfn, key=key, mode=mode)
        outputfiles.append(outputfn)
    return outputfiles


# Click CLI:
csv_to_hdf5_cli = click.Command(
    callback=csv_to_hdf5,
    name=csv_to_hdf5.__name__,
    help=inspect.getdoc(csv_to_hdf5),
    params=[
        click.Option(['--outputfnfmt', '-f'], default="{inputfn}.hdf5"),
        click.Option(['--keyfmt'], default="/locs"),  # remember: param_decls is a list, *decls.
        click.Option(['--mode'], default="a"),
        click.Option(['--append/--no-append'], default=True),
        click.Option(['--quiet/--no-quiet']),
        # click.Option(['--verbose', '-v'], count=True),
        click.Argument(['csvfiles'])
])


def hdf5_to_csv(
        hdffiles, outputfnfmt="{inputfn}_{key}.csv", keys=None, convert_slash='_',
        sep=",", header=True, index=True, quotechar='"', line_terminator="\n",
        doublequote=True, escapechar=None, decimal=".", dateformat=None,
        chunksize=None, tupleize_cols=None,
        quiet=False
):
    """Convert hdf5 files to csv files. See also `h5dump` CLI tool.

    Args:
        hdffiles:
        outputfnfmt:
        keys: Which datasets to read. Default is is "all"
        convert_slash: Convert slash characters ('/') in HDF keys when used to generate csv filename.
        sep: CSV field separation character; forwarded to `pandas.DataFrame.to_csv()`.
        header: Write CSV header; forwarded to `pandas.DataFrame.to_csv()`.
        index: Include index in CSV file; forwarded to `pandas.DataFrame.to_csv()`.
        quotechar: CSV quote character; forwarded to `pandas.DataFrame.to_csv()`.
        line_terminator: CSV line termination character; forwarded to `pandas.DataFrame.to_csv()`.
        dateformat: CSV date format; forwarded to `pandas.DataFrame.to_csv()`.
        doublequote: ; forwarded to `pandas.DataFrame.to_csv()`.
        escapechar: CSV escape character; forwarded to `pandas.DataFrame.to_csv()`.
        decimal: CSV decimal character; forwarded to `pandas.DataFrame.to_csv()`.
        chunksize: Chunksize for writing CSV file; forwarded to `pandas.DataFrame.to_csv()`.
        tupleize_cols: ; forwarded to `pandas.DataFrame.to_csv()`.
        quiet:

    Returns:
        outputfiles: list of all created CSV output files.

    """
    # NOTE: Reading HDF5 files with Pandas requires PyTables to be installed.
    if isinstance(hdffiles, (str, bytes)):
        csvfiles = [hdffiles]
    outputfiles = []
    for hdffile in hdffiles:
        if not quiet:
            print("Reading HDF5 file:", hdffile)
        dirname = os.path.dirname(hdffile)
        basename = os.path.basename(hdffile)
        basestem, ext = os.path.splitext(basename)  # basename? name? stem?
        with pd.HDFStore(hdffile) as store:
            for key in (keys if keys is not None else store.keys()):
                df = store[key]
                key_str = key.lstrip('/').replace('/', convert_slash) if convert_slash else key
                outputfn = outputfnfmt.format(inputfn=hdffile, key=key_str, basestem=basestem, dirname=dirname)
                if not quiet:
                    print(f"Writing table {key} to CSV file: {outputfn}")
                df.to_csv(outputfn)
                outputfiles.append(outputfn)
    return outputfiles


# Click CLI:
hdf5_to_csv_cli = click.Command(
    callback=hdf5_to_csv,
    name=hdf5_to_csv.__name__,
    help=inspect.getdoc(hdf5_to_csv),
    params=[
        click.Option(['--outputfnfmt', '-f'], default="{inputfn}_{key}.csv"),
        click.Option(['--keys'], nargs=-1),
        click.Option(['--sep'], default=","),
        click.Option(['--quiet/--no-quiet']),
        # click.Option(['--verbose', '-v'], count=True),
        click.Argument(['hdffiles'])
])
