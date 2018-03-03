"""

Yet another duplicate files finder written in Python.

This modules takes all the good things from previous "duplicate files finders", and adds some additional goodies.

The basic algorithm is similar to FastDup, fastdupes, etc:

1. Group files by size, remove groups with only 1 element, and optionally files below a certain size.
2. Sub-group by hashing the first 1-16 kB of the file. Eliminate sub-groups with only 1 element.
3. Sub-sub-group by the full hash of file (or, optionally, by comparing file content chunk-by-chunk).

Like `fastdupes`, you can:
* Provide multiple root directories to search in.
* Ignore files below a minimum file size limit.
* Exclude given files based on file name pattern (glob).
* Provide preferences for which files should be kept.


The primary difference between this module and previous "duplicate files finders" is that this module
uses a `pandas.DataFrame` as the main storage (instead of python dicts).

This makes it easy to save duplicate files DataFrame to disk and the process the data manually,
using all the features available to pandas DataFrames.

The DataFrame can be saved at any point, e.g. after sub-grouping by 4 kB file header hash,
inspected, modified, and then used as starting point for another run.


Other goodies and motivations for writing yet another duplicate files finder:
* Written for Python 3 (unlike the otherwise excellent `fastdupes` package)
* The module checks all file elements to make sure we have real file paths (and not e.g. symlinks or junction paths).
* The module uses the modern `click` module to provide the command line interface (CLI),
    instead of the old `optparser` (which is used by the otherwise excellent `fastdupes` package).
* The grouping scheme can be customized. You can e.g. add a subgroup that uses a hash
    of the first 4 MB of the file, before calculating the full hash, so the grouping is:
    (1) size, (2) hash first 16 kb, (3) hash first 4 MB, (4) hash full file.
    Such complex grouping behaviour is specified using a YAML file (rather than by complex command line arguments).


New concept: Dynamic read length
* In many of the previous "duplicate file finders", we have different levels of grouping.
    However, for the last level, comparing full file content, it may be really expensive
    to calculate hashes of two or more very large files.
* Some packages provide an option to instead compare file content chunk-by-chunk, until a difference is found,
    or the files have been found to be completely identical.
* This package, provides a dynamic mode, where hashes are calculated continuously for increasing sizes
    until a difference is found. In practice, this is very efficient, because hashing functions
    already calculate hashes in chunks, rather than trying to keep the full file content in memory.
    So, after feeding e.g. 1 MB to a hash function, the function has already calculated a "partial hash".




Non-comprehensive list of prior art (i.e. other "file duplicates finders):
* https://github.com/hsoft/dupeguru - “Current status: Unmaintained. I haven't worked on dupeGuru for a while and
    frankly, I don't want to. I never had any duplicate problems so I don't even care about the
    raison d'être of this thing.” (Feb 15, 2018)
* https://github.com/thorsummoner/duplicate-files - Not liking the code, and only does (size → full-hash) grouping without the intermediate 4kB head grouping.
* https://github.com/ssokolow/fastdupes - This seems nice. Although perhaps a bit unnecessary use of decorators, and using `optparse` instead of `argparse` or `click`. Also: Python 2.7 only, no python3. But: Allows searching multiple roots, e.g. `fastdupes C:\Music D:\Backup\Music` .
* https://github.com/cwilper/qdupe - Latest commit ff19a4d on Dec 8, 2010.
* https://github.com/michaelkrisper/duplicate-file-finder
* https://github.com/mikecurry74/hoarder (backup tool with file de-duplication)
* https://github.com/eduardoklosowski/deduplicated - doesn’t seem nice either.
* https://github.com/israel-lugo/capidup
* https://pypi.python.org/pypi?%3Aaction=search&term=duplicate+files - lots of alternatives.


"""

import os
import io
import hashlib
from functools import partial
import inspect
import numpy as np
import pandas as pd
from fnmatch import fnmatch, fnmatchcase
import yaml
import click
import warnings


kB = 1024
MB = 2**20
GB = 2**30
CHUNK_SIZE = 64*kB

prefixes = {
    'B': 1,
    'k': kB, 'kB': kB, 'KB': kB, 'K': kB,
    'M': MB, 'MB': MB,
    'G': GB, 'GB': GB,
}


def fsize_str_to_int(fsize, warn=True):
    if not isinstance(fsize, str):
        if warn:
            warnings.warn("fsize %r is not a str: %s" % (fsize, type(fsize)))
        return fsize
    assert len(fsize) > 0
    if len(fsize) == 1:
        # print("fsize of length 1: %r" % (fsize,))
        return int(fsize)
    if fsize[-2:] in prefixes:
        # 'kB', 'MB', 'GB':
        # print("%r, %r, %r" % (fsize[:-2], fsize[-2:], prefixes[fsize[-2:]]))
        return int(float(fsize[:-2]) * prefixes[fsize[-2:]])
    elif fsize[-1:] in prefixes:
        # 'B', 'k', 'M', 'G':
        # print("%r, %r, %r" % (fsize[:-1], fsize[-1:], prefixes[fsize[-1:]]))
        return int(float(fsize[:-1]) * prefixes[fsize[-1:]])


def calculate_file_hash(filepath, hashname='md5', read_limit=0, chunk_size=CHUNK_SIZE, return_type='int'):
    # hashfactory = getattr(hashlib, hashname)
    hashfactory = hashlib.md5
    hashmethod = hashfactory()
    with open(filepath, "rb") as f:
        n_bytes_read = 0
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hashmethod.update(chunk)
            n_bytes_read += chunk_size
            if 0 < read_limit < n_bytes_read:
                break
    if return_type == 'hex':
        return hashmethod.hexdigest()
    elif return_type == 'int':
        # Note: Python ints limited to 64bits = 8 bytes, else error: "int too big to convert".
        return int.from_bytes(hashmethod.digest()[:8], byteorder='little')
    else:
        return hashmethod.digest()


default_grouping_scheme = [
    ('filesize', os.path.getsize),
    ('md5-16kB', partial(calculate_file_hash, hashname='md5', read_limit=64*kB)),
    ('md5-4MB', partial(calculate_file_hash, hashname='md5', read_limit=4*MB)),
    ('md5-full', partial(calculate_file_hash, hashname='md5', read_limit=0)),
]


def find_files(
        start_points, exclude_patterns=None, use_realpath=True,
        realpaths=False, remove_realpath_dups=False, follow_links=False, exclude_links=False,
        return_type='iter', series_name='path', verbose=0
):
    """"""

    fpaths = (
        fp
        for start_point in start_points
        for dirpath, dirnames, filenames in os.walk(start_point, followlinks=follow_links)
        for fp in [os.path.join(dirpath, fn) for fn in filenames]
    )
    if exclude_patterns:
        fpaths = (fp for fp in fpaths if not any(fnmatch(fp, pat) for pat in exclude_patterns))
    if exclude_links:
        fpaths = (fp for fp in fpaths if not os.path.islink(fp))
    if realpaths:
        fpaths = (os.path.realpath(fp) if not os.path.islink(fp) else os.readlink(fp) for fp in fpaths)
    if return_type == 'iter':
        # For iterators, we break off here, since we cannot do many of the things below with iterators.
        return fpaths

    if return_type == 'list':
        fpaths = list(fpaths)
        fpaths.sort()  # sort in-place
        if remove_realpath_dups:
            # Checking dups with list-based way:
            is_dup_mask = [fpaths[i] == fpaths[i - 1] for i in range(1, len(fpaths))]
            if any(is_dup_mask):
                ndups = sum(is_dup_mask)
                print("%s link-duplicates found (hard-links, soft-links, or NTFS junctions)." % ndups)
                fpaths = [fp for fp, is_dup in zip(fpaths, is_dup_mask) if not is_dup]
    elif return_type in ('nparray', 'series'):
        # Convert to numpy array:
        # fpaths = np.fromiter(fpaths, dtype=np.object)  # ValueError: cannot create object arrays from iterator
        fpaths = np.array(list(fpaths), dtype=np.object)
        fpaths.sort()  # arr.sort() is in-place, while np.sort(arr) returns new
        # link-dups checking, numpy version:
        if remove_realpath_dups:
            is_dup_mask = np.ndarray(fpaths.shape)
            is_dup_mask[0] = False
            is_dup_mask[1:] = fpaths[1:] == fpaths[:-1]
            if np.any(is_dup_mask):
                if verbose:
                    ndups = is_dup_mask.sum()
                    print("%s link-duplicates found (hard-links, soft-links, or NTFS junctions)." % ndups)
                fpaths = fpaths[np.bitwise_not(is_dup_mask)]
        if return_type == 'series':
            fpaths = pd.Series(fpaths, name=series_name)
    else:
        raise ValueError("Specified `return_type` %r not recognized.")
    if verbose > 1:
        print("%s files found." % len(fpaths))
    return fpaths


def get_startpoint_df(
        start_points,
        use_realpath=True, remove_realpath_dups=False, follow_links=False, exclude_links=True,
        exclude_patterns=None,
        fsize_min=None,
        verbose=0,
):
    """"""

    if len(start_points) == 1 and os.path.isfile(start_points[0]):
        # Pandas IO performance considerations: https://pandas.pydata.org/pandas-docs/stable/io.html#io-perf
        inputfn = start_points[0]
        return pd.read_hdf(inputfn)

    fpaths = find_files(
        start_points=start_points, exclude_patterns=exclude_patterns,
        follow_links=follow_links, exclude_links=exclude_links,
        use_realpath=use_realpath, remove_realpath_dups=remove_realpath_dups,
        return_type='series',
    )
    assert isinstance(fpaths, pd.Series)
    # Let's just always add filesize and filesize_MB for good measure:
    # Series/Dataframe: map is for simple dict-like lookup table mapping,
    # DataFrame: applymap is map(func, series), apply is for row/column based operations.
    # Series: apply is map(func, series), there is no applymap for pd.Series.
    filesize = fpaths.apply(os.path.getsize)
    if fsize_min:
        print("Converting fsize_min %r -> " % (fsize_min, ), end='')
        fsize_min = fsize_str_to_int(fsize_min)
        print("%r" % (fsize_min,))
        is_big_enough = filesize >= fsize_min
        fpaths, filesize = fpaths[is_big_enough], filesize[is_big_enough]
    # Consider using the path as index?
    group_idx = np.zeros(len(fpaths), dtype='uint32')
    # The most reliable way to control column order is either with an OrderedDict or DataFrame.from_items
    df = pd.DataFrame.from_items(zip(
        ['path', 'group_idx', 'filesize'],  #, 'filesize_MB'],
        [fpaths, group_idx, filesize]))  # , filesize // 1]))
    return df


def group_and_eliminate(df, grouping_scheme):
    grouping_levels = []
    org_df = df  # Keep a copy of the original DataFrame - we may be able to do everything as a view.
    if 'group_idx' not in df:
        df['group_idx'] = np.zeros(len(df), dtype='uint32')
    for header, func in grouping_scheme:
        print("\n> Grouping by %r ..." % header)
        if header not in df:
            vals = [func(fp) for fp in df['path']]
            print("> Adding new column %r ..." % header)
            df[header] = vals  # SettingWithCopyWarning  - because we've generated a view in the selection below!
            # df.loc[:, header] = vals
            print("< column %r added, dtype: %s" % (header, df[header].dtype))
        grouping_levels.append(header)
        print("Sorting %s rows in df by %s" % (len(df), grouping_levels))
        # df.sort_values(by=grouping_levels, inplace=True)  # inplace=True required if you want to sort in-place.
        df = df.sort_values(by=grouping_levels, inplace=False)  # inplace=False (default) returns a copy.
        print("Grouping df by %s and eliminating 1-element groups..." % (grouping_levels,))
        grouped = df.groupby(by=grouping_levels, sort=False)  # returns GroupBy object
        # for combination, rowidxs in df.groupby(groupby).indices.items(), or
        # for combination, group_df in df.groupby(groupby): group_df.index
        # Use index to iterate over groups, because then you can modify the original dataframe without errors.
        # Can also use it as a hierarchical index.
        group_ndups_hdr = header + '_ndups'
        group_fsize_hdr = header + '_grp_MB'
        df[group_ndups_hdr] = pd.Series(np.zeros(len(df), dtype=bool))
        # Add group sizes:
        # for combination, rowidxs in grouped.indices.items():
        # print("%s different values for ")
        for group_idx, (combination, group_df) in enumerate(grouped, 1):
            print("Processing group %s = %s (%s elements)" % (grouping_levels, combination, len(group_df)))
            # df[col, row], df.loc[row, col], or df.iloc[rnum, cnum]
            df.loc[group_df.index, group_ndups_hdr] = len(group_df)
            df.loc[group_df.index, 'group_idx'] = group_idx
            if 'filesize' in df:
                df.loc[group_df.index, group_fsize_hdr] = group_df['filesize'].sum() // 1
        print("\nDataFrame before eliminating 1-element groups:")
        print(df)
        # New dataframe with 1-element groups removed:
        df = df.loc[df[group_ndups_hdr] > 1, :]  # Note: This may create a view!
        df = df.copy()  # Avoid SettingWithCopyWarning
        print("\nDataFrame after eliminating 1-element groups:")
        print(df)
    return df


def find_duplicate_files(
        start_points,
        fsize_min=0, exclude=None,
        follow_links=False, exclude_links=True,
        realpaths=True, remove_realpath_dups=False,
        grouping_scheme=None,
        save_fnpat=None, save_cols=None, print_cols=None,
        verbose=0, quiet=False,
):
    """"""
    pd.set_option('display.width', 1000)
    if quiet:
        verbose = 0
    if isinstance(save_cols, str):
        save_cols = save_cols.split(",")
    if isinstance(print_cols, str):
        print_cols = print_cols.split(",")
    if grouping_scheme is None:
        grouping_scheme = default_grouping_scheme
    elif isinstance(grouping_scheme, str):
        grouping_scheme = yaml.load(open(grouping_scheme))
    print("\n\n> starting get_startpoint_df...")
    df = get_startpoint_df(
        start_points=start_points, exclude_patterns=exclude, fsize_min=fsize_min,
        follow_links=follow_links, exclude_links=exclude_links,
        use_realpath=realpaths, remove_realpath_dups=remove_realpath_dups,
        verbose=verbose
    )
    print("< done get_startpoint_df\n")
    print("\nStarting df:")
    print(df)
    print("\n\n> starting group_and_eliminate")
    df = group_and_eliminate(df=df, grouping_scheme=grouping_scheme)
    print("< done group_and_eliminate\n")
    print("")
    if save_fnpat:
        if isinstance(save_fnpat, str):
            save_fnpat = (save_fnpat,)
        df_export = df[save_cols] if save_cols else df
        for fn in save_fnpat:
            method = getattr(df_export, 'to_' + os.path.splitext(fn)[1].strip('.'))
            method(fn)
    if print_cols:
        print(df if print_cols == 'all' else df[print_cols])


find_duplicate_files_cli = click.Command(
    callback=find_duplicate_files,
    name=find_duplicate_files.__name__,
    help=inspect.getdoc(find_duplicate_files),
    params=[
        click.Option(['--grouping-scheme', '-g']),  # remember: param_decls is a list, *decls.
        click.Option(['--fsize-min']),
        click.Option(['--exclude'], multiple=True),
        click.Option(['--follow-links/--no-follow-links'], default=False),
        click.Option(['--exclude-links/--no-exclude-links'], default=False),
        click.Option(['--realpaths/--no-realpaths'], default=False),
        click.Option(['--remove-realpath-dups/--no-remove-realpath-dups'], default=False),
        click.Option(['--save-fnpat']),
        click.Option(['--save-cols']),
        click.Option(['--print-cols']),
        click.Option(['--verbose', '-v'], count=True),
        click.Option(['--quiet/--no-quiet']),
        click.Argument(
            ['start-points'], required=True, nargs=-1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])






