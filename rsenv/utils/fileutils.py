
"""

Utility/aggregation module with various small functions for dealing with files and filesystems.

Functions are often simply "reference functions", used to exemplify how to do a particular task.


"""

import os
import glob
import yaml
from datetime import datetime


named_file_patterns = {
    'datetime': '{prefix}_{date:%Y%m%d-%H%M}.{ext}',
    'datetime-precise': '{prefix}_{date:%Y%m%d-%H%M%S}.{ext}',
    'date-seq': '{prefix}_{date:%Y%m%d}_{i:03}.{ext}',
    'image-datetime': 'image_{date:%Y%m%d-%H%M%S}.png',
    'image-date-seq': 'image_{date:%Y%m%d}_{i:03}.png',
}


def get_next_unused_filename(
        pattern="{prefix}_{i:03}.{ext}", i_range=range(1000),
        prefix="image", ext=".png",
        raise_if_none_found=True
):
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


def expand_files(files):
    """Expand glob filename patterns.
    Windows does not allow wildcard expansion at the command line prompt. Do this.
    """
    expanded = [fname for pattern in files for fname in glob.glob(pattern)]
    return expanded


def load_yaml(filepath):
    """ Load yaml from filepath """
    with open(filepath) as fp:
        r = yaml.load(fp)
    return r
