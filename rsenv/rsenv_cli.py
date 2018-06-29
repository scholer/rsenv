

import click

# 'nanodrop-cli=rsenv.dataanalysis.nanodrop.nanodrop_cli:cli',
# 'hplc-to-pseudogel=rsenv.hplcutils.cli:hplc_to_pseudogel_cli',
# 'hplc-cdf-to-csv=rsenv.hplcutils.cdf_csv:cdf_csv_cli',
# 'hplc-rename-cdf-files=rsenv.hplcutils.rename_cdf_files:rename_cdf_files_cli',
# 'json-redump-fixer=rsenv.seq.cadnano.json_redump_fixer:main',
# 'json-to-yaml=rsenv.fileconverters.jsonyaml:json_files_to_yaml_cli',
# 'csv-to-hdf5=rsenv.fileconverters.hdf5csv:csv_to_hdf5_cli',
# 'hdf5-to-csv=rsenv.fileconverters.hdf5csv:hdf5_to_csv_cli',
# 'clipboard-image-to-file=rsenv.utils.clipboard:clipboard_image_to_file_cli',
# 'duplicate-files-finder=rsenv.utils.duplicate_files_finder:find_duplicate_files_cli',
# # ELN: Print information about Pico/Markdown pages/files (based on the YAML header)
# 'eln-print-started-exps=rsenv.eln.eln_md_pico:print_started_exps_cli',
# 'eln-print-unfinished-exps=rsenv.eln.eln_md_pico:print_unfinished_exps_cli',
# 'eln-print-journal-yfm-issues=rsenv.eln.eln_md_pico:print_journal_yfm_issues_cli',
# 'eln-md-to-html=rsenv.eln.eln_md_to_html:convert_md_file_to_html_cli',
# # RsEnv utils:
# 'rsenv-help=rsenv.rsenv_cli:print_rsenv_help',
# 'rsenv=rsenv.rsenv_cli:rsenv_cli',
from rsenv.hplcutils.cli import hplc_to_pseudogel_cli
from rsenv.hplcutils.rename_cdf_files import rename_cdf_files_cli
from rsenv.eln.eln_md_to_html import convert_md_file_to_html_cli
from rsenv.eln.eln_cli import print_started_exps_cli, print_unfinished_exps_cli, print_journal_yfm_issues_cli
from rsenv.utils.clipboard import clipboard_image_to_file_cli

# MAKE SURE TO USE THE CLICK COMMAND ("*_cli") VERSIONS OF THE FUNCTIONS
# (I often make both a CLI and a regular, non-CLI version of most functions.)


@click.command()
def print_rsenv_help():
    """ Print further help information about rsenv package CLIs. """

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
    'eln-md-to-html=rsenv.eln.eln_md_to_html:convert_md_file_to_html_cli',

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
rsenv_cli.add_command(hplc_to_pseudogel_cli, name='hplc-to-pseudogel')
rsenv_cli.add_command(rename_cdf_files_cli, name='hplc-rename-cdf-files')
rsenv_cli.add_command(clipboard_image_to_file_cli, name='clipboard-image-to-file')
rsenv_cli.add_command(convert_md_file_to_html_cli, name='eln-md-to-html')
rsenv_cli.add_command(print_started_exps_cli, name='eln-print-started-exps')
rsenv_cli.add_command(print_unfinished_exps_cli, name='eln-print-unfinished-exps')
rsenv_cli.add_command(print_journal_yfm_issues_cli, name='eln-print-journal-yfm-issues')


if __name__ == '__main__':
    rsenv_cli()