# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

CLI tools for hashing oligo set files (describing a pool of oligonucleotides).


The tools found in this module is an expanded power-version of the sequencesethash CLI and provides:

* Option to calculate line-hashes both including and excluding sequence modifications.
* Option to rename the input files, adding a truncated hash to the filename.


Reminder: To create an order-independent hash of a collection of elements,
simply hash each element individually, then sum all the hashes together.



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
import autoclick

from rsenv.utils.click_cmd_utils import create_click_cli_command


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
        modifications_pattern=r"\/[^\/]*?\/",
        # These only apply to the sequence:
        normalize_seq_to_uppercase: bool = False,
        remove_all_sequence_chars_except="ATGCU",
        # Whether to reduce the list of lines/sequences to a set:
        remove_duplicates: bool = True,
        hash_modulus: int = 2**256,
        show_statistics: bool = True,
        rename_file: bool = False,
        assumed_ext: str = ".oligoset.txt",
        hash_truncate_lenght: int = 8,
):
    """ Calculate order-independent hashes of oligo sequences in one or more text files.

    This is typically used to calculate hashes of `*.oligoset.txt` files,
    with and without sequence modifications.

    Args:
        files: One or more files to process.
        strip_lines: Whether to remove empty space before/after each line.
        remove_whitespace: Whether to remove all whitespace characters from the line.
        remove_empty_lines:
        normalize_full_line_to_uppercase:
        modifications_pattern: Regex pattern used to find modifications in sequence.
        normalize_seq_to_uppercase:
        remove_all_sequence_chars_except: After removing modifications, remove all characters
            in the sequence, except for the ones listed here (typically "ATGC").
        remove_duplicates: Whether to remove duplicate lines.
        hash_modulus: The modulus applied to the hash after summarizing the individual line/sequence hashes.
        show_statistics: Print basic statistics for each file to stderr.
        rename_file: Rename the processed file to include line and sequence hashes.
        assumed_ext: Assume this filename extension when renaming, e.g. ".oligoset.txt".
        hash_truncate_lenght: Truncate the hashes/hexdigests to this length when renaming the file.

    Returns:
        A list of all hashes calculated.
    """

    hashes = []

    print("files:", files)

    for filename in files:
        path = Path(filename)
        with open(filename) as fp:
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

        if modifications_pattern:
            mod_regex = re.compile(modifications_pattern)
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

        if show_statistics:
            print(f"""
Oligoset hash stats for file: {path}

* Number of lines in file: {n_lines}
* Number of non-empty lines: {n_oligos}
* Number of unique lines: {n_unique_lines}  ({n_duplicate_lines} duplicate lines)
* Number of unique seqs:  {n_unique_seqs}  ({n_duplicate_seqs} duplicate seqs)
* Sha256 hash including mods: {hexdigest_incl_mods}
* Sha256 hash excluding mods: {hexdigest_excl_mods}

""", file=sys.stderr)

        if rename_file:
            if filename.endswith(assumed_ext):
                real_stem = filename.split(assumed_ext)[0]
                ext = assumed_ext
            else:
                real_stem, ext = os.path.splitext(filename)
            if hash_excl_mods == hash_incl_mods:
                new_name = f"{real_stem}.{hexdigest_incl_mods:.{hash_truncate_lenght}}{ext}"
            else:
                new_name = f"{real_stem}.{hexdigest_excl_mods:.{hash_truncate_lenght}}.{hash_incl_mods:.{hash_truncate_lenght}}{ext}"

            os.rename(filename, new_name)
            # p.rename(new_name)
            print(f"Renaming: {filename} --> {new_name}", file=sys.stderr)

        print(f"{hexdigest_incl_mods} *{filename}")

        hashes.append((hash_incl_mods, hash_excl_mods))

    return hashes


# Create click CLI:
# I don't think autoclick *varargs or a list of arguments of undefined length
# hash_oligoset_file_cli_autoclick = autoclick.command("Oligoset file hasher")(hash_oligoset_files)
hash_oligoset_file_cli_2 = create_click_cli_command(
    hash_oligoset_files,
)

@click.command("Oligoset file hasher")
@click.argument("files")
@click.option("--strip-lines/--no-strip-lines")
@click.option("--remove-whitespace/--no-remove-whitespace")
@click.option("--remove-empty-lines/--no-remove-empty-lines")
@click.option("--normalize-full-line-to-uppercase/--no-normalize-full-line-to-uppercase")
# @click.option("--strip-lines")
# @click.option("--strip-lines")
# @click.option("--strip-lines")
# @click.option("--strip-lines")
# @click.option("--strip-lines")
def hash_oligoset_file_cli(*args, **kwargs):
    return hash_oligoset_files(*args, **kwargs)

"""
        files: str,
        strip_lines: bool = True,
        remove_whitespace: bool = True,
        remove_empty_lines: bool = True,
        normalize_full_line_to_uppercase: bool = True,
        modifications_pattern=r"\/[^\/]*?\/",
        # These only apply to
        normalize_seq_to_uppercase: bool = False,
        remove_all_sequence_chars_except="ATGCU",
        # Whether to reduce the list of lines/sequences to a set:
        remove_duplicates: bool = True,
        hash_modulus: int = 2**256,
        show_statistics: bool = True,
        rename_file: bool = False,
        assumed_ext: str = ".oligoset.txt",
        hash_truncate_lenght: int = 8,
"""

hash_oligoset_file_cli = hash_oligoset_file_cli_autoclick
