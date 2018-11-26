# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

"""

You can use the following command line tools to generate the hash:

* sequencesethash - like `sha256setsum`, but converts lines (sequences) to upper case before hashing.
* sha256setsum - like `sha256sumsum`, but removes duplicate line hashes before
    calculating the final, order-independent, hash.
* sha256sumsum - calculate an order-independent hash of lines in a file (excluding EOL character).



How to generate order-independent hash:

1. Hash each element.
2. Add all hashes together using wrap-around integer arithmetic (or apply modulus).


Note: While this is my own implementation, the method is exactly what is used by existing solutions,
e.g. python and java, when an "order-independent" hash is needed, e.g. for hashing frozen sets, etc.
Other implementations use XOR instead of SUM as the order-independent (cumutative) operator
to reduce the hashes to a single hash. Addition, however, seems to be the most popular.


References:

* https://stackoverflow.com/questions/30734848/order-independent-hash-algorithm
* https://stackoverflow.com/questions/47253864/order-independent-hash-in-java


"""
import hashlib  # Use `hashlib.algorithms_available` to see available hashes.
import click
# import inspect

from rsenv.utils.cli_cmd_utils import create_click_cli_command


def sha256_digest(s):
    """ Reference function, takes a string and returns the sha256 hash digest (bytes) of that string."""
    return hashlib.sha256(s.encode('utf-8')).digest()


def sha256_hexdigest(s):
    """ Reference function, takes a string and returns the sha256 hash hexdigest (string)."""
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def sha256_int(s):
    """ Reference function, takes a string and returns the sha256 hash as integer."""
    return int.from_bytes(hashlib.sha256(s.encode('utf-8')).digest(), byteorder='big')


def sum_mod(vals, mod=2**256):
    """ Alternatively, just sum all values and then return the modulus. No need for this function. """
    total = 0
    for val in vals:
        total += val
        total %= mod
    return total


def sha256_sumsum_int(elements, mod=2 ** 256):
    """ Returns the sum of the sha256 hash of each element in `elements`."""
    hashes = [sha256_int(elem) for elem in elements]
    hash_sum = sum(hashes) % mod
    return hash_sum


def sha256_setsum_int(elements, mod=2 ** 256):
    """ Returns the sum of the set of the sha256 hash of each element in `elements`.
    This is almost the same as `sha256_sumsum_int`, except that duplicate elements are removed before calculating the sum.
    This is exactly the same as `sha256_sumsum_int(set(elements)).
    """
    hashes = set([sha256_int(elem) for elem in elements])
    hash_sum = sum(hashes) % mod
    return hash_sum


def sha256_sumsum_hexdigest(elements, mod=2**256):
    """ This is a good way to create an 'order-independent' checksum:
        First create a hash of each element, then add all hashes (as integers),
        and return the sum, as a hex-decimal string.
    Note: To get an int from a hex-decimal string, just do: `i = int(s, 16)`
    See also:
        int()
        hex()
    """
    hash_sum = sha256_sumsum_int(elements, mod)
    return f'{hash_sum:0x}'


def sha256_setsum_hexdigest(elements, mod=2**256):
    """ This version is just like `sha256_sumsum_hexdigest`,
    but it removes duplicate line hashes by creating a set, before calculating the sum.
    Returns:
        hex digest as string
    """
    hash_sum = sha256_setsum_int(elements, mod)
    return f'{hash_sum:0x}'


def sequencesethash(sequences, mod=2**256, base_filter=None, mod_regex=None, include_mods=False):
    """ Uses `sha256_setsum_int()` to generate an "oligo sequences set hash".
    We need to make sure that "AACGT" is interpreted as the same sequence as "aacgt", so this converts all sequences
    to upper-case before passing the sequences to sha256_setsum_int().
    Considerations:
    * Should we remove sequence annotations before hashing? - Probably remove.
    * Should we remove or include modifications? - These should be removed, but that requires a regex to find them.
    * Should we remove empty lines? - Yes.
    """
    sequences = [seq.strip() for seq in sequences]  # convert to upper case
    sequences = [seq.upper() for seq in sequences if seq]  # convert to upper case and remove empty lines.
    return sha256_setsum_hexdigest(sequences, mod=mod)


def read_lines_from_file(file, strip_eol=False, strip_whitespace=False, remove_empty_lines=False):
    with open(file) as fp:
        lines = fp.readlines()
    if strip_eol:
        lines = [line.strip('\n') for line in lines]
    if strip_whitespace:
        lines = [line.strip() for line in lines if line]
    if remove_empty_lines:
        lines = [line for line in lines if line]
    return lines


def file_sha256sumsum(file, strip_eol=True, strip_whitespace=False, remove_empty_lines=False):
    """ Create an "order-independent" sha256 hash of the lines in `file` (excluding EOL characters).
    """
    lines = read_lines_from_file(
        file, strip_eol=strip_eol, strip_whitespace=strip_whitespace, remove_empty_lines=remove_empty_lines)
    return sha256_sumsum_hexdigest(lines)


def file_sha256setsum(file, strip_eol=True, strip_whitespace=False, remove_empty_lines=False):
    """ Create an "order-independent" sha256 hash of the lines in `file` (excluding EOL characters).
    This `setsum` version removes duplicate lines (line hashes) before calculating the order-independent hash.
    """
    lines = read_lines_from_file(
        file, strip_eol=strip_eol, strip_whitespace=strip_whitespace, remove_empty_lines=remove_empty_lines)
    return sha256_setsum_hexdigest(lines)


def file_sequencesethash(file, strip_eol=True, strip_whitespace=True, remove_empty_lines=True):
    """ Create an "order-independent" sha256 hash of the lines in `file` (excluding EOL characters).
    This `setsum` version removes duplicate lines (line hashes) before calculating the order-independent hash.
    """
    lines = read_lines_from_file(
        file, strip_eol=strip_eol, strip_whitespace=strip_whitespace, remove_empty_lines=remove_empty_lines)
    return sequencesethash(lines)


@click.command()
@click.option('--strip-eol', default=True)
@click.option('--strip-whitespace', default=False)
@click.option('--remove-empty-lines', default=False)
@click.argument('files', nargs=-1)
def file_sha256sumsum_cli(files, strip_eol=True, strip_whitespace=True, remove_empty_lines=True):
    for file in files:
        hex_digest =  file_sha256sumsum(
            file, strip_eol=strip_eol, strip_whitespace=strip_whitespace, remove_empty_lines=remove_empty_lines)
        print(f"{hex_digest} *{file}")


@click.command()
@click.option('--strip-eol', default=True)
@click.option('--strip-whitespace', default=False)
@click.option('--remove-empty-lines', default=False)
@click.argument('files', nargs=-1)
def file_sha256setsum_cli(files, strip_eol=True, strip_whitespace=True, remove_empty_lines=True):
    for file in files:
        hex_digest =  file_sha256setsum(
            file, strip_eol=strip_eol, strip_whitespace=strip_whitespace, remove_empty_lines=remove_empty_lines)
        print(f"{hex_digest} *{file}")


@click.command()
@click.option('--strip-eol', default=True)
@click.option('--strip-whitespace', default=True)
@click.option('--remove-empty-lines', default=True)
@click.argument('files', nargs=-1)
def file_sequencesethash_cli(files, strip_eol=True, strip_whitespace=True, remove_empty_lines=True):
    for file in files:
        hex_digest =  file_sequencesethash(
            file, strip_eol=strip_eol, strip_whitespace=strip_whitespace, remove_empty_lines=remove_empty_lines)
        print(f"{hex_digest} *{file}")

# Click CLI Commands:
# file_sha256sumsum_cli = create_click_cli_command(file_sha256sumsum)
# file_sha256setsum_cli = create_click_cli_command(file_sha256setsum)
