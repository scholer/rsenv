# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module and CLI for doing order-independent comparison of lines in a file.

Alternatively, you can also just sort the lines in each file before sorting:

    > sort file1.txt > file1_sorted.txt
    > sort file2.txt > file2_sorted.txt
    > diff file1.txt file2.txt

Or just directly (in Bash shell):

    > diff <(sort file1) <(sort file2)


"""

import re
from collections import Counter
from termcolor import cprint
import click


def process_lines(
        lines,
        strip_lines: bool = True,
        remove_whitespace: bool = True,
        remove_empty_lines: bool = True,
        normalize_case: bool = True,
        remove_patterns=None,
):
    if strip_lines:
        lines = [line.strip() for line in lines]
    if remove_empty_lines:
        lines = [line for line in lines if line.strip()]
    if remove_whitespace:
        lines = [line.replace(" ", "").replace("\t", "") for line in lines]
    if remove_patterns:
        if isinstance(remove_patterns, str):
            remove_pattern = [remove_patterns]
        for regex in remove_patterns:
            if isinstance(regex, str):
                regex = re.compile(regex)
            lines = ["".join(regex.split(line)) for line in lines]
    if normalize_case:
        lines = [line.lower() for line in lines]

    return lines


def order_independent_line_comparison(
        lines1, lines2, *,
        strip_lines: bool = True,
        remove_whitespace: bool = True,
        remove_empty_lines: bool = True,
        normalize_case: bool = True,
        remove_patterns=None,
        # Whether to reduce the list of lines/sequences to a set:
        remove_duplicates: bool = True,
        sort_output: str = "linenumbers",
):
    """ """

    lines1_linenumbers = {
        line: lineno
        for lineno, line in enumerate(lines1)
    }

    lines2_linenumbers = {
        line: lineno
        for lineno, line in enumerate(lines2)
    }

    lines1 = process_lines(
        lines1, strip_lines=strip_lines, remove_whitespace=remove_whitespace,
        remove_empty_lines=remove_empty_lines, normalize_case=normalize_case,
        remove_patterns=remove_patterns
    )
    lines2 = process_lines(
        lines2, strip_lines=strip_lines, remove_whitespace=remove_whitespace,
        remove_empty_lines=remove_empty_lines, normalize_case=normalize_case,
        remove_patterns=remove_patterns
    )
    if remove_duplicates:
        # Do simple set-based comparison:
        lines1 = set(lines1)
        lines2 = set(lines2)

        added = lines2 - lines1
        removed = lines1 - lines2

        if sort_output == "alphabetically":
            added = sorted(added)
            removed = sorted(removed)

        print("\nThe following lines have been added:")
        for line in added:
            cprint(f"+ {line}", "green")

        print("\nThe following lines have been removed:")
        for line in removed:
            cprint(f"- {line}", "red")

    else:
        # Do more advanced Counter-based comparison:
        lines1_counter = Counter(lines1)
        lines2_counter = Counter(lines2)

        added = (lines2_counter - lines1_counter).items()
        removed = (lines1_counter - lines2_counter).items()

        if sort_output == "alphabetically":
            added = sorted(added, key=lambda line, n: line)
            removed = sorted(removed, key=lambda line, n: line)
        else:
            added = sorted(added, key=lambda line, n: lines2_linenumbers[line])
            removed = sorted(removed, key=lambda line, n: lines1_linenumbers[line])

        print("\nThe following lines have been added:\n")
        for line, n in added:
            cprint(f"+{n} {line}", "green")

        print("\nThe following lines have been removed:\n")
        for line, n in removed:
            cprint(f"-{n} {line}", "red")

    return added, removed


@click.command(name="oil-diff: Order-independent file comparison CLI")
@click.argument("file1", type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.argument("file2", type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option("--strip-lines/--no-strip-lines")
@click.option("--remove-whitespace/--no-remove-whitespace")
@click.option("--remove-empty-lines/--no-remove-empty-lines")
@click.option("--normalize-case/--no-normalize-case")
@click.option("--remove-duplicates/--no-remove-duplicates")
# To change the "dest" variable name, just add "dest" to the param_decls list:
@click.option("--remove-patterns", "remove_patterns", multiple=True)
@click.option("--sort-output", default=None)
@click.version_option(version="0.1.0")
def order_independent_line_diff_cli(
        file1, file2,
        strip_lines: bool = True,
        remove_whitespace: bool = True,
        remove_empty_lines: bool = True,
        normalize_case: bool = True,
        remove_patterns=None,
        # Whether to reduce the list of lines/sequences to a set:
        remove_duplicates: bool = True,
        #
        sort_output=None,
):

    lines1, lines2 = [open(fn).readlines() for fn in (file1, file2)]
    order_independent_line_comparison(
        lines1, lines2,
        strip_lines=strip_lines,
        remove_whitespace=remove_whitespace,
        remove_empty_lines=remove_empty_lines,
        normalize_case=normalize_case,
        remove_patterns=remove_patterns,
        remove_duplicates=remove_duplicates,
        sort_output=sort_output,
    )



