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
from collections import defaultdict

from zepto_eln.md_utils.document_io import load_all_documents_metadata

REQUIRED_PICO_KEYS = ('title', 'description', 'author', )
REQUIRED_EXP_KEYS = ('expid', 'titledesc', 'status', 'startdate', 'enddate', 'result')
REQUIRED_KEYS = REQUIRED_PICO_KEYS + REQUIRED_EXP_KEYS
NODEFAULT = object()


def find_md_files(basedir='.', pattern=r'*.md', pattern_type='glob'):
    # return list(find_files(start_points=[basedir], include_patterns=[pattern]))
    # Alternative, using glob:
    return glob.glob(os.path.join(basedir, '**/*.md'))


def pico_find_variable_placeholders(content, pat=r"%[\w\.]+%"):
    if isinstance(pat, str):
        pat = re.compile(pat)
    print("type(content):", type(content))
    res = pat.findall(content)
    print("type(res):", type(res))
    return set(res)  # Set to remove duplicates


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


def substitute_pico_variables(content, template_vars, errors='pass', varfmt="{sub}"):
    """ Perform Pico-style %variable% substitution. """
    # variable members are available as %variable.attribute%
    # Two approaches:
    #   a. Extract variables from document and substitute them. [we use this one]
    #   b. Generate all possible variable placeholder strings and do str.replace(placeholder, value).
    placeholders = pico_find_variable_placeholders(content)
    if isinstance(varfmt, str):
        _varfmt = varfmt
        varfmt = defaultdict(lambda: _varfmt)
    for placeholder in placeholders:
        # Note: We probably shouldn't do replacements inside comments, but whatever.
        varname = placeholder.strip('%')
        try:
            sub = get_attrs_string_value(template_vars, varname)
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
            # sub can be e.g. lists or dicts; the format string can be customized for each variable.
            content = content.replace(placeholder, varfmt[varname].format(sub, var=sub, sub=sub))
    return content


def print_document_yfm_issues(
        basedir='.',
        required_keys=REQUIRED_KEYS,
):
    """ Print journals that have YFM issues, e.g. missing YFM keys. """
    required_keys = set(required_keys)
    journals = load_all_documents_metadata(basedir=basedir, add_fileinfo_to_meta=True)
    for meta in journals:
        missing = required_keys.difference(meta.keys())
        if missing:
            print("FILE:", meta['filename'])
            print(" - MISSING KEYS:", missing)