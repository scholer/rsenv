# -*- coding: utf-8 -*-
#    Copyright 2017 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""

This module is for various functions for parsing queries.

For example, get_cand_idxs_matching_expr() is used to get the indices of candidates matching
a given expression or, if the expression is an integer, assume the integer is itself an index.

This can be used for command line tools where you wish to specify e.g. what samples to plot,
e.g. plot all measurements with titles starting with 'RS511' except those containing 'B4':

    $ $ nanodrop_cli plot datafile.csv "RS511*" "-*B4*"

Alternatives:
-------------

pandas.DataFrame.query - you could just use DataFrame query directly,
    e.g. "Index > 2" - but I'm not sure how well this works for matching strings.
    Pandas query has at least three modes:
        engine='numexpr' (default) - uses [numexpr](https://numexpr.readthedocs.io/en/latest/)
        engine='python' - execute expression with python as backend.
        parser='python' - evaluation in python space. Not sure about the difference, though.
    Refs: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.eval.html

Packages/projects:

* Note: "lexx + yacc" is just shorthand for "lexing and parsing".
    The lexer splits the input stream into the interesting bits (tokens),
    and the parser re-assembles it into the big picture.

* pyparsing, seems to be a generic human-language like parser.

* Woosh (a search engine) also has a Lucene-like query language,
    http://whoosh.readthedocs.io/en/latest/parsing.html.




"""


import fnmatch
import re


def get_cand_idxs_matching_expr(expr, candidates, match_method=None, flags='', range_char="-", debug=False):
    """ Return a list of candidate indices for candidate strings matching a given value or expression.

    Is used to perform query selection of a certain subset of values from a list of strings.

    This function has two modes: "string matching" and "index matching" (or index range selection):

        1a. If `expr` is an integer, or can be cast to an integer with `int(expr)`, it is assumed to be a single index,
        and is returned as a list: `[int(expr)]`.

        1b. If the integer cast fails, but the first character in `expr` is a number (0-9),
        then we check if `expr` specifies a numeric range, e.g. `1-5` or `1:5` or `1..5`. If it does, we return
        the explicit range, i.e. `[1, 2, 3, 4, 5]`  (last-inclusive, Julia/Matlab style).

        2: If `expr` is not an integer or numeric range, then each candidate is match against `expr`,
           using the given method.

    For instance, let's say you have a list of ['red', 'blue', 'light blue', 'dark blue', 'purple']
    and you want to know the index for all elements ending "blue",
    then use `match_method="glob"` and `expr="*blue"`:
        >>> candidates = ['red', 'blue', 'light blue', 'dark blue', 'purple']
        >>> get_cand_idxs_matching_expr(expr, candidates, match_method=None)
        [1, 2, 3]  # ['blue', 'light blue', 'dark blue']

    This method (and the whole module, really) is mostly targeted parsing of command line inputs,
    where we have no built-in way to specify whether parameters are strings or integers.

    Args:
        expr: The query selection expression/value used to select which candidates (indices) to include.
        candidates: A list of candidates, typically strings.
        match_method: How to determine if a candidate value matches `expr`.
            Options include: 'exact', 'substring', 'startswith', 'glob', 'iglob', 'regex'.
            TODO: If `match_method` is 'numeric' or 'int', then don't assume that integers are indices.
        flags: flags
        range_char:

    Returns:
        List of integers,
            either (a) parsed from `expr` if `expr` is an integer or integer range,
            or (b) indices of candidates matching `expr`.

    Discussion: Order of arguments.
        The current order, `expr, candidates` was selected because it imitates the signature of `regex.match(pat, str)`,
        and also somewhat `filter(func, values)`.
        However, there is an argument to be made that the usual order is:
            As query: <data_field_or_value(s)>  <operator> <selection_value> - e.g. "priority gt 2" .
            As function: query(candidates, value, comparison_method) - e.g. query('priority', 2, operator.gt).

        For now I'll keep the current `(expr, candidates)` order, but it may be subject to change.

    Similar efforts:
        rstodo has a very general task filtering mechanism, which takes the form `-filter key comp value`
        where comp is the name of a binary operator, e.g. 'eq' or 'iglob'.

    """
    if match_method is None:
        match_method = 'glob'  # changed from 'exact'
    if match_method == 'iglob':
        # Case-insensitive matching; equivalent to passing `flags='i'`.
        match_method = 'glob'
        # Add 'i' to flags, if needed:
        flags = 'i' if flags is None else (flags + 'i' if 'i' not in flags else flags)
    if flags and 'i' in flags:
        expr = expr.lower() if isinstance(expr, str) else expr
        candidates = [cand.lower() for cand in candidates]
    try:
        # If a value/request is numeric, interpret as index:
        idxs = [int(expr)]
        return idxs
    except ValueError:
        # See if it still looks "numeric":
        if isinstance(expr, str) and expr[0] in '0123456789':
            if range_char is None:
                range_char = next((c for c in ('–', '-', ':', '..') if c in expr), None)
            if range_char is not None and range_char in expr:
                # range: 0-4  - or maybe use 0..4 or 0:4 or 0–4 (proper en-dash).
                rng = expr.split(range_char)
                if len(rng) == 2:
                    start, stop = rng
                    if range_char in ('–', '-', '..'):
                        stop += 1  # Julia-style range, last-inclusive  - 1-4 is 1, 2, 3, 4 (including 4!)
                    return list(range(start, stop))
    if match_method in ('exact', 'eq', 'equals'):
        # Exact comparison; cand is included if cand value equals expr.
        idxs = [idx for idx, cand in enumerate(candidates) if expr == cand]
    elif match_method in ('substring', 'contains'):
        # Cand value contains the given substring.
        idxs = [idx for idx, cand in enumerate(candidates) if expr in cand]
    elif match_method in ('startswith', ):
        # Cand value startswith the given substring.
        idxs = [idx for idx, cand in enumerate(candidates) if cand.startswith(expr)]
    elif match_method == 'in':
        # Cand value is contained in the given substring. E.g. use "RS123 RS124 RS125" to include those three cands.
        # Although typically you would use translate_all_requests_to_idxs to select multiple candidates.
        idxs = [idx for idx, cand in enumerate(candidates) if cand in expr]
    else:
        # Regex comparisons: 'full-word', 'glob'/'fnmatch', 'regex',
        if match_method == 'full-word':
            # Use negative look-behind/ahead to ensure we have a full word:
            expr = ""  # TODO: REGEX FOR FULL-WORD MATCH NOT IMPLEMENTED.
            match_method = 'regex'
            raise NotImplementedError("REGEX FOR FULL-WORD MATCH NOT IMPLEMENTED.")
        elif match_method in ('glob', 'fnmatch', 'fnmatchcase'):
            # use fnmatch._compile_pattern if you want a compiled, cache-enabled optimization
            expr = fnmatch.translate(expr)
            match_method = 'regex'
        if match_method == 'regex':
            if debug:
                print("  regex:", expr)
            regex = re.compile(expr) if isinstance(expr, str) else expr
            idxs = [idx for idx, cand in enumerate(candidates) if regex.match(cand)]
        else:
            raise ValueError(f"Unknown `match_method` {match_method}")
    return idxs


def translate_all_requests_to_idxs(
        requests, candidates, match_method='glob',
        include_method='list-extend', exclude_method='list-remove',
        strict=False, min_query_selection=0, debug=False
):
    """Used to select a number of candidates based on a list of query requests.
    
    Requests are parsed sequentially. So, you can say the equivalent of 
        "Select all candidates, except those named 'John', although do include 'John Hancock'."
    which would be:
        all -John "John Hancock"        # with match_method='substring'
    or:
        all -"John*" "John Hancock"     # with match_method='glob'

    Example of requests:
        (query)     (meaning)
        all         special keyword; include all
        John        include all candidates matching "John"
        -James      exclude all candidates matching "James".
        2           integer values are interpreted as numeric indices for the candidates list (zero-based).
        -4          exclude the 5th candidate (index 4).
        1-4         range, include candidates 1 through 4 (both inclusive, but remember first index is 0).
    
    By default, "John" only matches candidates that are exactly "John", in which case the 
    "all Johns except John Hancock" example doesn't make much sense.
    However, you can use 
    
    Args:
        requests: A list of selection requests, each request being either a keyword or selection `expr` passed
            to
        candidates: 
        match_method: How each candidate is matched against each of the requested queries.
            Options: 'glob', 'regex', 'full-word', 'exact', 'contains', 'in', 'startswith', 'endswith'.
        include_method: How to merge idxs with previously-selected idxs. Options are:
            'set-sorted': Set-merge new idxs with previous, followed by sort.
            'list-extend': Just add the list of new idxs to the existing idxs list. May cause duplicates.
            'extend-unique': Add new unique idxs to existing idxs list, ignoring idxs already selected (avoid dups).
        exclude_method: How to remove idxs for negative selections (queries starting with a hyphen-minus).
        strict: If True, will raise an exception if negative selections contains idxs not already selected.
            (Default is False, which will just ignore negative selection idxs not selected by previous queries.)
        min_query_selection: The minimum number of candidates that must be selected for each query.
            Is usually just set to 1 to make sure all queries are successful.

    Returns:

    # Alternative names for "requests": directives, queries, query-parameter, query-request, query-parameters?
    """
    idxs = []
    for request in requests:
        exclude = request[0] == '-'
        request = request[1:] if request[0] in ('-', '+') else request  # trim plus or minus prefixes.
        if request == 'all':
            r_idxs = list(range(len(candidates)))
        else:
            r_idxs = get_cand_idxs_matching_expr(request, candidates, match_method=match_method, debug=debug)
        if len(r_idxs) < min_query_selection:
            raise ValueError(f"Only {len(r_idxs)} candidates selected from query {request!r}.")
        if exclude:
            if exclude_method in ('greedy', 'list-comprehension'):
                idxs = [idx for idx in idxs if idx not in r_idxs]
            elif exclude_method == 'list-remove':
                for idx in r_idxs:
                    try:
                        idxs.remove(idx)
                    except ValueError as exc:
                        if strict:
                            print(f"idxs.remove({idx}) failed; idxs = {idxs}")
                            raise exc
            elif exclude_method == 'set-sorted':
                idxs = sorted(set(idxs) - set(r_idxs))
            else:
                raise ValueError(f"`exclude_method` {exclude_method} not recognized.")
        else:
            if include_method == 'set-sorted':
                idxs = sorted(set(idxs) | set(r_idxs))
            elif include_method == 'list-extend':
                idxs.extend(r_idxs)
            elif include_method == 'extend-unique':
                idxs.extend([idx for idx in r_idxs if idx not in idxs])
            else:
                raise ValueError(f"`include_method` {include_method} not recognized.")
        if debug:
            opstring = "-" if request[0] == '-' else "+"
            print(f" + {request:14s} = {opstring}{r_idxs} --> {idxs}")
    return idxs



def data_query_filter(data, filters):
    pass


