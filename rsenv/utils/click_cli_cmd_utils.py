# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>


"""

Some utility functions for creating Click CLI commands from basic functions.

"""

import click
import inspect


def create_click_command(callback, params=None, help=None, epilog=None, short_help=None,
                         options_metavar='[OPTIONS]', add_help_option=True):
    """ Create a Click CLI Command for a function `callback`.

    Note: I think maybe you can also use the `context_settings` click.Command parameter for doing this.

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
    """
    _sig = inspect.signature(callback)
    # _argspec = inspect.getfullargspec(callback)
    if help is None:
        help = inspect.getdoc(callback)
    # print(_sig.parameters)
    if params is None:
        _optional = [par for parname, par in _sig.parameters.items() if not par.default is inspect._empty]
        _required = [par for parname, par in _sig.parameters.items() if par.default is inspect._empty]
        # print("Optional parameters:", _optional)
        # print("Required parameters:", _required)
        options = [
            click.Option([f"--{par.name.replace('_', '-')}"], default=par.default)
            for par in _optional
        ]
        arguments = [click.Argument([f"{par.name.replace('_', '-')}"]) for par in _required]
        params = options+arguments
    return click.Command(
        callback=callback,
        name=callback.__name__,
        help=help,
        params=params,
    )


