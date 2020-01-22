# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module to hash a cadnano file.

Unfortunately, cadnano saves a timestamp with the current time whenever it saves a file.
That makes it impossible to use traditional file hashes to determine if a cadnano design json file
has actually changed.

The CLI in this module creates two hashes, one for (scaffold and staple routing), which
determines how the design will physically appear in the real world,
and another which includes staple strand coloring.

The structure of a cadnano json file:

{
  name: str
  vstrands: [
    {
      'row': int, row index in the helix grid.
      'col': int, col index in the helix grid.
      'num': int, helix number, used for ordering helices in the pathview.
      'stap': list, staple strands routing.
      'scaf': list, scaffold routing.
      'loop': Add extra bases to the scaffold (relative to the fixed lattice).
      'skip': Remove bases from the scaffold (relative to the fixed lattice).
      'stapLoop': list, staple strand loops.
      'scafLoop': scaffold loops.
      'stap_colors': a list of (base_idx, color_number)
    }
  ]
}


Parsing the color_number value to RGB values:
---------------------------------------------

The color is written as a single 24-bit integer, where the left-most 8 bit is the red color,
the middle 8 bits the green color, and the right-most 8 bit indicates the blue color.

We can use the `>>` and `&` operators to split out the bits we want:

    r, g, b = (color_number>>16) & 0xFF, (color_number>>8) & 0xFF, color_number & 0xFF

The `>>` operator shifts the bits of a value (written in binary) to the right by a certain number of places.
So, `x >> returns the value with the bits shifted to the right by y places.
This is the same as //'ing x by 2**y.

The `& 0xFF` is used to select the right-most 8 bit after shifting the bits by 16, 8, or 0 places.
0xFF written in binary, f"{0xff:b}", is obviously 11111111

Together, `>>` and `&` works a bit like making a slice (except that the >> is counted from the left,
and & is used to indicate the size of the slice.

A color_number of 16225054 written in binary (using f"{16225054:b}"):

    111101111001001100011110

    111101111001001100011110 >> 8  -->
    1111011110010011

    1111011110010011 & 11111111  -->
            10010011

So, `(16225054>>16)&0xFF` is 0b10010011 (binary) or 0x93 (hex), or 147.

OBS: These can be copy/pasted as binary and the result printed as binary using:
f"{0b1111011110010011 & 0b11111111:b}"

To write an integer as hex, just use the ':x' format specifier:

    r_hex_str = f"{r:x}"

To write the traditional #RRGGBB hex string, make sure each value is zero-padded:

    rgb_str = f"#{r:02x}{g:02x}{b:02x}"


Data diff'ing alternatives:
---------------------------

Hashes only shows whether something has changed or not.
If you need to show the actual differences, here are some options:

* Basic file `diff` - this doesn't work well for cadnano json files.
* You can use one of the "structured data recursive diff'ing" tools:
    * The `datadiff` package for showing actual differences between lists and diffs.
    * The `json_diff` package CLI can be used to show changes to json files.
        However, the output is not very useful for comparing cadnano json files.





Hashing procedure:
------------------

Python's hash() function is not persistent between runs - in fact, it is designed to
change between runs for security purposes.

Is there any existing packages to hash general python data structures?


* Hash-things:
    * https://pypi.org/project/hash-things/
    * https://github.com/phalt/hash_things
    * > What can I hash?
      > Dictionaries with any value - Lists, Tuples, Sets, and even nested Dicts!
    * Uses Python's built-in `hash()` function.

* dict-hash:
    * https://pypi.org/project/dict-hash/
    * Uses `json.dumps()` to dump the data after converting values to strings, recursively,
      then hashes the bytes from the utf8-encoded json string.
    * I believe `json.dumps()` sorts the keys, so it shouldn't matter too much
      that we are not using order-independent hashing here.
      However, I'm not sure it is guaranteed that the output of `json.dumps()`
      is persistent and doesn't change between versions.
    * Uses `hashlib.sha256()` for hashing (good).


Other hashing libraries that may be relevant and/or just interesting?

* perfect-hash
* visual-hash
* hash-dict:
    * https://pypi.org/project/hash-dict/
    * https://github.com/Cologler/hash-dict-python
    * I think this is a re-implementation of a Python Dict / HashMap,
      providing things like case-insensitive keying, etc.
*

"""

import json
import hashlib
from pathlib import Path
from functools import partial
from datetime import datetime
from typing import Iterable, Mapping, List, Tuple
import click
import typer


hashable_types = {
    list,
    set,
    tuple,
    str,
    int,
    float,
    bytes,
}


def lists_and_dicts_to_tuples_recursively(obj):
    """ Convert all lists to tuples and all dicts to tuples of (k, v) pairs.
    OBS: This is a one-way conversion and indistinguishable from a nested-tuples
    data-structure to begin with.
    """
    if isinstance(obj, list):
        return tuple(lists_and_dicts_to_tuples_recursively(v) for v in obj)
    elif isinstance(obj, dict):
        return tuple((k, lists_and_dicts_to_tuples_recursively(v)) for k, v in obj.items())
    else:
        return obj


def recursive_hashing(m, obj):
    """

    Args:
        m:
        obj:

    Returns:

    Discussion: How to distinguish types?
    * I guess I could just add that as a tuple, so:
        1 --> ('int', 1)
    * While if the input was `('int', 1)`, the output would be
        ('int', 1)  -->  (('str', 'int'), ('int', 1)).
    """

    hash_bits = m.digest_size * 8
    hash_modulus = 2**hash_bits

    if isinstance(obj, str):
        m.update(obj.encode('utf8'))
    elif isinstance(obj, (int, float)):
        # Should 1 (int) hash to the same as '1' (str) ?
        # Or should we use int.to_bytes(n_bytes, byteorder) to convert to bytes?
        # You can use n_bytes = (int.bit_length() // 8) + 1 to get the number of bytes required.
        # But what about float?
        m.update(str(obj).encode('utf8'))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            recursive_hashing(m, v)
    elif isinstance(obj, set):
        # Order-independent hashing:
        # Or alternatively, just sort before hashing - is effectively order-independent.
        # But what if we cannot sort the elements? Nah, we can always do that.
        set_hash_int = 0
        for elem in obj:
            elem_hash_dig = recursive_hashing(hashlib.new(m.name), elem)
            elem_hash_int = int.from_bytes(elem_hash_dig, byteorder='big')
            set_hash_int = (set_hash_int + elem_hash_int) % hash_modulus
        set_hash_dig = int.to_bytes(set_hash_int, m.digest_size, byteorder='big')
        m.update(set_hash_dig)
    elif isinstance(obj, dict):
        # A dict is a set of (key, value) tuples:
        recursive_hashing(set(obj.items()))
    else:
        raise TypeError(f"Unrecognized type {type(obj)} for object {obj!r}.")

    return m.digest()
    # return int.from_bytes(m.digest(), byteorder='big')


def str_hash_hexdigest(s, hash_name="sha256"):
    """ Hash a given string, encoding it to bytes as utf-8, and return hexdigest. """
    m = hashlib.new(hash_name)
    m.update(s.encode("utf8"))
    hexdigest = m.hexdigest()
    return hexdigest


def json_hash_hexdigets(obj, hash_name="sha256"):
    """ Use json to serialize obj, then hash the serialized string. """
    # Does json.dump sort the data (to make the order of sets and dicts order-independent)?
    json_str = json.dumps(obj)
    return str_hash_hexdigest(json_str)


def cadnano_json_vstrands_hashes(
        jsonfile,
        # design_variant_keys=('row', 'loop', 'col', 'scafLoop', 'stap', 'scaf', 'num', 'skip', 'stapLoop'),
        # coloring_keys=('row', 'loop', 'col', 'scafLoop', 'stap', 'scaf', 'num', 'stap_colors', 'skip', 'stapLoop'),
        del_color_keys: List[str] = None,  # Use typing.List to support multi-arg input.
        hash_name: str = "sha256",
        # hash_without_colors: bool = True,
        # hash_with_colors: bool = True,
        save_hashes_to_file: bool = True,
):
    """

    cadnano-json-vstrands-hashes

    Args:
        jsonfile: The cadnano json file to hash ("legacy" cadnano json file format).
        del_color_keys: The keys to remove when creating the "hash without color".
        hash_name: The hashing algorithm to use when hashing.
        save_hashes_to_file: Automatically save the calculated hashes to a file next to the jsonfile.

    Removed args:
        hash_without_colors: Create hash without staple color info.
        hash_with_colors: Create hash with staple color info.

    Returns:
        tuple with (hash_with_colors, hash_without_colors)

    """
    # defaults:
    if hash_name is None:
        hash_name = "sha256"

    jsonstr = open(jsonfile).read()
    hexdigest_full_file = str_hash_hexdigest(jsonstr)
    jsondata = json.loads(jsonstr)
    vstrands = jsondata['vstrands']
    jsonpath = Path(jsonfile)

    # # Does json.dump sort the data?
    # json_str_with_colors = json.dumps(obj)
    # m_with_colors = hashlib.new(hash_name)
    # m_with_colors.update(json_str_with_colors.encode("utf8"))
    # hexdigets_with_colors = m_with_colors.hexdigets()

    hexdigets_with_colors = json_hash_hexdigets(vstrands, hash_name)

    # pop 'stap_colors' from all vstrands and repeat:
    for vh in vstrands:
        if not del_color_keys:
            del vh['stap_colors']
            vh.pop('scaf_colors', None)  # cadnano2.5 supports coloring the scaffold.
        else:
            for k in del_color_keys:
                del vh[k]

    hexdigets_no_colors = json_hash_hexdigets(vstrands, hash_name)

    date = datetime.now()

    # The output that we save to file does not have to include the full path,
    # since it is saved to a file next to the jsonfile:
    output = f"""
{date:%Y/%m/%d %H:%M:%S} > cadnano-json-vstrands-hashes --hash-name {hash_name} "{jsonpath.name}"
 * hexdigest vstrands without staple colors:    {hexdigets_no_colors}
 * hexdigest vstrands  with   staple colors:    {hexdigets_with_colors}
 * hexdigest full file contents:                {hexdigest_full_file}
"""

    print(output)
    # When printing, we should include the full path to jsonfile:
    # print("\ncadnano-json-vstrands-hashes for file:", jsonfile)
    # print(" * hexdigest without staple colors:   ", hexdigets_no_colors)
    # print(" * hexdigest with staple colors:      ", hexdigets_with_colors)

    if save_hashes_to_file:
        hash_filename = Path(jsonfile).with_suffix(f".{hash_name}-vstrands-hashes.txt")
        hash_filename.write_text(output)

    return hexdigets_with_colors, hexdigets_no_colors


# Create a traditional click CLI:
@click.command("Cadnano JSON['vstrands'] hashing CLI (Click implementation)")
@click.argument("jsonfile")
@click.option(
    "--del-color-keys", "--del-color-key", "-k",
    multiple=True  # click Options cannot have nargs=-1. Use multiple instead.
)
@click.option("--hash-name", default="sha256")
@click.option("--save-hashes-to-file/--no-save-hashes-to-file", default=True)
def cadnano_json_vstrands_hashes_click_cli(*args, **kwargs):
    # click passes all parameters as keyword arguments:
    # print("args:", args)  # Empty tuple
    # print("kwargs:", kwargs)  # Has all click args and options.
    cadnano_json_vstrands_hashes(*args, **kwargs)


# Create Typer click CLI:
def cadnano_json_vstrands_hashes_typer_cli():
    typer.run(cadnano_json_vstrands_hashes)
    # typer.run(function) is equivalent to:
    # app = Typer()
    # app.command()(function)
    # app()


cadnano_json_vstrands_hashes_typer_cli_2 = partial(typer.run, cadnano_json_vstrands_hashes)

# Select the CLI implementation to use:
cadnano_json_vstrands_hashes_cli = cadnano_json_vstrands_hashes_typer_cli
# cadnano_json_vstrands_hashes_cli = cadnano_json_vstrands_hashes_click_cli
