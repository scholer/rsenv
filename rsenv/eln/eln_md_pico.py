# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

"""

Module for dealing with Electronic laboratory notebook journals in Pico Markdown format,
as used with e.g. the Nextcloud Pico_CMS app.

Pico Markdown documents are generally just markdown documents with a standard "YAML front matter" (YFM) header,
separated by the main document with "---" on a single, separate line (also indicates "end of document" in YAML).

Pico Markdown documents supports %variable_placeholders%, e.g. %meta.title%, where meta is the YFM header.

Regarding document variable placeholders:

* `%variable%` - Standard variable placeholder format for Pico CMS (including Nextcloud app).
    Can access child members: `%variable.attribute%`.
    I think this was specifically chosen to be different from the Twig {{variable}} templating used downstream.


* `{{ variable }}`
    * This style is used by: Jinja, Django, Twig, Liquid, Jekyll.
        Django used to have its own Django Template Language that also used `{{ variable }}` type placeholders.
        > "Jinja2 is a modern and designer friendly templating language for Python, modelled after Django’s templates."
    * Supports pipe-filters and for-loops, e.g. `{% for p in pages|sort_by('time')|reverse %}`.
    * Judging by https://github.com/picocms/Pico/issues/142, Pico at least used to support this as well.


Regarding Pico CMS theming:

* Uses Twig.
* Some variables are available to both Twig templating variables, and the Pico %variable% preprocessor.
    Specifically, metadata is available to both: `{{ meta.attr }}` and `%meta.attr%`.
* Others maybe not? E.g. %site_title%, %base_url%, %theme_url%.
* I am not sure whether I can use Twig variables in my Markdown documents, or only in my Twig templates.
    I think the parsed markdown is just inserted into the Twig template as a a `{{ content }}` variable.
    If this is true, then it certainly *only* makes sense to use `%variables%` within my markdown ELN journals.


Other projects with similar or related aims:

* https://github.com/Python-Markdown/markdown has a meta-data parser, but is is self-rolled, and the consensus
    converged on the conclusion that it was better to have a separate YFM preprocessor, rather than
    yet another extension.
    * https://python-markdown.github.io/extensions/meta_data/
    * https://github.com/Python-Markdown/markdown/issues/497

* python-frontmatter,
    [github](https://github.com/eyeseast/python-frontmatter), [pypi](https://pypi.org/project/python-frontmatter/)
    Jekyll-style YAML front matter offers a useful way to add arbitrary, structured metadata to text documents.
    The YFM must begin and end with a line of '---'. (Same as Pico.)
    Has functions `frontmatter.load` and `frontmatter.parse`;
    the former will produce a full `document` object with `doc.content` and `doc.metadata` attributes.
    Supports YAML, JSON, and TOML.

* docdata
    * [github](https://github.com/waylan/docdata)
    * "A better Meta-Data handler for lightweight markup languages.".


Converting Markdown to HTML:

* Python-Markdown
    * `pip install markdown`
    * [github](https://github.com/Python-Markdown/markdown),
        [pypi](https://pypi.python.org/pypi/Markdown), [docs](https://python-markdown.github.io/)
    * Supports a number of extensions to change the behaviour of the markdown parser and HTML generator.
    * Seems like the most standard python markdown parser. Used by e.g. MkDocs.

* ghmarkdown
    * `pip install ghmarkdown`
    * [github](), [pypi](https://pypi.python.org/pypi/ghmarkdown), [docs]().
    * Uses the official GitHub web API, limited to 60 requests/hour or 5000 requests/hour if logged in.
    * Uses requests, argparse.
    * Has nice "server' feature for continuous updates. Although just opening a file in browser is the same.
    * Cons: Makes use of a lot of global variables, against best practices.
    * Usage:

        $ ghmarkdown -i my_file.md -o my_page.html`
        $ cat my_file.md | ghmarkdown > my_page.html
        $ ghmarkdown --serve --port 8000 --input my_file.md

* https://github.com/joeyespo/grip

* Python-Markdown2
    * `pip install markdown2`
    * [github](https://github.com/trentm/python-markdown2)
    * Very old, but still updated recently (2017).

* Pandoc
    * As always, Pandoc can probably do it.

* Refs:

    * http://sebastianraschka.com/Articles/2014_markdown_syntax_color.html  - uses Python-Markdown and Pygments.
    * https://gist.github.com/jiffyclub/5015986
        - Python-Markdown with mdx_smartypants and jinja2 "{{variable}}" templating.
    *

Other:

* R-Markdown: Use a productive notebook interface to weave together narrative text and code (R, Python, SQL).


"""

import os
import glob
import re
import yaml
import yaml.scanner
import pandas as pd
import click
import inspect

from rsenv.fileutils.fileutils import find_files
from rsenv.eln.eln_yfm_utils import parse_yfm

WARN_MISSING_YFM = False
WARN_YAML_SCANNER_ERROR = True

REQUIRED_PICO_KEYS = ('title', 'description', 'author', )
REQUIRED_EXP_KEYS = ('expid', 'titledesc', 'status', 'startdate', 'enddate', 'result')
REQUIRED_KEYS = REQUIRED_PICO_KEYS + REQUIRED_EXP_KEYS


def find_md_files(basedir='.', pattern=r'*.md', pattern_type='glob'):
    # return list(find_files(start_points=[basedir], include_patterns=[pattern]))
    # Alternative, using glob:
    return glob.glob(os.path.join(basedir, '**/*.md'))


def read_journal(fn, add_fileinfo_to_meta=True, warn_yaml_scanner_error=None):
    if warn_yaml_scanner_error is None:
        warn_yaml_scanner_error = WARN_YAML_SCANNER_ERROR
    dirname, basename = os.path.split(fn)
    fnroot, fnext = os.path.splitext(basename)
    fileinfo = {
        'filename': fn,
        'dirname': dirname,
        'basename': basename,
        'fnroot': fnroot,
        'fnext': fnext
    }
    with open(fn, 'r', encoding='utf-8') as fd:
        raw_content = fd.read()
    try:
        yfm, md_content = parse_yfm(raw_content)
    except yaml.scanner.ScannerError as exc:
        if warn_yaml_scanner_error:
            if warn_yaml_scanner_error == 'raise':
                raise exc
            print(f"WARNING: YAML ScannerError while parsing YFM of file {fn}.")
        yfm = None
        md_content = None

    if add_fileinfo_to_meta and yfm is not None:
        yfm.update(fileinfo)
    journal = {
        'filename': fn,
        'fileinfo': fileinfo,
        'raw_content': raw_content,
        # 'yfm_content': yfm_content,
        'md_content': md_content,
        'content': md_content,
        'meta': yfm,
    }
    return journal


def pico_find_variable_placeholders(content, pat=r"%[\w\.]+%"):
    if isinstance(pat, str):
        pat = re.compile(pat)
    print("type(content):", type(content))
    res = pat.findall(content)
    print("type(res):", type(res))
    return set(res)  # Set to remove duplicates


NODEFAULT = object()


def get_attrs_string_value(dct, attrs, default=NODEFAULT):
    """ Get attribute from object string: dict.key1.subkey2.subsubkey

    Args:
        dct:
        attrs: A string 'attr0.attr1.attr2' or list ['attr0', 'attr1', 'attr2']
        default: A default value if the given attrs string wasn't found.
            If no default is given, a KeyError is raised.

    Returns:
        The value given by attrs.

    Examples:
        >>> a = {'h': {'e': {'j': 'word'}}}
        >>> get_attrs_string_value(a, 'h.e.j')
        'word'

    """
    if isinstance(attrs, str):
        attrs = attrs.split('.')
    key, *rest = attrs
    try:
        val = dct[key]
    except TypeError:
        val = getattr(dct, key)
    except KeyError as exc:
        if default is not NODEFAULT:
            return default
        else:
            raise exc
    if rest:
        return get_attrs_string_value(val, attrs=rest, default=default)
    else:
        return val


def pico_variable_substitution(content, vars, errors='pass'):
    """ Perform Pico-style %variable% substitution. """
    # variable members are available as %variable.attribute%
    # Two approaches:
    #   a. Extract variables from document and substitute them.
    #   b. Generate all possible variable placeholder strings and do str.replace(placeholder, value).
    placeholders = pico_find_variable_placeholders(content)
    for placeholder in placeholders:
        # Note: We probably shouldn't do replacements inside comments, but whatever.
        try:
            sub = get_attrs_string_value(vars, placeholder.strip('%'))
        except KeyError as exc:
            # E.g. if you have a comment explaining %meta.variable%:
            if errors == 'raise':
                raise exc
            elif errors == 'print':
                print(f"{exc.__class__.__name__}: {exc}")
            elif errors == 'pass':
                pass
            else:
                raise ValueError(f"Value {errors!r} for parameter `errors` not recognized.")
        else:
            print(f"Replacing {placeholder!r} -> {sub!r}")
            content = content.replace(placeholder, repr(sub))  # sub can be e.g. lists or dicts.
    return content


def get_journals(basedir='.', add_fileinfo_to_meta=True, exclude_if_missing_yfm=True):
    """ Find all Markdown journals (recursively) within a given base directory.

    Args:
        basedir: The directory to look for ELN journals in.
        add_fileinfo_to_meta: Whether to add fileinfo to the journal's metadata (the parsed YFM).
        exclude_if_missing_yfm: Exclude pages if they don't have YAML front-matter.

    Returns:
        List of journal dicts.

    """
    files = find_md_files(basedir=basedir)
    journals = []
    for fn in files:
        journal = read_journal(fn, add_fileinfo_to_meta=add_fileinfo_to_meta)
        if journal['meta'] is not None or not exclude_if_missing_yfm:
            journals.append(journal)
    return journals


def get_journals_metadata(basedir='.', add_fileinfo_to_meta=True, exclude_if_missing_yfm=True):
    """ Find journals and extract metadata.

    Args:
        basedir: The directory to find journals in.
        add_fileinfo_to_meta: Whether to add fileinfo (e.g. filename, directory, etc).
        exclude_if_missing_yfm: Exclude journals/files if they don't have any YAML front-matter.

    Returns:
        List of metadata dicts.
    """
    journals = get_journals(
        basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta, exclude_if_missing_yfm=exclude_if_missing_yfm)
    # print("\n".join("{}: {}".format(j['filename'], type(j['meta'])) for j in journals))
    metadata = [journal['meta'] for journal in journals]
    return metadata


def get_started_exps(basedir='.', add_fileinfo_to_meta=True):
    """ Get metadata for journals with status='started'. """
    all_meta = get_journals_metadata(
        basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta, exclude_if_missing_yfm=True)
    started = [m for m in all_meta if m['status'] == 'started']
    return started


def get_unfinished_exps(basedir='.', add_fileinfo_to_meta=True):
    """ Journals where either status is not ('completed' or 'cancelled') or 'complete' but enddate is None.
    Edit: This is just where enddate is None and 'status' is not 'cancelled'.
    """
    all_meta = get_journals_metadata(
        basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta, exclude_if_missing_yfm=True)
    started = [
        m for m in all_meta
        # if m.get('status') != 'cancelled' and (m.get('status') != 'completed' and m.get('enddate') is not None)
        # if not (m.get('status') == 'cancelled' or (m.get('status') == 'completed' and m.get('enddate') is not None))
        if m.get('enddate') is None and m.get('status') != 'cancelled'
    ]
    return started


def print_started_exps(basedir='.', rowfmt="{expid:<10} {titledesc}"):
    """ Print journals with status='started'. """
    started = get_started_exps(basedir=basedir)
    print("\n".join(rowfmt.format(**meta) for meta in started))


def print_unfinished_exps(basedir='.', rowfmt="{expid:<10} {titledesc}", print_header=True):
    """ Print journals with status not 'completed'. """
    unfinished = get_unfinished_exps(basedir=basedir)
    # print("\n".join(rowfmt.format(**meta) for meta in unfinished))
    if print_header:
        keys_titlecased = [k.title() for k in REQUIRED_KEYS]
        hdr_str = rowfmt.format(**dict(zip(REQUIRED_KEYS, keys_titlecased)))
        print(hdr_str)
        print("-"*(len(hdr_str)+8*hdr_str.count("\t")))
    for meta in unfinished:
        try:
            print(rowfmt.format(**meta))
        except KeyError as exc:
            print("{}: {}, for file {} - keys: {}".format(exc.__class__.__name__, exc, meta['filename'], meta.keys()))


def print_journal_yfm_issues(
        basedir='.',
        required_keys=REQUIRED_KEYS,
):
    """ Print journals that have YFM issues, e.g. missing YFM keys. """
    required_keys = set(required_keys)
    journals = get_journals_metadata(basedir=basedir, add_fileinfo_to_meta=True)
    for meta in journals:
        missing = required_keys.difference(meta.keys())
        if missing:
            print("FILE:", meta['filename'])
            print(" - MISSING KEYS:", missing)


# Pandas DataFrame versions of the functions above (if you prefer the convenience of DataFrames):

def get_journals_metadata_df(basedir='.', add_fileinfo_to_meta=True):
    """ Get journal metadata as a Pandas DataFrame. """
    metadata = get_journals_metadata(basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta)
    df = pd.DataFrame(metadata)
    return df


def get_started_exps_df(basedir='.', add_fileinfo_to_meta=True):
    """ Get metadata DataFrame with journals where status='started'. """
    df = get_journals_metadata_df(basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta)
    df = df.loc[df['status'] == 'started', :]
    return df


def print_started_exps_df(basedir='.', cols=('expid', 'titledesc')):
    """ Print metadata DataFrame with journals where status='started'. """
    df = get_started_exps_df(basedir=basedir)
    print(df.loc[:, cols])


print_started_exps_cli = click.Command(
    callback=print_started_exps,
    name=print_started_exps.__name__,
    help=inspect.getdoc(print_started_exps),
    params=[
        click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc}'),  # remember: param_decls is a list, *decls.
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])


print_unfinished_exps_cli = click.Command(
    callback=print_unfinished_exps,
    name=print_unfinished_exps.__name__,
    help=inspect.getdoc(print_unfinished_exps),
    params=[
        click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc:<40}  [enddate: {enddate}]'),
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])


print_journal_yfm_issues_cli = click.Command(
    callback=print_journal_yfm_issues,
    name=print_journal_yfm_issues.__name__,
    help=inspect.getdoc(print_journal_yfm_issues),
    params=[
        # click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc} (enddate={enddate})'),
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])

if __name__ == '__main__':
    # print_started_exps_cli()
    # print_unfinished_exps_cli()
    print_journal_yfm_issues_cli()
