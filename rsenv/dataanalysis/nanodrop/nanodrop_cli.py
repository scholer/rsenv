

import os
import yaml
import click

from rsenv.dataanalysis.nanodrop import denovix
from rsenv.utils.query_parsing import translate_all_requests_to_idxs

"""
    Alternative name:
        plot
        plot_nanodrop_data
        load_nanodrop_data_and_plot_requested_samples


    # Edit: Don't provide Args help in the docstring for click commands, provide that to click.option.

    Args:
        yamlfile:
        header_fmt: Format the DataFrame header this way using metadata fields from the file.
            Default: "{Sample Name}-{Sample Number}"
        query_match_method: How to query select the nanodrop data set to plot.
            See `rsenv.utils.query_parsing.translate_all_requests_to_idxs` for info.
        savetofile: Save plot to this file. Default = `filepath+.png`.
        nm_range: The range of wavelengths (nm) to use (x-axis).
            Note: This is data-selection, not actual plot `xlim`. Use `plot_kwargs` in `yamlfile` to provide xlim/ylim.
        tight_layout: Whether to invoke `tight_layout()` before saving the figure.
        verbose: The verbosity with which information is printed during execution.

    Returns:
        None



"""

# From http://click.pocoo.org/6/arguments/:
# Click will not attempt to document arguments for you and wants you to document them manually (...).

# @click.option(
# '--query', '-q',
CONTEXT_SETTINGS = dict(
    max_content_width=400,  # Prevent rewrapping completely.
)


@click.command()  # context_settings=CONTEXT_SETTINGS
@click.option('--yamlfile', help="If given, read options from this yaml-formatted file.")
@click.option('--header_fmt', help="Format the DataFrame header this way using metadata fields from the file.")
@click.option('--query_match_method', default='glob',
              help="How to query select the nanodrop data set to plot. Default: glob.")
@click.option('--nm_range', '-x', nargs=2, type=int, help="The range of wavelengths (nm) to use.")
@click.option('--tight-layout/--no-tight-layout', '-t', default=None,
              help="If given, invoke `tight_layout()` before saving the figure.")
@click.option('--savetofile', '-o', multiple=True, help="Save plot to this file. Default = `filepath+.png`.")
@click.option('--showplot/--no-showplot', '-s', default=None,
              help="If given, invoke `show()` after creating the plot.")
@click.option('--verbose', '-v', count=True, help="The verbosity with which information is printed during execution.")
@click.argument(
    'filepath', type=click.Path(exists=True),
    # help="Path of the nanodrop/denovix data file to plot.",  # Do not provide help for arguments, only options.
)
@click.argument(
    'query', nargs=-1,
    # help="Query used to select which data to plot. If None, plot all samples in the data file."
)
def plot(
        filepath,
        yamlfile=None,
        header_fmt=None,
        query=None, query_match_method="glob",
        nm_range=None,
        tight_layout=None,
        savetofile=None,
        showplot=None,
        verbose=0
):
    """ Plot spectrograms from a given nanodrop data file.

    Args:

        filepath: path to nanodrop/denovix data file (.csv).

        query: Query list used to select which data to plot. If None, plot all samples in the data file.

    Examples:

        To plot all samples in `datafile.csv` starting with "RS511":

        $ nanodrop_cli plot datafile.csv "RS511*"

        Note the use of the asterix (*) GLOB character used to select samples.

        You can use multiple "queries" to select the samples:

        $ nanodrop_cli plot datafile.csv "RS511*" ControlStandard "*B4*"

        This will plot all samples in `datafile.csv` that either starts with "RS511", or is "ControlStandard",
        or includes "B4" in the sample name.

        You can even negative selections, e.g.

        $ nanodrop_cli plot datafile.csv "RS511*" "-*B4*"

        This will plot all samples in `datafile.csv` that starts with "RS511"
        except samples containing "B4" in the name.

        You can even use the special query keyword "all" to start by including all samples,
        and then removing specific samples, e.g.:

        $ nanodrop_cli plot datafile.csv all "-*B4*"

        Will plot all samples from `datafile.csv` except samples containing "B4" in the name.

        It is possible to change the "query matching method" from 'glob' to e.g. 'substring', 'exact' or 'regex'
        using the `--query-match-method` option.

        Note that the query selection is done using the Legend / Header generated for each sample.
        By default, this includes both Sample Name and Sample Number (joined by a dash).
        You can use the `--header-fmt` option to change how the Header (Legend) is stiched together
        for each sample.

    """

    rootpath, ext = os.path.splitext(filepath)
    if yamlfile is None:
        if os.path.isfile(rootpath+'.yaml'):
            yamlfile = rootpath+'.yaml'
    if yamlfile:
        yamlconfig = yaml.load(open(yamlfile))
    else:
        yamlconfig = {}
    if not savetofile:
        savetofile = yamlconfig.get('savetofile', rootpath+'.png')
    if showplot is None:
        showplot = yamlconfig.get('showplot', False)
    if header_fmt is None:
        header_fmt = yamlconfig.get('header_fmt', "{Sample Name}-{Sample Number}")
    if not query:
        query = yamlconfig.get('query_list')
    if not nm_range:
        nm_range = yamlconfig.get('nm_range')
    if tight_layout is None:
        tight_layout = yamlconfig.get('tight_layout')

    # print("\nLocals:\n")
    # print(yaml.dump(locals()))
    # print()

    df, metadata = denovix.csv_to_dataframe(filepath, header_fmt=header_fmt, verbose=verbose)

    plot_kwargs = yamlconfig.get('plot_kwargs', {})

    if query:
        selected_idxs = translate_all_requests_to_idxs(
            query, candidates=df.columns, match_method=query_match_method)
        selected_cols = [df.columns[idx] for idx in selected_idxs]
        if verbose >= 2:
            print(" query_list:", query)
            print("Selected:")
            print("\n".join(f"  {i:2} {n}" for i, n in zip(selected_idxs, selected_cols)))
    else:
        selected_cols = None

    ax = denovix.plot_nanodrop_df(
        df=df, selected_columnnames=selected_cols, nm_range=nm_range,
        plot_kwargs=plot_kwargs, tight_layout=tight_layout,
        savetofile=savetofile, showplot=showplot, verbose=verbose
    )

    # return ax


@click.command(help="List samples in a Nanodrop/Denovix data file.")
@click.argument('filepath', type=click.Path(exists=True))  # Do not provide help to arguments only options.
@click.option(
    '--header_fmt', default="{Sample Name}-{Sample Number}",
    help="Format the DataFrame header this way using metadata fields from the file."
)
def ls(filepath, header_fmt):
    df, metadata = denovix.csv_to_dataframe(filepath, header_fmt=header_fmt)
    print(f"\nThe following samples / datasets were found in {filepath} :\n")
    print("Sample Number:\tSample Name:           \tHeader/Legend: (generated with `header-fmt`)")
    print("--------------\t------------           \t--------------------------------------------")
    for header, meta in zip(df.columns, metadata):
        click.echo(f"       {meta['Sample Number']:>3} \t{meta['Sample Name']:20} \t{header:30}")


@click.group()
def cli():  # context_settings=CONTEXT_SETTINGS
    pass


cli.add_command(plot)
cli.add_command(ls)


if __name__ == '__main__':
    cli()

