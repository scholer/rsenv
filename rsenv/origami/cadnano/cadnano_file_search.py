# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module and CLI for finding cadnano files.


TODO: Use a proper data scheme validation library, e.g.:

* schema
    * https://github.com/keleshev/schema - 2.1k stars, 156 forks.
* pydantic
    * https://github.com/samuelcolvin/pydantic - 3.3k stars, 307 forks.
* python-jsonschema
    * https://github.com/Julian/jsonschema - 2.8k stars, 418 forks.
* Cerberus
    * https://github.com/pyeve/cerberus - 2.1k stars, 194 forks.


## Schema:

* Provides `Schema`, `And`, `Use`, `Optional` classes for building your schema.



## Pydantic:

* Pydantic provides a BaseModel class with type-enforced attributes.
* Raises ValidationError if initializing with wrongly-typed data.


## Cerberus:

* Could definitely be used.
* Option to allow/disallow unknown fields.
* Option to require all the specified fields (default is to ignore missing fields).
* Example:
```
>>> schema = {'name': {'type': 'string', 'maxlength': 10}}
>>> v = Validator(schema)
>>> document = {'name': 'john doe'}
>>> v.validate(document)
True
```


## python-jsonschema:

* Implementation of [JSON Schema](https://json-schema.org/) for Python.
    * Most of the "schema definition" is documented at json-schema.org,
      the python-jsonschema docs mostly has usage examples and other python-specific notes.
    * https://json-schema.org/understanding-json-schema/
* Has "meta-validators", e.g. "maxItems".
* Has a nice CLI: `$ jsonschema -i sample.json sample.schema`.
* I already have `jsonschema` installed in my rsenv environment.
* Example:
```
>>> from jsonschema import validate
>>> # A sample schema, like what we'd get from json.load()
>>> schema = {
...     "type" : "object",
...     "properties" : {
...         "price" : {"type" : "number"},
...         "name" : {"type" : "string"},
...     },
... }
>>> validate(instance={"name" : "Eggs", "price" : 34.99}, schema=schema)

>>> validate(instance={"name" : "Eggs", "price" : "Invalid"}, schema=schema)
ValidationError: 'Invalid' is not of type 'number'
```


Cerberus and python-jsonschema makes it easy to create a .schema file (e.g. in json),
whereas `schema` must be specified in python, and pydantic is more for runtime validation during object instantiation.

Cerberus vs python-jsonschema:

* python-jsonschema has an "outer" parameter to define what the given object is.
* cerberus, on the other han, just assumes the object to be validated is a dict/document with the given attributes.





Related: Pandas DataFrame validation:
--------------------------------------

* pandas-validation
* pandera
* Bulwark



Related: Validating web APIs:
------------------------------

* Schemathesis


"""

import sys
from pathlib import Path
import json
import jsonschema
import typer


CADNANO_SCHEMA = {
    # Not required, but recommended - mark this JSON document as a JSON Schema:
    "$schema": "http://json-schema.org/schema#",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "vstrands": {"type": "array"}
    },
    "required": ["name", "vstrands"],
}


def json_file_has_attr(filepath, attr):
    with open(filepath) as fp:
        data = json.load(fp)
    return isinstance(data, )


def find_cadnano_files(basedir, glob_pattern: str = "**/*.json", verbose: int = 0):
    """ Find cadnano files by looking not just at the extension, but by validating the json document.

    Rationale: Cadnano using the *.json file extension makes it super hard to find cadnano files
    using just the file name. (Imagine if all .docx, .pptx, and .xlsx files just had a .zip file extension).
    It is probably a good idea to use a more recognizable extension,
    but it would have to be something like ".cadnano.json" or ".cn2.json", ".cn25.json", etc.,
    since the cadnano UI doesn't recognize files other than .json.
    Also, even if you are using a an easily-recognizable file naming scheme, your collaborators might not be.

    Thus, this function and CLI will find all .json files in <basedir> (recursively),
    and check if the json document is consistent with being a cadnano file
    (specifically, having a "name" and "vstrands" properties).

    CLI entry-point: cadnano-file-search

    Args:
        basedir: The directory to look for cadnano files from.
        glob_pattern: Glob pattern to use. The default glob pattern, "**/*.json" will scan the basedir recursively.
        verbose: Be more verbose when printing whether a given file doesn't match the cadnano json schema.

    Returns:
        None

    """
    basedir = Path(basedir)
    file_candidates = basedir.glob(glob_pattern)  # use rglob to prefix "**/" to pattern.
    validator = jsonschema.Draft7Validator(schema=CADNANO_SCHEMA)
    validated_files = []
    for fp in file_candidates:
        try:
            document = json.load(open(fp))
        except (json.JSONDecodeError, IOError) as exc:
            print(f"Unable to load file '{fp}: {exc} ({type(exc)})", file=sys.stderr)
            continue
        try:
            validator.validate(document)
        except jsonschema.exceptions.ValidationError as exc:
            if verbose:
                print(f"{fp} is not valid cadnano file: {exc.message}", file=sys.stderr)
        else:
            print(fp)
            validated_files.append(fp)


# Create Typer click CLI:
# Typer is faster to create than click and is automatically updated when the function changes.
def find_cadnano_files_cli():
    typer.run(find_cadnano_files)


if __name__ == '__main__':
    find_cadnano_files_cli()
