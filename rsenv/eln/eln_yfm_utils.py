# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

"""

Module for extracting and parsing YAML Front-Matter from documents.

"""

import re
import yaml
try:
    import frontmatter
except ImportError:
    print("`frontmatter` package not available; using local routines.")
    frontmatter = None

from zepto_eln.md_utils.yfm import split_yfm, parse_yfm
