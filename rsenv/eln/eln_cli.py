# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

import inspect
import click

from rsenv.eln.eln_md_pico import print_document_yfm_issues
from rsenv.eln.eln_exp_filters import print_started_exps, print_unfinished_exps
from .eln_config import get_combined_app_config
from .eln_md_to_html import convert_md_files_to_html, convert_md_file_to_html


print_started_exps_cli = click.Command(
    callback=print_started_exps,
    name=print_started_exps.__name__,
    help=inspect.getdoc(print_started_exps),
    params=[
        # remember: param_decls is a list, *decls.
        click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc}'),
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])


print_unfinished_exps_cli = click.Command(
    callback=print_unfinished_exps,
    name=print_unfinished_exps.__name__,
    help=inspect.getdoc(print_unfinished_exps),
    params=[
        click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc:<40}  [enddate: {enddate}]'),
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])


print_journal_yfm_issues_cli = click.Command(
    callback=print_document_yfm_issues,
    name=print_document_yfm_issues.__name__,
    help=inspect.getdoc(print_document_yfm_issues),
    params=[
        # click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc} (enddate={enddate})'),
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])


_SYSCONFIG = get_combined_app_config()
# click.Command(context_settings={'max_content_width': 400})
# Using a Context with max_content_width isn't enough to prevent rewrapping,
# probably have to define a custom click.HelpFormatter.
convert_md_file_to_html_cli = click.Command(
    callback=convert_md_files_to_html,
    name=convert_md_file_to_html.__name__,
    help=convert_md_file_to_html.__doc__,
    # context_settings={'max_content_width': 400},  # Control help text rewrapping
    params=[
        click.Option(
            ['--outputfn'], default=_SYSCONFIG.get('outputfn'), help="Specify the Markdown parser/generator to use."),
        click.Option(
            ['--parser'], default=_SYSCONFIG.get('parser'), help="Specify the Markdown parser/generator to use."),
        click.Option(
            ['--extensions'], default=_SYSCONFIG.get('extensions'), multiple=True,
            help="Specify which Markdown extensions to use."),
        click.Option(
            ['--template'], default=_SYSCONFIG.get('template'),
            help="Load and apply a specific template (file)."),
        click.Option(
            ['--template-dir'], default=_SYSCONFIG.get('template_dir'),
            help="The directory to look for templates. Each markdown file can then choose which template (name) "
                 "to use to render the converted markdown."),
        click.Option(
            ['--apply-template/--no-apply-template'], default=_SYSCONFIG.get('apply_template'),
            help="Enable/disable template application."),
        click.Option(
            ['--open-webbrowser/--no-open-webbrowser'], default=_SYSCONFIG.get('open_webbrowser'),
            help="Open the generated HTML file in the default web browser."),
        click.Option(
            ['--config'], default=None, help="Read a specific configuration file."),
        # click.Option(
        #     ['--default-config/--no-default-config'], default=_SYSCONFIG.get('outputfn'),
        #              help="Enable/disable loading default configuration file."),
        # click.Argument(['inputfn'])  # cannot add help to click arguments.
        click.Argument(['inputfns'], nargs=-1)  # cannot add help to click arguments.
    ]
)


if __name__ == '__main__':
    # For testing only...
    # print_started_exps_cli()
    # print_unfinished_exps_cli()
    print_journal_yfm_issues_cli()
    # convert_md_file_to_html_cli()
