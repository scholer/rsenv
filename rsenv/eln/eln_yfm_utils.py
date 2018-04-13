# Copyright 2018 Rasmus Scholer Sorensen

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


def split_yfm(raw_content, sep_regex=r'^-{3,}$', require_leading_marker='raise', require_empty_pre=False):
    yfm_sep_regex = re.compile(sep_regex, re.MULTILINE)
    splitted = yfm_sep_regex.split(raw_content, 2)  # Split at most two times (into three parts) on regex matches.

    if len(splitted) == 1:
        raise ValueError(f"Unable to extract YAML frontmatter from text; no matches for {sep_regex!r}")
    if len(splitted) == 2:
        if require_leading_marker:
            if require_leading_marker == 'raise':
                raise ValueError(f"Only found one YFM marker ({sep_regex!r}).")
            else:
                print(f"WARNING: Only found one YFM marker ({sep_regex!r}).")
        yfm_content, md_content = splitted
    else:
        pre, yfm_content, md_content = splitted
        if require_empty_pre:
            assert not pre.strip()
    return yfm_content, md_content


def parse_with_frontmatter(text):
    """ Parse, using the 'frontmatter' package. """
    import frontmatter
    from frontmatter import YAMLHandler
    # Unfortunately, frontmatter.parse doesn't have any way to determine if splitting gives an error (only YAML load).
    metadata, content = frontmatter.parse(text, handler=YAMLHandler)
    return metadata, content


def parse_yfm(raw_content, sep_regex=r'^-{3,}$', require_leading_marker='raise', require_empty_pre=False):
    """ Parse Yaml Front Matter from text and return metadata dict and stripped content.

    Args:
        raw_content:
        sep_regex: The regex on which the YFM is separated from the surrounding text.
        require_leading_marker: Raise error if only one YFM marker is found.
        require_empty_pre: Raise error if the part before the YFM is not empty.

    Returns:
        Two-tuple of (frontmatter/metadata dict, and remaining, stripped, content).

    """
    if frontmatter:
        return parse_with_frontmatter(raw_content)

    yfm_content, md_content = split_yfm(
        raw_content, sep_regex=sep_regex,
        require_leading_marker=require_leading_marker, require_empty_pre=require_empty_pre)
    yfm = yaml.load(yfm_content)  # Exception caught in outer functions that has knowledge about filename.
    return yfm, md_content

