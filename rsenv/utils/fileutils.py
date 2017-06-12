
"""

Utility/aggregation module with various small functions for dealing with files and filesystems.

Functions are often simply "reference functions", used to exemplify how to do a particular task.


"""

import yaml


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
