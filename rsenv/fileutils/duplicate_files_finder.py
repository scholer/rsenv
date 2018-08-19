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
import inspect
import numpy as np
import pandas as pd
from fnmatch import fnmatch
import yaml
import click
import warnings
from collections import OrderedDict

from rsenv.fileutils.filehashing import calculate_file_hash
from rsenv.fileutils.fileutils import find_files, fsize_str_to_int, kB, MB
import datetime

# While having a generic list of (header, function) tuples was nice and simple,
# it prevented us from doing slightly more complex things like:
# "don't calculate 4MB md5 hash if file is only 10kb and you have already calculated 64kb md5 hash."
# (Although arguably that could have been done with the `read_start` parameter.
default_grouping_scheme = [
    {'name': 'filesize', 'func': os.path.getsize, 'args': [], 'kwargs': {}, 'filesizelimit': 0},
    # We do *not* by default use file modification time, as it may be unreliable.
    # Two files can easily be identical but still have different modification time, e.g. from windows copy operations.
    {'name': 'md5-16kB', 'func': calculate_file_hash, 'args': [], 'kwargs': dict(hashname='md5', read_limit=64 * kB), 'filesizelimit': 64 * kB},
    {'name': 'md5-04MB', 'func': calculate_file_hash, 'args': [], 'kwargs': dict(hashname='md5', read_limit=4 * MB), 'filesizelimit': 4 * MB},
    {'name': 'md5-full', 'func': calculate_file_hash, 'args': [], 'kwargs': dict(hashname='md5', read_limit=0), 'filesizelimit': 0},
    # ('filesize', os.path.getsize),
    # ('md5-16kB', partial(calculate_file_hash, hashname='md5', read_limit=64*kB)),
    # ('md5-4MB', partial(calculate_file_hash, hashname='md5', read_limit=4*MB)),
    # ('md5-full', partial(calculate_file_hash, hashname='md5', read_limit=0)),
]


def get_file_paths(
        start_points, exclude_patterns=None,
        abspaths=True, realpaths=True,
        remove_realpath_dups=False, follow_links=False, exclude_links=False,
        return_type='iter', series_name='path', verbose=0
):
    """ Get a list/array/series of file paths.

    This function is mainly driven by the generator returned by `find_files()`.
    The generator from `find_files()` is converted to list/array/series,
    and some optional processing is applied (e.g. removing path duplicates
    arising from symbolic links pointing to the same file node).

    TODO: You may want to use `os.stat()` to get device and inode to make sure apparently identical
    TODO: files are not just hardlinked to the same inode.

    Args:
        start_points:
        exclude_patterns:
        abspaths: Use the absolute file path instead of relative.
        realpaths: De-reference links.
        remove_realpath_dups:
        follow_links:
        exclude_links:
        return_type:
        series_name:
        verbose:

    Returns:

    """

    fpaths = find_files(
        start_points=start_points, exclude_patterns=exclude_patterns,
        abspaths=abspaths, realpaths=realpaths, followlinks=follow_links, exclude_links=exclude_links
    )

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
        fpaths.sort()  # arr.sort() is in-place, while np.sort(arr) returns new array
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


def get_basic_fileinfo_df(
        start_points,
        abspaths=True, realpaths=True, remove_realpath_dups=False, follow_links=False, exclude_links=True,
        exclude_patterns=None,
        fsize_min=None,
        add_filesize=False,
        add_stat=True,
        add_mtime=True,
        add_mtime_str=True, modtime_strfmt="%Y-%m-%d %H:%M:%S.%f+%z",
        filelist_source=None,
        verbose=0,
):
    """ Create the basic DataFrame with file paths from which to start finding duplicates from.

    Args:
        start_points: One or more paths to start looking for files from.
        abspaths: Use absolute file paths instead of relative.
        realpaths: De-reference symbolic links.
        remove_realpath_dups: If a symbolic link has been de-referenced and now points to a file that is also included,
            remove the obvious duplicate.
        follow_links:
        exclude_links:
        exclude_patterns:
        fsize_min:
        add_stat: Add file stats (mtime, and st_dev and st_ino inode info) columns to the dataframe.
        filelist_source:
        verbose:

    Returns:

    """

    if len(start_points) == 1 and os.path.isfile(start_points[0]):
        # Pandas IO performance considerations: https://pandas.pydata.org/pandas-docs/stable/io.html#io-perf
        inputfn = start_points[0]
        return pd.read_hdf(inputfn)

    if filelist_source:
        with open(filelist_source) as fd:
            fpaths = [line for line in fd]
    else:
        fpaths = get_file_paths(
            start_points=start_points, exclude_patterns=exclude_patterns,
            follow_links=follow_links, exclude_links=exclude_links,
            abspaths=abspaths, realpaths=realpaths, remove_realpath_dups=remove_realpath_dups,
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
    if add_stat:
        df['dev'], df['ino'], df['ctime'], df['mtime'], df['mtime_ns'], df['filesize'], df['gid'], df['uid'] = [
            (st.st_dev, st.st_ino, st.st_ctime, st.st_mtime, st.st_mtime_ns, st.st_size, st.st_gid, st.st_uid)
            for st in [os.stat(fp) for fp in fpaths]
        ]
    else:
        if add_mtime:
            # os.path.getmtime() uses os.stat().
            df['mtime'] = [os.path.getmtime(fp) for fp in fpaths]
        if add_filesize:
            df['filesize'] = df['path'].map(os.path.getsize)

    if add_stat or add_mtime:

        def timestamp_to_str(ts):
            return datetime.datetime.fromtimestamp(ts).strftime(modtime_strfmt)
        # df['mtime_str'] = [timestamp_to_str(ts) for ts in df['mtime']]
        df['mtime_str'] = df['mtime'].map(timestamp_to_str)


    # It would be nice to have some metadata, e.g. on what types of checksums and groupings have been performed
    # df.hash_groups = OrderedDict()
    # Unfortunately, just using attributes is not a good idea, since operations may return a new dataframe
    # without those attributes. There is an "unofficial" `DataFrame._metadata` attribute that "should"
    # survive, but since it is not part of the public API, that may not be a stable solution.
    # Alternatively, use xarray or one of the other DataFrame packages that DO support metadata annotations.
    df._metadata['hashes'] = OrderedDict()
    return df


def group_and_eliminate_df(
        df, grouping_scheme, entry_column='path',
        eliminate_nonduplicates=True, add_ndups_count=True, add_group_mb_sum=True
):
    """ Group entries and eliminate unique entries after each grouping round.

    This function is used to find duplicates by iteratively grouping entries and
    removing entries in groups with only a single entry.

    Entries in the dataframe are grouped according to the list of grouping specifications/methods.
    A group spec is a dict with keys 'header', 'func', and optionally 'args', 'kwargs', 'filesizelimit',
    The grouping key value is calculated as `val = func(df[entry_column], *args, **kwargs)`

    Two entries must be guaranteed to be different if the value returned by any grouping method differ.

    The typical use case is to find duplicate files by

    Args:
        df: A DataFrame with path entries to group and eliminate unique.
        grouping_scheme:
        eliminate_nonduplicates:
        add_ndups_count:
        add_group_mb_sum:

    Returns:

    """
    grouping_levels = []
    org_df = df  # Keep a copy of the original DataFrame - we may be able to do everything as a view.
    if 'group_idx' not in df:
        df['group_idx'] = np.zeros(len(df), dtype='uint32')
    for group_spec in grouping_scheme:
        header = group_spec['name']
        func, args, kwargs = group_spec['func'], group_spec.get('args', []), group_spec.get('kwargs', {})
        grouping_type, filesizelimit = group_spec.get('type', 'hash'), group_spec.get('filesizelimit', 0)
        print("\n> Grouping by %r ..." % header)
        if header not in df:
            vals = [func(fp, *args, **kwargs) for fp in df[entry_column]]
            print("> Adding new column %r ..." % header)
            df[header] = vals  # SettingWithCopyWarning, because `df.loc[df[group_ndups_hdr] > 1, :]` generates a view
            # df.loc[:, header] = vals
            if grouping_type == 'hash':
                df._metadata['hashes'][header] = group_spec
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
            if add_ndups_count:
                df.loc[group_df.index, group_ndups_hdr] = len(group_df)
            df.loc[group_df.index, 'group_idx'] = group_idx
            if add_group_mb_sum and 'filesize' in df:
                df.loc[group_df.index, group_fsize_hdr] = group_df['filesize'].sum() // 1
        print("\nDataFrame before eliminating 1-element groups:")
        print(df)
        if eliminate_nonduplicates:
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
        abspaths=True, realpaths=True, remove_realpath_dups=False,
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
    print("\n\n> starting get_basic_fileinfo_df...")
    df = get_basic_fileinfo_df(
        start_points=start_points, exclude_patterns=exclude, fsize_min=fsize_min,
        follow_links=follow_links, exclude_links=exclude_links,
        abspaths=abspaths, realpaths=realpaths, remove_realpath_dups=remove_realpath_dups,
        verbose=verbose
    )
    print("< done get_basic_fileinfo_df\n")
    print("\nStarting df:")
    print(df)
    print("\n\n> starting group_and_eliminate_df")
    df = group_and_eliminate_df(df=df, grouping_scheme=grouping_scheme)
    print("< done group_and_eliminate_df\n")
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
        click.Option(['--abspaths/--no-abspaths'], default=False),
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






