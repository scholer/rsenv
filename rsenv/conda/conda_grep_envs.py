#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2015 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##

# pylintxx: disable-msg=C0103,C0301,C0302,R0201,R0902,R0904,R0913,W0142,W0201,W0221,W0402
# pylint: disable=C0103,C0111,R0913

"""

Compare which packages are installed in which environments.


Examples:
    $> python conda_grep_envs.py show-available bio bio-python numpy pyqt5 pyqt4 pandas matplotlib --verbose
    $> python conda_grep_envs.py show-available bio numpy pyqt5 pyqt4 pandas --envs bio pyqt5
    $> python conda_grep_envs.py --verbose count bio bio-python numpy pyqt5 pyqt4 pandas matplotlib --envs bio pyqt5


Refs:
* https://docs.python.org/3/library/subprocess.html

"""


import os
import subprocess
import argparse
#import json
from json import loads, dumps


global verbose
verbose = 0


def get_conda_info(json=False):
    """
    Get information on the current conda environment.
    """
    argv = ["conda", "info"]
    if json:
        argv += ["--json"]
    output = subprocess.check_output(argv, universal_newlines=True)
    if json:
        return loads(output)
    return output


def get_conda_envs(json=False, name_only=False):
    """
    Return a list of all conda environments, as a list of tuples:
        [(<env name>, <env path>, <is active>), ...]
    """
    # get output:  conda env list
    # alternative: conda info -e
    argv = ["conda", "env", "list"]
    if json:
        argv += ["--json"]
        output = subprocess.check_output(argv, universal_newlines=True)
        return loads(output)
    if verbose:
        print("Getting conda environments...")
    output = subprocess.check_output(argv, universal_newlines=True)
    tups = [line.split() for line in output.split("\n") if line.strip() and not line[0] == "#"]
    envs = [(tup[0], tup[-1], len(tup) > 2) for tup in tups]
    if name_only:
        return [tup[0] for tup in tups]
    return envs


def get_conda_packages(env=None, regex=None, json=False, canonical=False, name_only=False):
    """
    Return a list of packages, for a particular environment <env> or for the currently active env.
    The packages list is returned as a list of tuples, with:
        [(<package name>, <version>, <info>)]

    If canonical is set to True, return a simple list of canonical package names:
        pyyaml-3.11-py34_0
    If json=True, return a list of package specs. (canonical is implied)
    """
    argv = ["conda", "list"]
    if env:
        argv += ["-n", env]
    if regex:
        argv += [regex]
    if canonical:
        argv += ["--canonical"]
    if verbose:
        print("Getting conda packages for environment", env, "...")
    if json:
        argv += ["--json"]
        output = subprocess.check_output(argv, universal_newlines=True)
        return loads(output)
    output = subprocess.check_output(argv, universal_newlines=True)
    if canonical:
        return output.split("\n")
    tups = [line.split() for line in output.split("\n") if line.strip() and not line[0] == "#"]
    if name_only:
        return [tup[0] for tup in tups]
    return tups


def get_env_packages(envs=None):
    """
    Return a dict of
        env-name : [list of linked/installed packages in environment]
    """
    if envs is None:
        envs = [tup[0] for tup in get_conda_envs()]
    env_packages = {env: get_conda_packages(env, name_only=True) for env in envs}
    return env_packages


def get_env_counts(packages, envs=None):
    """
    Return a dict with
        env-name: count of the number of packages in <packages> available in env,
    Example:
        >>> count(["bio", "pyqt5", "numpy"])
        {
            "bio": 2
            "qt": 1
            "plot": 3
        }
    """
    env_packages = get_env_packages(envs)
    env_count = {env: sum(pkg in env_pkgs for pkg in packages)
                 for env, env_pkgs in env_packages.items()}
    return env_count


def get_available(packages, envs=None):
    """
    Return a dict with an entry for each environment showing which of
    the packages in <packages> are installed/available to that environment:
        env-name: [<list of available packages in <env-name> >]
    Example:
        >>> show_available(["bio", "pyqt5", "numpy"])
        {
            "bio": ["bio", "numpy"]
            "qt": ["pyqt5"]
            "plot": ["bio", "numpy", "pyqt5"]
        }
    """
    env_packages = get_env_packages(envs)
    available = {env: [pkg for pkg in packages if pkg in env_pkgs]
                 for env, env_pkgs in env_packages.items()}
    return available


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="conda-grep-envs",
        description="Find and compare which packages are installed in which conda environments.",
        epilog=__doc__,
        add_help=True,
    )
    parser.add_argument('--verbose', '-v', action="count", help="Increase program verbosity.")
    parser.add_argument('--command', '-c', default="show-available",
                        help="The command to run. (count, show-available)")
    parser.add_argument('packages', metavar="PACKAGE", nargs="+",
                        help="One or more packages to search for.")
    parser.add_argument('--envs', '-n', metavar="ENV", nargs="*",
                        help="The environments to search (default: search all environments)")

    argsns = parser.parse_args(argv)
    return parser, argsns


def main(argv=None):
    parser, argsns = parse_args()
    global verbose
    verbose = argsns.verbose or 0
    if argsns.command is None:
        argsns.command = "show-available"
    if argsns.command == "count":
        print("## Count: ##")
        env_count = get_env_counts(argsns.packages, envs=argsns.envs)
        print("\n".join("{env}: {count}".format(env=env, count=count)
                        for env, count in env_count.items()))
    elif argsns.command == "show-available":
        print("## Which packages are available in what environments: ##")
        available = get_available(argsns.packages, envs=argsns.envs)
        print("\n".join("{}: {}".format(env, pkgs)
                        for env, pkgs in available.items()))
    else:
        print("Command '{}' not recognized...".format(argsns.command))
        parser.print_help()


if __name__ == '__main__':
    main()
