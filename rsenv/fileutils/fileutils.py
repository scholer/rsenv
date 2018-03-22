
"""

Utility/aggregation module with various small functions for dealing with files and filesystems.

Functions are often simply "reference functions", used to exemplify how to do a particular task.


"""

import os
import glob
from fnmatch import fnmatch
import yaml
from datetime import datetime
import warnings


named_file_patterns = {
    'datetime': '{prefix}_{date:%Y%m%d-%H%M}.{ext}',
    'datetime-precise': '{prefix}_{date:%Y%m%d-%H%M%S}.{ext}',
    'date-seq': '{prefix}_{date:%Y%m%d}_{i:03}.{ext}',
    'image-datetime': 'image_{date:%Y%m%d-%H%M%S}.png',
    'image-date-seq': 'image_{date:%Y%m%d}_{i:03}.png',
}

kB = 1024
MB = 2**20
GB = 2**30
prefixes = {
    'B': 1,
    'k': kB, 'kB': kB, 'KB': kB, 'K': kB,
    'M': MB, 'MB': MB,
    'G': GB, 'GB': GB,
}


def fsize_str_to_int(fsize, warn=True):
    """ Convert a filesize string, e.g. "10 MB" to actual number of bytes (int).

    Args:
        fsize: The filesize string to convert.
        warn: Whether to warn if e.g. fsize is not a string (it could be an int, in which case just return the int).

    Returns:
        Integer, actual number of bytes.

    Note:
        Filesize byte unit must be given with capital 'B'.
        The 'B' can also be omitted, e.g. '10M' is interpreted as '10MB'.
        Spaces shouldn't matter; only the last 1-2 characters are probed, the rest is passed to `int()`.

    Examples:
        >>> fsize_str_to_int("2 kB")
        >>> fsize_str_to_int("10MB")
        >>> fsize_str_to_int("100 GB")
        >>> fsize_str_to_int("8M")

    """
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


def find_files(
        start_points,
        exclude_patterns=None, include_patterns=None,
        followlinks=False, exclude_links=True,
        realpaths=False, abspaths=False,
        fsize_min=None, fsize_max=None
):
    """ Find files matching a particular filepath pattern (using walk and fnmatch).

    Args:
        start_points: One or more base directories to start from.
        exclude_patterns: Exclude files matching any of these patterns.
        include_patterns: Only include files matching any of these patterns. (Inverted exclude)
        followlinks: Whether to follow directory links; passed to `os.walk`.
        exclude_links: Whether to exclude file symbolic links.
        realpaths: Convert paths with `os.path.realpath` before returning them, i.e. return
            "canonical path of the specified filename, eliminating any symbolic links encountered in the path"
        abspaths: Convert paths with `os.path.realpath` before returning them, i.e. return
            "normalized absolutized version of the path" (does not expand symbolic links).
        fsize_min: Only include files above or equal to this file size.
        fsize_max: Only include files below or equal to this file size.

    Returns:
        A generator of file paths matching the given criteria.

    Alternatives:
        In `glob.glob` with `recursive=True` you can use '**' to expand to match all directories and sub-directories:
        >>> glob.glob('**/*.mp4', recursive=True)  # Search recursively for mp4 files.
        >>> glob.glob('**/.git/')  # Search recursively for .git repositories (trailing `os.sep` matches directories)

    """
    if isinstance(start_points, str):  # str, or filepath instance
        start_points = [start_points]
    if isinstance(exclude_patterns, str):
        exclude_patterns = [exclude_patterns]
    if isinstance(include_patterns, str):
        include_patterns = [include_patterns]
    fpaths = (
        fp
        for start_point in start_points
        for dirpath, dirnames, filenames in os.walk(start_point, followlinks=followlinks)
        for fp in [os.path.join(dirpath, fn) for fn in filenames]
    )
    if exclude_patterns:
        fpaths = (fp for fp in fpaths if not any(fnmatch(fp, pat) for pat in exclude_patterns))
    if include_patterns:
        fpaths = (fp for fp in fpaths if any(fnmatch(fp, pat) for pat in exclude_patterns))
    if exclude_links:
        fpaths = (fp for fp in fpaths if not os.path.islink(fp))
    if realpaths:
        fpaths = (os.path.realpath(fp) if not os.path.islink(fp) else os.readlink(fp) for fp in fpaths)
    if abspaths:
        fpaths = (os.path.abspath(fp) for fp in fpaths)
    if fsize_min:
        fpaths = (fp for fp in fpaths if os.path.getsize(fp) >= fsize_min)
    if fsize_max:
        fpaths = (fp for fp in fpaths if os.path.getsize(fp) <= fsize_min)
    return fpaths


def get_next_unused_filename(
        pattern="{prefix}_{i:03}.{ext}", i_range=range(1000),
        prefix="image", ext=".png",
        raise_if_none_found=True
):
    """ Generate unique/unused filenames based on a certain pattern. """
    if pattern in named_file_patterns:
        pattern = named_file_patterns[pattern]
    now = datetime.now()
    for i in i_range:
        fn = pattern.format(i=i, prefix=prefix, ext=ext, date=now, datetime=now, now=now)
        if not os.path.exists(fn):
            return fn
    else:
        if raise_if_none_found:
            raise RuntimeError(f"Could not find a suitable filename, tried pattern "
                               f"{pattern} for all combinations of i in range {i_range}.")
        else:
            return None


def expand_files(files, nonmatching_passthrough=False):
    """ Expand glob filename patterns.

    Rationale: Windows does not allow wildcard expansion at the command line prompt.
    If you want to emulate linux-like wildcard expansion in your programs,
    you can pass your filename arguments through this function.

    Args:
        files: List of filenames to expand.
        nonmatching_passthrough: Filename patterns that do not match any elements are

    Returns:
        A list of actual filenames matching the filename patterns.

    Note regarding `nonmatching_passthrough`:
        In Bash, patterns are passed as-is, if they do not match any file/directories.
        To emulate this behavior, `nonmatching_passthrough` must be set to True.
        Otherwise, patterns that does not match any filenames will be glob-expanded to an empty list.
        Thus, by default, this function does not exactly emulate bash wildcard expansion.
    """
    if nonmatching_passthrough:
        globbed = [(pattern, glob.glob(pattern)) for pattern in files]
        expanded = [fname for pat, flist in globbed for fname in (flist if flist else [pat])]
    else:
        expanded = [fname for pattern in files for fname in glob.glob(pattern)]
    return expanded


def load_yaml(filepath):
    """ Load yaml from filepath (reference function). """
    with open(filepath) as fp:
        r = yaml.load(fp)
    return r
