# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

CLI for updating the "name" field in a cadnano json file.

This can also be done with other JSON tools, obviously.

* `jq` would be the obvious choice, but it does not support in-place file editing.
  (Likely because the file is still open when you try to write to it.)
  So you would have to use something like:
  * `jq '.address = "abcde"' test.json > "$tmp" && mv "$tmp" test.json`

* The `json` npm package allows for inplace editing:
    * `json -I -f package.json -e "this.name='adar'"`

"""

import json
import click
from pathlib import Path


@click.command("Get the name attribute a Cadnano JSON file.")
@click.argument("jsonfile")
def get_cadnano_json_name_cli(jsonfile):
    """ cadnano-get-json-name """
    with open(jsonfile) as fd:
        jsondata = json.load(fd)
    name = jsondata["name"]
    print(f"{name}")


@click.command("Set the name attribute a Cadnano JSON file to a given value.")
@click.argument("jsonfile")
@click.argument("name")
def set_cadnano_json_name_cli(jsonfile, name):
    """ cadnano-set-json-name """
    with open(jsonfile) as fd:
        jsondata = json.load(fd)

    jsondata["name"] = name
    print(f"Setting name to '{name}' for cadnano file: {jsonfile}")
    with open(jsonfile, 'w') as fd:
        json.dump(jsondata, fd, separators=(',', ':'))


@click.command("Update the name attribute of a Cadnano JSON file to match its current filename.")
@click.argument("jsonfile")
@click.option("--include-ext/--no-include-ext", default=True)
def reset_cadnano_json_name_cli(jsonfile, include_ext=True):
    """ cadnano-reset-json-name """
    with open(jsonfile) as fd:
        jsondata = json.load(fd)

    path = Path(jsonfile)
    if not include_ext:
        # path = path.with_suffix("")
        name = path.stem
    else:
        name = path.name
    jsondata["name"] = name
    print(f"Setting name to '{name}' for cadnano file: {jsonfile}")
    with open(jsonfile, 'w') as fd:
        json.dump(jsondata, fd, separators=(',', ':'))
