# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Utility functions for staple pooling modules.

"""


def read_lines_from_file(fn, comment_char='#', skip_empty_lines=True, strip_lines=True):
    """ Read a single staple pool file. """
    with open(fn) as f:
        lines = [line for line in f]
    # Remove comments:
    if comment_char:
        lines = [line.split(comment_char, 1)[0] for line in lines]
    if strip_lines:
        lines = [line.strip() for line in lines]
    if skip_empty_lines:
        lines = [line for line in lines if lines]
    return lines
