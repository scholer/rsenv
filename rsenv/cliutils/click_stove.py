# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>


"""

click-stove - provides boiler-plate Click CLI code and commands from a function.

Functions for creating Click CLI commands from basic functions.

Alternative names: fast-click, easy-click, instant-click, speed-click.




Prior art and direct alternatives:
----------------------------------

This module was mainly created to create a *minimal*, *simplistic* way to quickly generate
a click CLI after you have written a function that you want to use.

`click_stove` is NOT intended to be feature-rich or provide a lot of different options.
If that is what you want, you are probably better off either just creating an actual Click CLI,
or use one of the alternatives below:

* AutoClick is a direct alternative to this module; creating Click CLIs from type-annotated functions.
* clize - Same approach, write, document, and annotation a function, then create a CLI from that.



CLI libraries, full overview:
-----------------------------

* argparse - python's standard CLI argument parsing library.

* click - focussed on making composable and standardized CLIs. Uses function decorators.
    * https://github.com/pallets/click - 7k github stars.
    * Click deliberately uses a parser based on the old `optparse`,
      and Click has some very opinionated ideas on how to build proper CLIs.
    * Click is very advanced, extensible, but also complex.
    * AutoClick - creates Click-based CLIs using type annotations.
        * https://github.com/jdidion/autoclick
        * The AutoClick package is very similar in purpose to this function
          (but considerably more advanced and elaborate). Uses type hints.
          Sadly, it does not provide any documentation or examples on how to use
          multiple arguments (nargs=-1).
    * See also: https://github.com/click-contrib for projects that extends click in one way or another.
    * "AsyncClick (Trio-click) ist a fork of Click that works well with trio, asyncio, or curio."

* fire - Python Fire is a very fast way to generate basic CLIs. Similar to clize.
    * Hey, hosted on Google's github, nice. And almost 13k stars.
    * Has a little bit of legacy, and doesn't completely rely on python type annotations.
    * Doesn't seem to use flags; instead parses "True" and "False" as their boolean typed values.
    * Is more focused on prototyping python API functions rather than creating standard CLIs.
    * CLI interface:
        > python myapp.py --option1=value1
        > python mycommands.py command --option1=value1
    * Has things like tracebacks, etc.
    * Install from PyPI or conda-forge.
        >>> fire.Fire(callback)
        >>> fire.Fire(<module or class or object or dict-with-callbacks>)
    * https://github.com/google/python-fire/  - 13k github stars.
    * https://github.com/google/python-fire/blob/master/docs/guide.md
    * https://google.github.io/python-fire/guide/
    * https://pypi.org/project/fire/ - latest 0.2.1 release Aug 2019.

* clize - easily create CLIs from python API functions.
    * https://github.com/epsy/clize - 400 github stars.
    * Usage:
        >>> clize.run(main)
    * Rather old, first release 2011.
    * Still supports Python 2.7 (through decorators, but still).
    * Unlike many of the other CLI-generation libraries, Clize does not have separate argparser-constructors,
      instead it has a primary Clize class, which is initialized, called, then use `Clize.read_commandline(args)`
      to parse the command line arguments, extracting posargs and kwargs, which are then passed to the function.
    * Is giving me an error: "ValueError: path is on mount 'C:', start on mount 'D:'" when I try to use it.
    * https://github.com/epsy/clize/issues/37
    * After fixing the above issue, I'm getting a new error:
        > TypeError: Parameters to generic types must be types. Got 0.  # edit: fixed by using std types.
    * https://clize.readthedocs.io/en/stable/
    * https://clize.readthedocs.io/en/stable/why.html
    * https://clize.readthedocs.io/en/stable/alternatives.html - a good list of alternative CLI packages,
        and how they compare to / differ from clize.
    * https://pypi.org/project/clize - latest 4.0.3 release Jan 2018, first release Dec 2011.
    * setup requires od, attrs, docutils, sigtools, in addition to installing clize.

* defopt - "defopt is a lightweight, no-effort argument parser."
    * Uses function annotations or docstring annotations for inferring parameter types.
    * Uses `argparse` under the hood.
    * "If you want total control over how your command line looks or behaves, try docopt, click or argh."
    * Supposedly doesn't support composition.
    * This library is giving me some really useless errors and error traces when I try to use it.
      >>> defopt.run([func1, func2])
    * https://github.com/evanunderscore/defopt - 128 github stars
    * https://github.com/anntzer/defopt
    * https://defopt.readthedocs.io/en/stable/
    * https://pypi.org/project/defopt/ - latest 5.1.0 release Feb 2019, first release 2016.
    * defopt setup also requires mypy-extensions, pockets, sphinxcontrib-napoleon, typing-inspect

* plac
    * "Created to be simple" - but the docs are tediously verbose and lengthy.
    * http://micheles.github.io/plac/
    * https://github.com/micheles/plac - 91 github stars.
    * https://pypi.org/project/plac - latest release 1.0.0 Aug 2018, first release 2010.
    >>> def main(command: ("SQL query", 'option', 'c'), dsn):
    >>>     pass
    >>> plac.call(main)

* argh
    * "An argparse wrapper that doesn't make you say "argh" each time you deal with it."
    * http://argh.rtfd.org
    * https://argh.readthedocs.io/en/latest/
    * https://github.com/neithere/argh/ - 200 github stars.
    * https://pypi.org/project/argh - last release 2016, first release 2010.
    >>> argh.dispatch_command(main)
    >>> # Or, for multiple commands:
    >>> parser = argh.ArghParser()
    >>> parser.add_commands([echo, greet])

* declarative-parser
    * "Modern, declarative argument parser for Python 3.6+."
    * "Powerful like click, integrated like argparse, declarative as sqlalchemy."
    * Uses Python type annotations.
    * It has two use-cases:
        1. An alternative, perhaps easier, way of defining an argparse CLI argument parser.
        2. Construct a CLI arg-parser from either a class, function, or docstring.
    * The docs only describes argparser-constrution based on classes,
        but the `declarative_parser.constructor_parser` module also contains a FunctionParser.
    * Is a bit like argparse on steroids - produces namespaces from python classes that are built up around
      declarative_parser.Parser and declarative_parser.Argument objects.
    * https://github.com/krassowski/declarative-parser/ - 27 github stars
    * https://pypi.org/project/declarative-parser/ - latest 0.1.3 release Apr 2018.

* docopt - create CLI from a CLI help/docstring, without even creating a python API function.
    Definitely NOT what I want.
    https://github.com/docopt/docopt - 6k github stars.
    https://pypi.org/project/docopt - latest 0.6.2 release 2014.

* Clint
    * https://github.com/kennethreitz/clint - 2k github stars.
    * Mostly just tools for creating CLIs (creating TextUIs, printing text),
      not an independent CLI package.

* AutoCommand
    * "Autocommand turns a python function into a CLI program"
    * "A library to automatically generate and run simple argparse parsers from function signatures."
    * https://github.com/Lucretiel/autocommand - 15 github stars.
    * https://pypi.org/project/autocommand - latest 2.2.1 release Aug 2017.


Old/deprecated projects:

* aaargh -- Deprecated in favor of click



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

    Discussion: Supporting *varargs in functions?
    * >>> def func(arg1, arg2, *args, kwarg1="Apple", **kwargs):
    * Click does not seem to support functions that uses *args for variadic arguments.
    * That may be why autoclick decided to drop support for *args and **kwargs in functions.
        (https://github.com/jdidion/autoclick/commit/08530b87cfe6f0e5acc25721397d4bb1ec634599)
    * It might still be possible to support functions that uses *args and **kwargs,
      you just have to wrap that function up, creating a new function, that does something like:
      # Input func:
          def func(*args, kwarg1="Apple", **kwargs):
      # Wrapped func:
          def newfunc(args, kwarg1="Apple"):
              func(*args, kwarg1=kwarg1)
      For **kwargs, you could maybe use Click's ignore_unknown_options?
      Can you still parse options, even if they are not defined?
    * Hmm, it might just be too much of a hassle. If I want to support *args and **kwargs,
      I should use an underlying CLI package that supports that. And Click doesn't.
    * So, in that case, maybe just use Clize? ALthough I'm not sure Clize supports *args and **kwargs either.

    On the other hand, maybe it is just easier to create a function that outputs click decorators boilerplate?
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
        # Note: Does this have to be updated, now that you can have keyword-only arguments,
        # including "required keyword arguments"
        # def reqkw(a, b, *, required_kwarg)  # keyword-only arguments, PEP-3102.
        # def posonly(a, b, /, opt)  # Positional-only parameters, PEP-570 + PEP-457.
        # def f(pos1, pos2, /, pos_or_kwd, *, kwd1, kwd2)
        # Does this mean that you cannot just use `inspect._empty` to differentiate positional vs keyword arguments?
        # No, actually, I think using Parameter.default is still suitable to determine whether a function
        # parameter should be considered a click Argument vs Option.

        # I think the only case that is not covered is functions that have required keyword arguments:
        # * A function keyword-only argument should map to a click.Option.
        # * However, click.Option class does not accept the `required` parameter.
        # * So maybe this would be a case where you have to use click.Parameter class?
        # * We could in theory use click.Parameter for everything. However, click.Parameter class
        #   has a some things defined that are missing in click.Parameter.

        # You can use inspect.Parameter.kind enum attribute to determine what type the parameter is.
        positional_only_args = [par for parname, par in _sig.parameters.items() if par.kind is par.POSIITONAL_ONLY]
        positional_or_kw_args = [par for parname, par in _sig.parameters.items() if par.kind is par.POSITIONAL_OR_KEYWORD]
        kw_only_args = [par for parname, par in _sig.parameters.items() if par.kind is par.KEYWORD_ONLY]
        var_positional = [par for parname, par in _sig.parameters.items() if par.kind is par.VAR_POSITIONAL]
        var_keyword = [par for parname, par in _sig.parameters.items() if par.kind is par.VAR_KEYWORD]

        # All optional parameters are keyword parameters; you cannot have a positional parameters with a default value, right?
        # But required parameters can be either positional or keyword-only.
        _optional = [par for parname, par in _sig.parameters.items() if par.default is not inspect._empty]
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


