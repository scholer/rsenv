"""


This is a simplified, modernized (python 3.6+) version of the old oligomanager om_automapper script.

This version is:
* Functional, where the old was object-oriented.
* Uses click, where the old used argparser.


See also:
* oligomanager/tools/file_transformation/sequencemapper.py
* oligomanager/tools/file_transformation/modulecolormapper.py
* oligomanager/tools/file_transformation/om_automapper.py



"""


import os
import re
import sys
from itertools import chain, zip_longest
import pandas as pd
import click


DEFAULT_FN_SEARCHPATS = {
    "seqmap": ["{filename_no_ext}.seqmap.txt", "seqmap.txt"],
    "colormap": ["{filename_no_ext}.colormap.txt", "colormap.txt"]
}
OLIGO_MOD_REGEX = "\[.*?\]"
OLIGO_MOD_REGEXC = re.compile(OLIGO_MOD_REGEX)


@click.command()
@click.argument("cadnano_csv_filename", type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option("--colormap-filename")
@click.option("--seqmap-filename")
@click.option("--show-used-seq-keys/--no-show-used-seq-keys", default=False)
@click.option("--recalculate-length/--no-recalculate-length", default=True)
@click.option("--parse-helixbaseidx/--no-parse-helixbaseidx", default=False)
@click.option("--sort")
@click.option("--sort-ascending/--no-sort-ascending", default=True)
@click.option("--sort-default/--no-sort-default", default=False)
@click.option("--output-filename")
@click.option("--use-default-output-filename/--no-use-default-output-filename", default=False)
@click.option("--out-sep", default="\t")
@click.option("--out-cols", default=None)
def cadnano_maptransformer_cli(
        cadnano_csv_filename,
        colormap_filename=None,
        seqmap_filename=None,
        output_filename=None,
        use_default_output_filename=False,
        out_sep='\t',
        out_cols=None,
        color_col='Color',
        color_name_col='Pool-name',
        seq_col='Sequence',
        seq_col_out=None,
        undefined_symbol=r'\?',
        seq_parts_join_str='',
        show_used_seq_keys=False,
        sort=None,
        sort_ascending=True,
        sort_default=False,
        parse_helixbaseidx=False,
        mapfile_sep=None,
        recalculate_length=True,
):
    """ Cadnano CSV export file, map transformer CLI.

    Example usage:
        First, make sure you have both colormap and sequence map files in the directory next to the csv export file:
        $ ls
            maptransformer cadnano_export.csv
            seqmap.txt
            colormap.txt
        Then invoke cadnano_maptransformer to read csv exported file, perform substitutions and mappings, and write
        output to stdout or file (defined with -o option).
        $ cadnano_maptransformer cadnano_export.csv > cadnano_export.mapped.csv

    Args:
        cadnano_csv_filename:
        colormap_filename:
        seqmap_filename:
        output_filename:
        out_sep:
        color_col:
        color_name_col:
        seq_col:
        seq_col_out:
        undefined_symbol:
        seq_parts_join_str:
        show_used_seq_keys: Print the sequence keys that was used for mapping to stderr.
        sort:
        sort_ascending:
        sort_default:

    Returns:

    """
    filename_no_ext, ext = os.path.splitext(cadnano_csv_filename)
    fmtpars = {
        'dirname': os.path.dirname(cadnano_csv_filename),
        'filename_no_ext': filename_no_ext,
        'ext': ext,
    }
    if use_default_output_filename and output_filename is None:
        output_filename = "{filename_no_ext}.mapped.csv"
    if colormap_filename is None:
        colormap_filename = locate_file("colormap", fmtpars=fmtpars)
    if seqmap_filename is None:
        seqmap_filename = locate_file("seqmap", fmtpars=fmtpars)

    df = pd.read_csv(cadnano_csv_filename)

    if seqmap_filename:
        print(f"Using {seqmap_filename!r} to perform sequence mapping...", file=sys.stderr)
        seqmap = read_map_file(seqmap_filename, sep=mapfile_sep)
        # seqmap keys are ints, so convert:
        seqmap = {int(k): v for k, v in seqmap.items()}
        used_seq_keys = set()
        df_substitute_undefined_seq_spans(
            df, seqmap=seqmap,
            undef_char=undefined_symbol,
            input_col=seq_col,
            output_col=seq_col_out,
            joinstr=seq_parts_join_str,
            used_keys=used_seq_keys,
        )
        if show_used_seq_keys:
            print("Used sequence keys: (lengths of undefined sequence)")
            # print(used_seq_keys)
            print(",".join(f"  {k:2}" for k in sorted(used_seq_keys)))

    if colormap_filename:
        print(f"Using {colormap_filename!r} to perform color-name mapping...", file=sys.stderr)
        # Colors use '#', so disable comment removal (or use a different character).
        colormap = read_map_file(colormap_filename, comment_symbol='', sep=mapfile_sep)
        df[color_name_col] = [colormap[color] for color in df[color_col]]

    if parse_helixbaseidx:
        hb_regexc = re.compile(r'(\d+)\[(\d+)\]')
        for k in 'Start', 'End':
            # Make sure to convert to int for proper sorting:
            df[k+'_helix_idx'], df[k+'_base_idx'] = zip(*[
                [int(v) for v in hb_regexc.match(hb).groups()] for hb in df[k]
            ])

    if recalculate_length:
        df_recalculate_length(df, length_col="Length", seq_col=seq_col)

    if sort_default:
        sort = [color_name_col, 'Start']

    # Regarding sorting a DataFrame "naturally", i.e. 2[100] comes before 10[100]:
    # https://stackoverflow.com/questions/29580978/naturally-sorting-pandas-dataframe
    # Using natsort:
    #   >>> df.reindex(index=order_by_index(df.index, index_natsorted(zip(df.b, df.a))))
    # The Pandas devs recommend using proper Pandas 'Categorical' objects, but that seems really tedious.
    # Pandas doesn't currently accept a 'key' function when sorting, but there is an open FR for this:
    # https://github.com/pandas-dev/pandas/issues/3942
    # Best solution for now is to enable parse-helixbaseidx but limit the output columns:
    #   $ `--parse-helixbaseidx --sort Start_helix_idx,Start_base_idx` --out-cols "Start,Sequence,Pool-name"

    if sort:
        if isinstance(sort, str):
            sort = [s.strip() for s in sort.split(",")]
        sort_specifiers = list(zip_longest(*[s.split(':') for s in sort], fillvalue=""))
        sort_by = list(sort_specifiers[0])
        if len(sort_specifiers) > 1:
            # one or more sorting specifiers include colon, e.g. "Color:d" (for descending order).
            print(" - sort_specifiers[1]:", sort_specifiers[1])
            sort_ascending = [not (val == 'r' or val == 'd') and (val == 'a' or bool(sort_ascending))
                              for val in sort_specifiers[1]]
            print(" - ascending:", sort_ascending, file=sys.stderr)
        print(f"Sorting by: {sort_by} (ascending: {sort_ascending})", sort_by, file=sys.stderr)
        df = df.sort_values(by=sort_by, ascending=sort_ascending)

    if isinstance(out_cols, str):
        out_cols = [col.strip() for col in out_cols.split(",")]

    if output_filename:
        # fout = open(output_filename, 'w')
        output_filename = output_filename.format(**fmtpars)
        with open(output_filename, 'w') as fout:
            df.to_csv(fout, sep=out_sep, index=False, columns=out_cols)
    else:
        fout = sys.stdout
        df.to_csv(fout, sep=out_sep, index=False, columns=out_cols)


def locate_file(key, fmtpars):
    for cand in DEFAULT_FN_SEARCHPATS[key]:
        cand = cand.format(**fmtpars)
        if os.path.isfile(cand):
            return cand
    else:
        print(f"Notice: Could not find any {key!r} files.", file=sys.stderr)


def read_map_file(
        filename,
        strip_lines=True,
        remove_empty_lins=True,
        remove_comment_lines=True,
        remove_trailing_comments=False,
        comment_symbol="#",
        sep=None,
):
    fmap = None
    with open(filename) as fd:
        lines = fd
        if strip_lines:
            # print("Stripping lines...", file=sys.stderr)
            lines = (line.strip() for line in fd)
        if remove_empty_lins:
            # print("Removing empty lines...", file=sys.stderr)
            lines = (line for line in lines if line.strip())
        if comment_symbol and remove_comment_lines:
            # print("Removing comment lines...", file=sys.stderr)
            lines = (line for line in lines if not line.startswith(comment_symbol))
        if comment_symbol and remove_trailing_comments:
            # print("Removing trailing comments...", file=sys.stderr)
            lines = (line.split(comment_symbol)[0] for line in lines)
        lines = list(lines)
        # print("Mapfile rows:", file=sys.stderr)
        # print("\n".join(repr(v) for v in lines), file=sys.stderr)
        lines = (line.split(sep=sep) for line in lines)
        try:
            fmap = {row[0]: row[1] for row in lines}
        except IndexError as exc:
            print(f"Error reading {filename}, in the line just above/before the following:", file=sys.stderr)
            print(fd.read(128), file=sys.stderr)
            raise exc
    return fmap


def df_substitute_undefined_seq_spans(
        df, seqmap=None, undef_char=r'\?', joinstr="", input_col='Sequence', output_col=None, used_keys=None,
):
    """

    Args:
        df:
        seqmap:
        undef_char:
        joinstr:
        input_col:
        output_col:
        used_keys:

    Returns:

    """

    if output_col is None:
        output_col = input_col

    if seqmap is None:
        print("Notice: Using default seqmap, mapping undefined sequence spans to spans of 'T' with same length.",
              file=sys.stderr)
        seqmap = {i: 'T' * i for i in range(100)}

    seqmap[0] = ''  # We need a zero-length entry because of the implementation where we use re.split()

    if used_keys is None:
        used_keys = set()

    regex_pat = f"({undef_char}+)"  # Use capturing group.
    regexc = re.compile(regex_pat)

    def substitute_undefined(seq):
        splitted = regexc.split(seq)
        # print("splitted:", splitted, file=sys.stderr)
        # Returns interweaved non-matching and matching parts.
        # To split:
        # it = iter(range(10)
        # even, odd = zip(*zip(it, it))
        # first zip makes a list of 2-tuples [(0, 1), ...], next zip combines even and odds.
        # print(even, odd, sep="\n")
        split_iter = iter(splitted)
        defined, undefined = zip(*zip_longest(split_iter, split_iter, fillvalue=''))
        used_keys.update({len(span) for span in undefined})
        # print("used_keys after update:", used_keys)
        try:
            mapped_vals = [seqmap[len(span)] for span in undefined]
        except KeyError as exc:
            print(f"\n\nERROR: {exc} not specified in the sequence map.\n\n")
            raise exc
        new_seq = joinstr.join(chain(*zip(defined, mapped_vals)))
        # print(f"{seq} --> {new_seq}", file=sys.stderr)
        return new_seq

    df[output_col] = df[input_col].map(substitute_undefined)
    # print("used_keys after map:", used_keys)


def df_recalculate_length(df, length_col="Length", seq_col="Sequence"):
    df[length_col] = df[seq_col].map(get_oligo_nbases)


def get_oligo_nbases(sequence, mod_regex=OLIGO_MOD_REGEXC):
    return len(get_oligo_raw_sequence(sequence=sequence, mod_regex=mod_regex))


def get_oligo_raw_sequence(sequence, mod_regex=OLIGO_MOD_REGEXC, sub_str=""):
    """ Return raw oligo sequence without modifications.
    Mostly just a reference function for how to invoke re.sub(pat, repl, strng).

    Args:
        sequence: Oligo sequence (str).
        mod_regex: A regex pattern matching the modifications (str or compiled regex).
        sub_str: Replace mod pattern matches with this string (str).

    Returns:
        Sequence with substitutions.

    Modifications patterns:
        "\[[^\]]*\]"     # Greedy, matching anything except closing bracket before closing bracket.
        "\[.*?\]"        # Lazy matching anything within brackets.
    """
    if isinstance(mod_regex, str):
        mod_regex = re.compile(mod_regex)
    # re.sub(X, Y, Z)  # "replace X with Y in the string Z"
    # pat.sub(Y, Z)    # "replace matches with Y in the string Z
    raw = mod_regex.sub(sub_str, sequence)
    # print(f"{sequence} --> {raw}")
    return raw


if __name__ == '__main__':
    cadnano_maptransformer_cli()
