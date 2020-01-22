# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module and CLI for pretty-printing cadnano json files.

Wow, this was actually much more work than just doing a manual, custom-made data-level diff.
See cadnano-json-data-diff.

"""

import json
from pprint import pprint
import click
import sys
import yaml
import yaml.dumper
from yaml.dumper import Dumper, SafeDumper
# Dumper and SafeDumper are identical, except SafeDumper use SafeRepresenter.
from yaml.emitter import Emitter
from yaml.serializer import Serializer
from yaml.resolver import Resolver
from yaml.representer import Representer, SafeRepresenter
import pdb


def pretty_print_json_cli(
        jsonfile,
        width=80, depth=None, compact=False, sort_dicts=True,
        truncation_placeholder="(...)",
):
    """ """
    jsondata = json.load(open(jsonfile))
    kwargs = {}
    if sys.version_info >= (3, 8):
        # sort_dicts arg only for Python >= 3.8
        kwargs["sort_dicts"] = sort_dicts
    pprint(jsondata, width=width, depth=depth, compact=compact, **kwargs)


def yaml_print_json_cli(
        jsonfile,
        default_flow_style=True,
        default_style=None,
        sort_keys=True,
        canonical=None, indent=None, width=None,
        allow_unicode=None, line_break=None,
        encoding=None, explicit_start=None, explicit_end=None,
        version=None, tags=None,
        dumper="SafeDumper",
):
    if isinstance(dumper, str):
        dumper = getattr(yaml.dumper, dumper)  # E.g. "SafeDumper" or "Dumper"
    jsondata = json.load(open(jsonfile))
    print(yaml.dump_all(
        [jsondata],
        Dumper=dumper,
        default_style=default_style,
        default_flow_style=default_flow_style,
        canonical=canonical, indent=indent, width=width,
        allow_unicode=allow_unicode, line_break=line_break,
        encoding=encoding, version=version, tags=tags,
        explicit_start=explicit_start, explicit_end=explicit_end, sort_keys=sort_keys
    ))


def json_compact(obj):
    return json.dumps(obj, separators=(",", ","))  # No spaces after comma.


DEEP_ITEMS_HANDLERS = {
    "json.dumps": json.dumps,
    "json": json.dumps,
    "json-compact": json_compact,
    "json_compact": json_compact,
}


def truncate_line_at(line, limit):
    if limit is not None and 0 < limit < len(line):
        return line[0:limit]
    else:
        return line


def represent_line_chars(line, limit, fmt="( {n_chars} ... )"):
    """

    Args:
        line:
        limit:
            limit=None or limit=-1 means never truncate line.
            limit=0 means always truncate line.
        fmt:

    Returns:

    """
    if limit is not None and 0 < limit < len(line):
        return fmt.format(n_chars=len(line), line=line)
    else:
        return line


LINE_TRUNCATORS = {
    "truncate_line_at": truncate_line_at,
    "represent_line_chars": represent_line_chars,
}


def handle_deep_items(
        obj, *,
        depth, handler, deep_items_truncator=None, deep_items_truncate_threshold=None,
        cast_other_to_str=True,
        cast_other_with_handler=False,
):
    if depth <= 0:
        assumed_str = handler(obj)
        if deep_items_truncator:
            pdb.set_trace()
            assumed_str = deep_items_truncator(assumed_str, limit=deep_items_truncate_threshold)
        return assumed_str
    if isinstance(obj, dict):
        return {k: handle_deep_items(
            v, depth=depth-1, handler=handler,
            deep_items_truncator=deep_items_truncator,
            deep_items_truncate_threshold=deep_items_truncate_threshold
        ) for k, v in obj.items()}
    if isinstance(obj, list):
        return [handle_deep_items(
                    v, depth=depth-1, handler=handler,
                    deep_items_truncator=deep_items_truncator,
                    deep_items_truncate_threshold=deep_items_truncate_threshold
                ) for v in obj]
    if isinstance(obj, set):
        return {handle_deep_items(
                    v, depth=depth-1, handler=handler,
                    deep_items_truncator=deep_items_truncator,
                    deep_items_truncate_threshold=deep_items_truncate_threshold
                ) for v in obj}
    else:
        if cast_other_to_str:
            return str(obj)
        else:
            return obj


@click.command()
@click.argument("jsonfile")
@click.option("--depth", type=int)
@click.option("--deep-items-handler")
@click.option("--deep-items-truncator")
@click.option("--truncate-threshold", type=int, default=80)
def cadnano_neatprinted_json_cli(
        jsonfile,
        depth=None,
        deep_items_handler="json.dumps",
        deep_items_truncator=represent_line_chars,
        truncate_threshold=20,
        outer_rep=yaml.dump,
        outer_width=100000,
        outer_indent=2,
):
    jsondata = json.load(open(jsonfile))
    if deep_items_handler is None:
        deep_items_handler = json.dumps
    if isinstance(deep_items_handler, str):
        deep_items_handler = DEEP_ITEMS_HANDLERS[deep_items_handler]
    if isinstance(deep_items_truncator, str):
        deep_items_truncator = deep_items_truncator.replace("-", "_")
        deep_items_truncator = LINE_TRUNCATORS[deep_items_truncator]

    print("deep_items_truncator:", deep_items_truncator)

    # Truncating deep items, optionally truncating the representation:
    data = handle_deep_items(
        jsondata,
        depth=depth, handler=deep_items_handler,
        deep_items_truncator=deep_items_truncator,
        deep_items_truncate_threshold=truncate_threshold,
    )

    # Dump and print:
    dumped = yaml.dump_all([data], width=outer_width, indent=outer_indent)
    dumped = yaml.safe_dump(data, width=outer_width, indent=outer_indent)
    print(dumped)

