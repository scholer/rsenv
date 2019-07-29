# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

Datareader for reading data for printing labels.

"""

import csv
import io
import sys


def get_clipboard_data():
    try:
        import pyperclip
        return pyperclip.paste()
    except ImportError:
        pass
    try:
        import xerox
        return xerox.paste()
    except ImportError:
        pass
    raise RuntimeError("Could not find any way to retrieve clipboard data.")


def data_from_csv_file(filename, fieldnames=None, sep=None):
    if isinstance(fieldnames, str):
        fieldnames = fieldnames.split(sep)
    with open(filename, newline="") as file:
        # "If csvfile is a file object, it should be opened with newline=''." - csv module ref.
        # The csv reader is hard-coded to recognise either '\r' or '\n' as end-of-line, and ignores lineterminator.
        reader = csv.DictReader(file, fieldnames=fieldnames, delimiter=sep)
        dictlist = list(reader)
    return dictlist


def data_from_csv_content(content, fieldnames=None, sep=None, eol_char="\n"):

    if isinstance(fieldnames, str):
        fieldnames = fieldnames.split(sep)

    if eol_char == "win":
        eol_char = "\r\n"
    elif eol_char == "unix":
        eol_char = "\n"
    elif eol_char == "auto-detect":
        eol_char = "\r\n" if "\r\n" in content else "\n"

    if eol_char:
        # csv.DictReader accepts any string-yielding generator, including a list of strings.
        file = content.split(eol_char)
    else:
        # The csv reader is hard-coded to recognise either '\r' or '\n' as end-of-line, and ignores lineterminator.
        file = io.StringIO(content)

    reader = csv.DictReader(file, fieldnames=fieldnames, delimiter=sep)
    return list(reader)


def df_data_from_csv_file(filename, fieldnames=None, sep=None):
    import pandas as pd
    if isinstance(fieldnames, str):
        fieldnames = fieldnames.split(sep)
    return pd.read_csv(filename, names=fieldnames, delimiter=sep)


def df_data_from_csv_content(content, fieldnames=None, sep=None):
    import pandas as pd
    if isinstance(fieldnames, str):
        fieldnames = fieldnames.split(sep)
    file = io.StringIO(content)
    return pd.read_csv(file, names=fieldnames, delimiter=sep)


def data_from_clipboard(fieldnames=None, sep=None):
    content = get_clipboard_data()
    return data_from_csv_content(content, fieldnames=fieldnames, sep=sep)


def df_data_from_clipboard(fieldnames=None, sep=None):
    """ Read text from clipboard and pass to read_csv. See read_csv for the full argument list. """
    import pandas as pd
    return pd.read_clipboard(sep=sep)


def data_from_stdin(fieldnames=None, sep=None):
    content = sys.stdin.read()
    return data_from_csv_content(content, fieldnames=fieldnames, sep=sep)


def data_from_args(data_args, fieldnames=None, sep="\t", format="key:value", assignment_char=None, eol_char="\n"):
    """ Parse data (dictlist) from a list of data arguments.

    Args:
        data_args:
        fieldnames:
        sep:
        format: The key=value specifier format. Either "key=value" or "key:value".
            This is just a more expressive way of specifying the assignment character,
            and is only used if `assignment_char` parameter is not given.
        assignment_char: Another way of specifying the `key=value` format. Takes precedence over `format`.
            `assignment_char` and `format` are only used if `fieldnames` is not given.
        eol_char: If data_args is a single string, split the string using this character(s).

    Returns:
        Data as a list of dicts.

    The data_arg parsing behavior changes, depending on whether fieldnames is given separately or not.
    If fieldnames are given separately, the data_args is just a "list of lines" to parse,
    basically like a normal csv file content.
    If fieldnames is not given, the format is expected to be that each value is prefixed by its fieldname,
    e.g. "field1:value1, field2:value2".

    Examples:

        data_args = ["first:Hej,Second:Der"]
        data_from_args(data_args)
        [{"first": "Hej", "Second": "Der"}]
        data_args = ["Hej,Der"]
        data_from_args(data_args, fieldnames=["first", "Second"])
        [{"first": "Hej", "Second": "Der"}]

    """

    # print("data_args:", data_args)
    # print("sep:", sep)

    if isinstance(fieldnames, str):
        fieldnames = fieldnames.split(sep)

    if isinstance(data_args, str):
        data_args = data_args.split(eol_char)

    # print("data_args:", data_args)

    if fieldnames:
        data = [dict(zip(fieldnames, line.split(sep))) for line in data_args]
    else:
        if assignment_char is None:
            if format == "key=value":
                assignment_char = "="
            else:
                assignment_char = ":"
        # for row in data_args:
        #     print("row: {row!r}")
        #     for keyvaluepair in row.split(sep):
        #         print(f"keyvaluepair: {keyvaluepair!r}")
        #         for fieldname, value in (keyvaluepair.split(assignment_char, 1),):
        #             print(f"{fieldname}={value}")
        data = [
            {
                fieldname.strip(): value
                for fieldname, value in [keyvaluepair.split(assignment_char, 1) for keyvaluepair in row.split(sep)]
            }
            for row in data_args
        ]
    return data
