# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module for diff'ing cadnano files.

Cadnano files can be diff'ed at two levels:

* The json file.
* The json data structure (cadnano1/2 json file structure).
* The cadnano document.
* The exported staple strand sequences.

Considerations for each of these:

* The json file is hard to diff, as it is saved as a single lne of text.
    It can be diffed after breaking the json up, but that is pretty hacky.
* The json data structure can be diffed, but this should generally only be used to
    show which vstrands (vhelices) have been changed, not the exact details.
    *
    * The `json_diff` CLI tool on cadnano json files is not very useful, as it
      cannot be limited in depth.


Alternative: Print json data until a given threshold limit.

* One option might be to:
    1. Load the cadnano json file.
    2. Create a dict with the same "name" and "vstrands" entries,
       but where each entry in "vstrands" is serialized separately as a single-line string.
    3. Save the serialized data to yaml.

* Another option: Just pretty-print the json data:
    1. Load cadnano json file.


"""

import json
import click


@click.command("CLI for diff'ing Cadnano .json files (cadnano format version 1 and 2).")
@click.argument("jsonfile1")
@click.argument("jsonfile2")
@click.option("--report-changed-list-indices/--no-report-changed-list-indices", default=True)
def cadnano_diff_jsondata_cli(
        jsonfile1,
        jsonfile2,
        report_changed_list_indices=True,
        report_indices_len_threshold=10,
):
    """ CLI for diff'ing Cadnano .json files (cadnano format version 1 and 2).

    CLI entry-point: cadnano-diff-jsondata

    This is currently my best and most concise method for determining the difference
    between two cadnano .json files at the json data level,
    without actually loading it as a cadnano document.

    """
    jsondata1 = json.load(open(jsonfile1))
    jsondata2 = json.load(open(jsonfile2))

    if jsondata1["name"] != jsondata2["name"]:
        print('\n"name" has changed:')
        print(f"< {jsondata1['name']}")
        print(f"> {jsondata2['name']}")

    for vs1, vs2 in zip(jsondata1["vstrands"], jsondata2["vstrands"]):
        vs1_name, vs2_name = ["vh {num}:{row},{col}".format(**vs) for vs in [vs1, vs2]]
        if vs1 != vs2:
            print(f"\n{vs1_name} has changed:" + (f"({vs1_name} --> {vs2_name}):" if vs1_name != vs2_name else ""))
            for k in vs1:
                if vs2[k] != vs1[k]:
                    print(f" - Change in '{k}':")
                    if isinstance(vs1[k], list) and report_changed_list_indices and report_indices_len_threshold < max(len(vs1[k]), len(vs2[k])):
                        changed_idxs = [idx for idx, (elem1, elem2) in enumerate(zip(vs1[k], vs2[k])) if elem1 != elem2]
                        print("    idxs for changed list elements:", changed_idxs)
                    else:
                        print(f"    < {vs1[k]}")
                        print(f"    > {vs2[k]}")


if __name__ == '__main__':
    cadnano_diff_jsondata_cli()
