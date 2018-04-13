

import click



@click.command()
def print_rsenv_help():

    print(
        """

Available RsEnv CLI commands:
-----------------------------

NanoDrop/Denovix CLI:
    'nanodrop-cli=rsenv.dataanalysis.nanodrop.nanodrop_cli:cli',

HPLC CLIs:
    'hplc-to-pseudogel=rsenv.hplcutils.cli:hplc_to_pseudogel_cli',
    'hplc-cdf-to-csv=rsenv.hplcutils.cdf_csv:cdf_csv_cli',
    'hplc-rename-cdf-files=rsenv.hplcutils.rename_cdf_files:rename_cdf_files_cli',

File conversion CLIs:
    'json-redump-fixer=rsenv.seq.cadnano.json_redump_fixer:main',
    'json-to-yaml=rsenv.fileconverters.jsonyaml:json_files_to_yaml_cli',
    'csv-to-hdf5=rsenv.fileconverters.hdf5csv:csv_to_hdf5_cli',
    'hdf5-to-csv=rsenv.fileconverters.hdf5csv:hdf5_to_csv_cli',

Clipboard CLIs:
    'clipboard-image-to-file=rsenv.utils.clipboard:clipboard_image_to_file_cli',

Other file utilities:
    'duplicate-files-finder=rsenv.utils.duplicate_files_finder:find_duplicate_files_cli',

ELN CLIs: Print information about Pico/Markdown pages/files (based on the YAML header)
    'eln-print-started-exps=rsenv.eln.eln_md_pico:print_started_exps_cli',
    'eln-print-unfinished-exps=rsenv.eln.eln_md_pico:print_unfinished_exps_cli',
    'eln-print-journal-yfm-issues=rsenv.eln.eln_md_pico:print_journal_yfm_issues_cli',

RsEnv CLIs:
    'rsenv-help=rsenv.rsenv_cli:print_rsenv_help',

"""
    )


@click.group()
def rsenv_cli():
    """ RsEnv basic CLI.

    To list available RSENV CLIs, invoke:

        $ rsenv help

    """
    # The group code is performed first, then the requested command.
    # $ rsenv help
    pass


# Usually, we add commands to groups when defining the command function, using the Group.command decorator:
# @rsenv_cli.command()  # Notice: not the usual click.command()
# def help():
#   print("Unhelpful message.")
# Using the Group.command() decorator is in fact just a regular command() decorator followed by Group.add_command()
# However, since we want print_rsenv_help to be available as an independent command, we do it like this:
rsenv_cli.add_command(print_rsenv_help, name='help')


if __name__ == '__main__':
    rsenv_cli()
