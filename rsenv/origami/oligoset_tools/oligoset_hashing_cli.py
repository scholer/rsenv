# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

CLI tools for hashing oligo set files (describing a pool of oligonucleotides).


The tools found in this module is an expanded power-version of the sequencesethash CLI and provides:

* Option to calculate line-hashes both including and excluding sequence modifications.
* Option to rename the input files, adding a truncated hash to the filename.


Reminder: To create an order-independent hash of a collection of elements,
simply hash each element individually, then sum all the hashes together.


Generating oligoset hashes is the second step in the "oligoset registration" pipeline, which is as follows:

1. Generate `.oligoset.txt` file from Cadnano exported CSV using `extract-oligoset-from-cadnano-csv` CLI.
    * You can generate both a "Complete origami" pool (name should be title-cased),
      and/or pools for individual staple pools/modules.
2. Generate oligoset hash and add this to filename(s) using `oligoset-file-hasher-cli`.
3. Move the renamed ` (hash).oligoset.txt` file(s) to the central `Oligo-pools-registry` folder.




See also:

* rsenv.utils.hash_utils module for generic hashing utilities, including:
    * sha256sumsum - calculate an order-independent hash of lines in a file (excluding EOL character).
    * sha256setsum - like `sha256sumsum`, but removes duplicate line hashes before
        calculating the final, order-independent, hash.
    * sequencesethash - like `sha256setsum`, but converts lines (sequences) to upper case before hashing.



"""

import sys
import os.path
import re
import hashlib
from pathlib import Path

import click

from rsenv.cliutils import click_stove


def sha256_int(s):
    """ Reference function, takes a string and returns the sha256 hash as integer."""
    return int.from_bytes(hashlib.sha256(s.encode('utf-8')).digest(), byteorder='big')


def hexdigest(hash_int: int) -> str:
    return f'{hash_int:0x}'


def hash_oligoset_files(
        files: str,
        strip_lines: bool = True,
        remove_whitespace: bool = True,
        remove_empty_lines: bool = True,
        normalize_full_line_to_uppercase: bool = True,
        mod_regex=r"\/[^\/]*?\/",
        # These only apply to the sequence:
        normalize_seq_to_uppercase: bool = False,
        remove_all_sequence_chars_except="ATGCU",
        # Whether to reduce the list of lines/sequences to a set:
        remove_duplicates: bool = True,
        hash_modulus: int = 2**256,
        show_stats: bool = True,
        rename_file: bool = False,
        assumed_ext: str = ".oligoset.txt",
        rename_pattern = "{output_dir}/{fn_no_ext} ({hashes_str}).oligoset.txt",
        output_dir = ".",
        hash_str_sep: str = " ",
        hash_truncate_lenght: int = 8,
        return_digests: bool = False,
):
    """ Calculate order-independent hashes of oligo sequences in one or more text files.

    This is typically used to calculate hashes of `*.oligoset.txt` files,
    with and without sequence modifications.

    Args:
        files: One or more files to process.
        strip_lines: Whether to remove empty space before/after each line.
        remove_whitespace: Whether to remove all whitespace characters from the line.
        remove_empty_lines: Remove all empty lines from file.
        normalize_full_line_to_uppercase: Normalize full-line to upper-case before hashing.
            (Applies to both `seqhash` AND `modhash`).
        mod_regex: Regex pattern used to find modifications in sequence.
        normalize_seq_to_uppercase: Normalize sequence to upper-case before hashing.
            (Applies only to `seqhash`, not `modhash`).
        remove_all_sequence_chars_except: After removing modifications, remove all characters
            in the sequence, except for the ones listed here (typically "ATGC").
        remove_duplicates: Whether to remove duplicate lines.
        hash_modulus: The modulus applied to the hash after summarizing the individual line/sequence hashes.
        show_stats: Print basic statistics for each file to stderr.
        rename_file: Rename the processed file to include line and sequence hashes.
        assumed_ext: Assume this filename extension when renaming, e.g. ".oligoset.txt".
        hash_truncate_lenght: Truncate the hashes/hexdigests to this length when renaming the file.
        return_digests: If True, return hashes as hexdigest strings, instead of integer numbers.

    Returns:
        A list of all hashes calculated.
    """

    hashes = []

    print("files:", files)

    for fpath_str in files:
        fpath = Path(fpath_str)
        with open(fpath_str) as fp:
            lines = [line for line in fp]
        n_lines = len(lines)
        if strip_lines:
            lines = [line.strip() for line in lines]
        if remove_empty_lines:
            lines = [line for line in lines if line.strip()]
        if remove_whitespace:
            lines = [line.replace(" ", "").replace("\t", "") for line in lines]

        n_oligos = len(lines)

        if normalize_full_line_to_uppercase:
            lines = [line.upper() for line in lines]

        if mod_regex:
            if isinstance(mod_regex, str):
                mod_regex = re.compile(mod_regex)
            lines_excl_mods = ["".join(mod_regex.split(line)) for line in lines]
        else:
            lines_excl_mods = lines

        if normalize_seq_to_uppercase:
            lines_excl_mods = [line.upper() for line in lines]

        line_hashes = [sha256_int(line) for line in lines]
        line_hashes_excl_mods = [sha256_int(line) for line in lines_excl_mods]

        if remove_duplicates:
            line_hashes = set(line_hashes)
            line_hashes_excl_mods = set(line_hashes_excl_mods)
            n_unique_lines = len(line_hashes)
            n_unique_seqs = len(lines_excl_mods)
        else:
            n_unique_lines = len(set(line_hashes))
            n_unique_seqs = len(set(line_hashes_excl_mods))

        n_duplicate_lines = n_oligos - n_unique_lines
        n_duplicate_seqs = n_oligos - n_unique_seqs

        hash_incl_mods = sum(line_hashes) % hash_modulus
        hash_excl_mods = sum(line_hashes_excl_mods) % hash_modulus

        hexdigest_incl_mods = f'{hash_incl_mods:0x}'
        hexdigest_excl_mods = f'{hash_excl_mods:0x}'

        if show_stats:
            print(f"""
Oligoset hash stats for file: {fpath}

* Number of lines in file: {n_lines}
* Number of non-empty lines: {n_oligos}
* Number of unique lines: {n_unique_lines}  ({n_duplicate_lines} duplicate lines)
* Number of unique seqs:  {n_unique_seqs}  ({n_duplicate_seqs} duplicate seqs)
* Sha256 hash including mods: {hexdigest_incl_mods}
* Sha256 hash excluding mods: {hexdigest_excl_mods}

""", file=sys.stderr)

        if rename_file:
            # `fpath_str` is the input (str), `fpath` is the Path object.
            if output_dir is None:
                output_dir = fpath.parent
            fn_with_ext = fpath.name

            if str(fn_with_ext).endswith(assumed_ext):
                fn_no_ext = str(fn_with_ext).split(assumed_ext)[0]
                ext = assumed_ext
            else:
                real_stem, ext = os.path.splitext(fn_with_ext)
            hash_digests = [hexdigest_excl_mods]
            if hexdigest_incl_mods != hexdigest_excl_mods:
                hash_digests.append(hexdigest_incl_mods)

            # Truncate each hash (hexdigest) and join using the given `hash_str_sep` separator.
            hash_str = hash_str_sep.join(hash_digest[:hash_truncate_lenght] for hash_digest in hash_digests)

            # Format new filename:
            new_filename = rename_pattern.format(
                output_dir=output_dir, fn_no_ext=fn_no_ext, fn_with_ext=fn_with_ext,
                path=str(fpath_str), filename=fn_with_ext, ext=ext, hash_str=hash_str,
                hash_incl_mods=hash_incl_mods, hash_excl_mods=hash_excl_mods,
            )

            print(f"Renaming: {fpath_str} --> {new_filename}", file=sys.stderr)
            # fpath.rename(new_filename)
            # os.rename(fpath_str, new_filename)

        print(f"{hexdigest_incl_mods} *{fpath_str}")

        if return_digests:
            hashes.append((hexdigest_incl_mods, hexdigest_excl_mods))
        else:
            hashes.append((hash_incl_mods, hash_excl_mods))

    return hashes


# Create click CLI:
# I don't think autoclick *varargs or a list of arguments of undefined length
# hash_oligoset_file_cli_autoclick = autoclick.command("Oligoset file hasher")(hash_oligoset_files)
# hash_oligoset_file_cli = hash_oligoset_file_cli_autoclick

# Create Click CLI command using my click_stove module:
hash_oligoset_file_cli_2 = click_stove.create_click_cli_command(
    hash_oligoset_files,
)

# Manually create a Click command:
@click.command("Oligoset file hasher")
@click.argument("files")
@click.option("--strip-lines/--no-strip-lines", default=True)
@click.option("--remove-whitespace/--no-remove-whitespace", default=True)
@click.option("--remove-empty-lines/--no-remove-empty-lines", default=True)
@click.option("--normalize-full-line-to-uppercase/--no-normalize-full-line-to-uppercase", default=True)
@click.option("--mod-regex", default=r"\/[^\/]*?\/")
@click.option("--normalize-seq-to-uppercase/--no-normalize-seq-to-uppercase", default=True)
@click.option("--remove-duplicates/--no-remove-duplicates", default=True)
@click.option("--hash-modulus", type=int, default=2**256)
@click.option("--show-stats/--no-show-stats", default=True)
@click.option("--rename-file/--no-rename-file", default=False)
@click.option("--assumed-ext", default=".oligoset.txt")
@click.option("--hash-truncate-length", type=int, default=8)
def hash_oligoset_file_cli(*args, **kwargs):
    return hash_oligoset_files(*args, **kwargs)
