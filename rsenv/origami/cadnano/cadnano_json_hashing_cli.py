# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module to hash a cadnano file.

See also:

* cadnano_diff_jsondata_cli()


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
from copy import deepcopy
import sys

from rsenv.utils.hash_utils import str_hash_hexdigest
from rsenv import __version__


DEFAULT_VSTRANDS_HASH_SPECS = {
    #         # 'row', 'loop', 'col', 'scafLoop', 'stap', 'scaf', 'num', 'stap_colors', 'skip', 'stapLoop'
    "vstrands-all-attributes": {"exclude_keys": None, "order_independent": False},
    "vstrands-legacy": {
        "json_separators": None,  # Previously, we didn't use compact form.
        "exclude_keys": None,
        "order_independent": False,
    },

    "vstrands-order-independent": {"order_independent": True},
    "vstrands-num": {"include_keys": ['num'], "order_independent": False},

    "vstrands-without-colors": {
        "exclude_keys": ['stap_colors', 'scaf_colors'],
        "order_independent": False,
        "allow_missing_exclude_keys": True,
    },

    # I think this is the best way to check if a design has functionally changed:
    "vstrands-stap-scaf-loops-skips": {
        "include_keys": ['stap', 'scaf', 'loop', 'stapLoop', 'skip'],
        "order_independent": False
    },
    "vstrands-stap-scaf-loops-skips-oi": {
        "include_keys": ['stap', 'scaf', 'loop', 'stapLoop', 'skip'],
        "order_independent": True,
    },

    "vstrands-stap": {"include_keys": ['stap'], "order_independent": False},
    "vstrands-scaf": {"include_keys": ['scaf'], "order_independent": False},

    "vstrands-stap-colors": {"include_keys": ['stap_colors'], "order_independent": False},
    "vstrands-scaf-colors": {"include_keys": ['scaf_colors'], "order_independent": False, "allow_missing_include_keys": True},

    "vstrands-skip": {"include_keys": ['skip'], "order_independent": False},
    "vstrands-loop": {"include_keys": ['loop'], "order_independent": False},
    "vstrands-scafLoop": {"include_keys": ['scafLoop'], "order_independent": False},

}


def json_hash_hexdigets(obj, hash_name="sha256", json_separators=(",", ":")) -> str:
    """ Use json to serialize obj, then hash the serialized string.

    This is basically the simplest way I could think of to hash a json-serializable object.
    Of course, this has a bunch of potential issues:
    * Doesn't hash sets (order-invariant hashing).
    * Might change if the json-serialization changes for some reason (e.g. different defaults).

    Does json.dump sort the data (to make the order of sets and dicts order-independent)?
    * json does not sort dicts, unless `sort_keys=True`
    * json cannot serialize sets.
    * json does not sort lists, for obvious reasons.

    OBS:
    * For Python 3.6+, the key-order of dicts is maintained.
    * For Python 3.0-3.5, the order is random (since dict had no guaranteed order then).
    * In Python 2, json.dumps would produce sorted dicts.

    """
    json_str = json.dumps(obj, separators=json_separators)
    return hashlib.new(name=hash_name, data=json_str.encode("utf8")).hexdigest()


def order_dependent_json_hash_hexdigest(sequence, hash_name="sha256", json_separators=(",", ":")) -> str:
    """ Hash a list/sequence of objects by serializing the objects with json. """
    m = hashlib.new(name=hash_name)
    for obj in sequence:
        json_str = json.dumps(obj, separators=json_separators)
        m.update(json_str.encode("utf-8"))
    return m.hexdigest()


def order_independent_json_hash_intdigest(sequence, hash_name="sha256", json_separators=(",", ":")) -> int:
    total = 0
    for obj in sequence:
        json_str = json.dumps(obj, separators=json_separators)
        m = hashlib.new(name=hash_name, data=json_str.encode("utf8"))
        bytes_digest = m.digest()
        int_digest = int.from_bytes(bytes_digest, byteorder="big")
        # We use addition as the commutative operation to ensure order-independence:
        total += int_digest
        # Make sure integer is within the fixed-width size of the hashing algorithm:
        # It would be nice to have wrap-around integer objects in python...
        # Maybe use https://pypi.org/project/fixedint/
        total = total % 2**(8*m.digest_size)
    return total


def order_independent_json_hash_hexdigest(sequence, hash_name="sha256", json_separators=(",", ":")) -> str:
    """ Hash a set/sequence of objects in an order-independent way using json for object serialization.
    Order-independence is achieved using addition as the commutative operator between independent object hashes.
    """
    int_digest = order_independent_json_hash_intdigest(sequence, hash_name=hash_name, json_separators=json_separators)
    return f"{int_digest:0x}"


def vstrands_json_hash(
        vstrands,
        include_keys=None,
        exclude_keys=None,
        order_independent=False,
        hash_name="sha256",
        allow_missing_include_keys=False,
        allow_missing_exclude_keys=False,
        val_for_nonexisting_attributes=None,
        json_separators=(",", ":"),
        verbose=0,
) -> str:
    """ Calculate a single "vstrands" hash of a cadnano file, using the optionally-specified attributes.

    Args:
        vstrands: Cadnano vstrands list (from cadnano json file).
            The cadnano.json vstrands is a list of dicts, each dict describing a "virtual helix"
            with the following attributes:
            'num', 'row', 'col', 'stap', 'scaf', 'loop', 'stapLoop', 'scafLoop', 'skip', 'stap_colors', 'scaf_colors'
            ('scaf_colors' is only for cadnano 2.5 - earlier versions did not allow coloring the scaffold).
        include_keys: Include only these vstrands attributes when calculating the hash.
        exclude_keys: Exclude these vstrands attributes before calculating the hash.
        order_independent: Whether the hash depends on the order of the vstrands list.
            This can be used to determine if the only thing that has changed is the order of the strands.
        hash_name: The hash algorithm to use (must be supported by hashlib).
        allow_missing_include_keys: What to do if a key listed in `include_keys` is not present in a vh.
            False = Raise KeyError.
            True = ignore silently, replace with `val_for_nonexisting_attributes`.
            None or "exclude" = ignore silently, do not include attribute in vh dict.
        allow_missing_exclude_keys: What to do if a key listed in `exclude_keys` is not present in a vh.
        val_for_nonexisting_attributes: The value to use for non-existing attribute.
        json_separators: The separators to use when serializing vstrands as json (list and key:value).
        verbose: Change verbosity during run. Useful for debugging.

    Returns:

        hash hexdigest (str)

    """
    if include_keys or exclude_keys:
        # We don't want to modify the original vstrands object, so make a copy:
        vstrands = deepcopy(vstrands)
    if verbose:
        print("exclude_keys:", exclude_keys)
        print("include_keys:", include_keys)
        print("allow_missing_include_keys:", allow_missing_include_keys)
        print("json_separators:", json_separators)
    if include_keys:
        if isinstance(include_keys, str):
            include_keys = (include_keys,)
        for vh in vstrands:
            keys_to_delete = [k for k in vh.keys() if k not in include_keys]
            for k in keys_to_delete:
                del vh[k]
        # Maybe it is better to just generate a new vstrands list?
        if allow_missing_include_keys:
            if allow_missing_include_keys in (None, "exclude"):
                vstrands = [{k: vh[k] for k in include_keys if k in vh} for vh in vstrands]
            else:
                vstrands = [{k: vh.get(k, val_for_nonexisting_attributes) for k in include_keys} for vh in vstrands]
        else:
            vstrands = [{k: vh[k] for k in include_keys} for vh in vstrands]
    if exclude_keys:
        if isinstance(exclude_keys, str):
            exclude_keys = (exclude_keys,)
        for i, vh in enumerate(vstrands):
            for k in exclude_keys:
                if allow_missing_exclude_keys:
                    vh.pop(k, None)  # Use pop, to prevent KeyError if key does not exist.
                else:
                    try:
                        del vh[k]
                    except KeyError as exc:
                        # print(f"Key '{k}' not in vh {i}, it only has keys:", vh.keys())
                        raise exc

    if order_independent:
        hexdigest = order_independent_json_hash_hexdigest(
            sequence=vstrands, hash_name=hash_name, json_separators=json_separators
        )
    else:
        hexdigest = order_dependent_json_hash_hexdigest(
            vstrands, hash_name=hash_name, json_separators=json_separators
        )

    return hexdigest


def cadnano_json_vstrands_hashes(
        jsonfile,
        # design_variant_keys=('row', 'loop', 'col', 'scafLoop', 'stap', 'scaf', 'num', 'skip', 'stapLoop'),
        # coloring_keys=('row', 'loop', 'col', 'scafLoop', 'stap', 'scaf', 'num', 'stap_colors', 'skip', 'stapLoop'),
        # del_color_keys: List[str] = None,  # Use typing.List to support multi-arg input.
        hash_vstrands_specs=None,
        hash_vstrands_specs_file: str = None,
        hash_name: str = "sha256",
        # hash_without_colors: bool = True,
        # hash_with_colors: bool = True,
        save_hashes_to_file: bool = True,
        save_hash_specs_to_file: bool = None,
        output_line_fmt: str = " * {hexdigest} {description}",   # " * {hexdigest} {description} hexdigest"
        verbose: int = 0,
):
    """ Calculate and output various hashes for a cadnano json file.

    The purpose of this is to make it quick to determine what has changed between different cadnano designs.
    This complements more detailed tools to display changes in cadnano files.

    CLI entry-point: cadnano-json-vstrands-hashes

    Args:
        jsonfile: The cadnano json file to hash ("legacy" cadnano json file format).
        hash_name: The hashing algorithm to use when hashing.
        save_hashes_to_file: Automatically save the calculated hashes to a file next to the jsonfile.
        hash_vstrands_specs: Dict specifying which vstrands hashes to calculate.
            Each dict entry is <description>: <kwargs-to
        hash_vstrands_specs_file: Load hash_vstrands_specs from a json file.
        save_hash_specs_to_file: Save hash_vstrands_specs to file (useful if just using the defaults).
        output_line_fmt: Change how each hexdigest hash output line is formatted.
        verbose: Change verbosity during run. Useful for debugging.

    Removed args:
        hash_without_colors: Create hash without staple color info.
        hash_with_colors: Create hash with staple color info.

    Returns:
        dict with the various hashes

    CLI Example usage:

        $ cadnano-json-vstrands-hashes "TR.ZZ-5nm-spaced-x60.json"

    OBS: I generally calculate hashes for each cadnano file,
    then check what changes have been made, if any, by diff'ing the "*.sha256-vstrands-hashes.txt" files:

        $

    I then use `cadnano-diff-jsondata` to see more detailed changes:

        $ cadnano-diff-jsondata "TR.ZZ-5nm-spaced-x60.json" "TR.ZZ-5nm-spaced-x60 - Copy.json"

    See also:
    * cadnano_diff_jsondata_cli()

    """
    # defaults:
    if hash_name is None:
        hash_name = "sha256"
    if save_hash_specs_to_file is None:
        save_hash_specs_to_file = True

    if hash_vstrands_specs is None:
        if hash_vstrands_specs_file:
            hash_vstrands_specs_file = Path(hash_vstrands_specs_file)
            hash_vstrands_specs = json.load(open(hash_vstrands_specs_file))
        else:
            hash_vstrands_specs = DEFAULT_VSTRANDS_HASH_SPECS

    date = datetime.now()
    hashes_output = {}

    jsonstr = open(jsonfile).read()
    hashes_output["full-file-contents"] = str_hash_hexdigest(jsonstr)
    jsondata = json.loads(jsonstr)
    vstrands = jsondata['vstrands']
    jsonpath = Path(jsonfile)

    for description, kwargs in hash_vstrands_specs.items():
        if verbose:
            print(f"\nCalculating '{description}' hash...", file=sys.stderr)
        hashes_output[description] = vstrands_json_hash(vstrands, **kwargs)

    output_lines = "\n".join(
        output_line_fmt.format(description=description, hexdigest=hexdigest)
        for description, hexdigest in hashes_output.items()
    )
    output_header = f"""\
# {date:%Y/%m/%d %H:%M:%S} > cadnano-json-vstrands-hashes --hash-name {hash_name} "{jsonpath.name}"
# rsenv.__version__: {__version__}
"""
    output = output_header + output_lines + "\n"

    print(output)

    if save_hashes_to_file:
        hash_filename = Path(jsonfile).with_suffix(f".{hash_name}-vstrands-hashes.txt")
        print("Saving hashes to file:", hash_filename, file=sys.stderr)
        try:
            hash_filename.write_text(output)
        except IOError as exc:
            print(f" - ERROR, unable to write to file: {exc}", file=sys.stderr)
        if save_hash_specs_to_file and hash_vstrands_specs:
            hash_vstrands_specs_file = Path(jsonfile).with_suffix(f".{hash_name}-vstrands-hashes-specs.json")
            print("Saving hash_vstrands_specs to file:", hash_vstrands_specs_file, file=sys.stderr)
            try:
                hash_vstrands_specs_file.write_text(json.dumps(hash_vstrands_specs))
            except IOError as exc:
                print(f" - ERROR, unable to write to file: {exc}", file=sys.stderr)

    return hashes_output


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
# The advantage of typer is that the CLI options is automatically updated when you update the function.
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
