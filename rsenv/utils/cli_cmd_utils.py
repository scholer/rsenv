# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>


"""

Some utility functions for creating Click CLI commands from basic functions.

Reading/Writing Excel files with Pandas:

* xlrd - read only
* openpyxl - read + write, xlsx/xlsm/xltx/xltm files.
* xlsxwriter - write xlsx files.

Other Excel libs:

* xlutils
* pyexcel
* pyxll - use python from within Excel.
* Pandas - read/write excel spreadsheets to DataFrames

OBS: Pandas currently only supports `xlrd` for reading xlsx files.

Refs:

* https://xlsxwriter.readthedocs.io/alternatives.html


CLI libraries overview:

    * argparse - python's standard CLI argument parsing library.
    * click - focussed on making composable and standardized CLIs. Uses function decorators.
        https://github.com/pallets/click - 7k github stars.
    * fire - Python Fire is a very fast way to generate basic CLIs. Similar to clize.
        Hey, hosted on Google's github, nice. And almost 13k stars.
        Has a little bit of legacy, and doesn't completely rely on python type annotations.
        Doesn't seem to use flags; instead parses "True" and "False" as their boolean typed values.
        Is more focused on prototyping python API functions rather than creating standard CLIs.
        Has things like tracebacks, etc.
        Install from PyPI or conda-forge.
        >>> fire.Fire(callback)
        >>> fire.Fire(<module or class or object or dict-with-callbacks>)
        https://github.com/google/python-fire/  - 13k github stars.
        https://github.com/google/python-fire/blob/master/docs/guide.md
        https://google.github.io/python-fire/guide/
        https://pypi.org/project/fire/ - latest 0.1.3 release Jan 2018.
    * clize - easily create CLIs from python API functions.
        >>> clize.run(main)
        https://github.com/epsy/clize - only 400 github stars.
        Rather old, first release 2011.
        Is giving me an error: "ValueError: path is on mount 'C:', start on mount 'D:'" when I try to use it.
        https://github.com/epsy/clize/issues/37
        After fixing the above issue, I'm getting a new error:
        >   "TypeError: Parameters to generic types must be types. Got 0." - edit: fixed by using std types.
        https://clize.readthedocs.io/en/stable/
        https://clize.readthedocs.io/en/stable/why.html
        https://clize.readthedocs.io/en/stable/alternatives.html
        https://pypi.org/project/clize - latest 4.0.3 release Jan 2018, first release Dec 2011.
        setup requires od, attrs, docutils, sigtools, in addition to installing clize.
    * defopt - "defopt is a lightweight, no-effort argument parser."
        Uses function annotations or docstring annotations for inferring parameter types.
        Uses `argparse` under the hood.
        "If you want total control over how your command line looks or behaves, try docopt, click or argh."
        Supposedly doesn't support composition.
        This library is giving me some really useless errors and error traces when I try to use it.
        >>> defopt.run([func1, func2])
        https://github.com/evanunderscore/defopt - 120 github stars
        https://defopt.readthedocs.io/en/stable/
        https://pypi.org/project/defopt/ - latest 5.0.0 release 2018, first release 2016.
        defopt setup also requires mypy-extensions, pockets, sphinxcontrib-napoleon, typing-inspect
    * plac
        "Created to be simple" - but the docs are tediously verbose and lengthy.
        http://micheles.github.io/plac/
        https://github.com/micheles/plac - 91 github stars.
        https://pypi.org/project/plac - latest release 1.0.0 Aug 2018, first release 2010.
        >>> def main(command: ("SQL query", 'option', 'c'), dsn):
        >>>     pass
        >>> plac.call(main)
    * argh
        https://argh.readthedocs.io/en/latest/
        https://github.com/neithere/argh/ - 200 github stars.
        https://pypi.org/project/argh - last release 2016, first release 2010.
        >>> argh.dispatch_command(main)
        >>> # Or, for multiple commands:
        >>> parser = argh.ArghParser()
        >>> parser.add_commands([echo, greet])
    * declarative-parser
        "Modern, declarative argument parser for Python 3.6+."
        "Powerful like click, integrated like argparse, declarative as sqlalchemy."
        Is a bit like ArgParse on steroids - produces namespaces from python classes that are built up around
        declarative_parser.Parser and declarative_parser.Argument objects.
        https://github.com/krassowski/declarative-parser/ - 20 github stars
        https://pypi.org/project/declarative-parser/ - latest 0.1.3 release Apr 2018.
    * docopt - create CLI from a CLI help/docstring, without even creating a python API function.
        Definitely NOT what I want.
        https://github.com/docopt/docopt - 6k github stars.
        https://pypi.org/project/docopt - latest 0.6.2 release 2014.
    * Clint
        https://github.com/kennethreitz/clint - 2k github stars.
        Mostly just tools for creating CLIs?
    * AutoCommand
        "Autocommand turns a python function into a CLI program"
        "A library to automatically generate and run simple argparse parsers from function signatures."
        https://github.com/Lucretiel/autocommand - 15 github stars.
        https://pypi.org/project/autocommand - latest 2.2.1 release Aug 2017.


Other interesting things:

* http://xion.io/post/programming/python-dont-use-click.html - says click is too simple and supports an
    unfortunate use case of just "slap some decorators on our top-level functions and call it a day".
    Recommends just sticking to the argparse module instead.
    Also mentions Docopt (Python) and Grunt and Gulp (Javascript runners)
* https://realpython.com/comparing-python-command-line-parsing-libraries-argparse-docopt-click/
* https://medium.com/@collectiveacuity/argparse-vs-click-227f53f023dc
* https://kite.com/blog/python/python-command-line-click-tutorial
* https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
    Argparse, Click, DocOpt, PyInquirer, PyFiglet, Clint, Cement, Cliff, Plac, SendGrid,
* https://news.ycombinator.com/item?id=17785168
* https://github.com/chriskiehl/Gooey - turn CLIs into GUIs.
* https://github.com/spotify/luigi
*

"""

from collections import defaultdict
import typing
import inspect
import click


def create_click_cli_command(callback, params=None, help=None, epilog=None, short_help=None,
                             options_metavar='[OPTIONS]', add_help_option=True, arg_spec=None):
    """ Create a Click CLI Command for a function `callback`.

    Alternatively, just use:
        >>> import fire
        >>> fire.Fire(callback)

    I've also tried to use `defopt` and `clize`, but I never got them to work.

    I basically created this because I got tired of all the annoying boilerplate
    that I had to write to create a CLI that calls a single function.

    Args:
        callback:
        params:
        help:
        epilog:
        short_help:
        options_metavar:
        add_help_option:

    Returns:
        Click CLI Command

    Note: I think maybe you can also use the `context_settings` click.Command parameter for doing this.
    http://click.palletsprojects.com/en/7.x/api/#context
    However, I haven't quite found the right way of doing this yet.

        CONTEXT_SETTINGS = dict(
            # provide custom defaults:
            default_map={'runserver': {'port': 5000}},
            help_option_names=['-h', '--help'],
            token_normalize_func=lambda x: x.lower(),
            ignore_unknown_options=True,
        )
    Edit: click context_settings is just the parameters forwarded to a specific click.Command.

    Alternatively, consider using CLI libraries that were specifically made to easily convert
    python API function to CLIs without any boilerplate, e.g. `clize` and `fire`.

    """
    _sig = inspect.signature(callback)
    # _argspec = inspect.getfullargspec(callback)
    if help is None:
        help = inspect.getdoc(callback)
    if arg_spec is None:
        arg_spec = defaultdict(dict)
    # print("arg_spec:", arg_spec)
    # print(_sig.parameters)
    LIST_ARGSPEC = {'nargs': -1}
    if params is None:
        _optional = [par for parname, par in _sig.parameters.items() if not par.default is inspect._empty]
        _required = [par for parname, par in _sig.parameters.items() if par.default is inspect._empty]
        # print("Optional parameters:", _optional)
        # print("Required parameters:", _required)
        options = [
            click.Option([f"--{par.name.replace('_', '-')}"], default=par.default)
            for par in _optional
        ]
        # for par in _required:
        #     print(par.name, ":", arg_spec.get(par.name, {}))
        # TODO: Use python function parameter annotations to create arg_spec for click.Argument
        # TODO: Primarily determining if argument is plural (list, nargs=-1) or singular (int/str/etc, nargs=1).
        # TODO: and perhaps also type (mostly boolean values and pathlib.Path).
        arguments = [click.Argument(
            [f"{par.name.replace('_', '-')}"], **arg_spec.get(
                par.name, LIST_ARGSPEC if par.annotation == typing.List or par.kind == par.VAR_POSITIONAL else {}))
                     for par in _required]
        params = options+arguments
        # print("Click params:", params)
    return click.Command(
        callback=callback,
        name=callback.__name__,
        help=help,
        params=params,
    )


