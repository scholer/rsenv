

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
# Dataset naming and selection:
@click.option('--header_fmt',
              help="A python format string used to generate DataFrame column headers "
                   "using metadata fields from the file.")
@click.option('--query-match-method', default='glob',
              help="How to query select the data sets to plot (matching against the generated header). Default: glob.")
@click.option('--query-include-method', default='extend-unique',
              help="How to build/merge the list of selected samples for each query. "
                   "Default: 'extend-unique'. Alternatively: 'set-sorted' (for sorted idxs list).")
@click.option('--min-query-selection', default=0, type=int,
              help="Raise an error if query-selections return less than this number of candidates. (Query debugging)")
@click.option('--normalize/--no-normalize', default=False,
              help="If given, normalize the spectrograms to the highest value before plotting.")
# Plotting options:
@click.option('--nm-range', '-x', nargs=2, type=int, help="The range of wavelengths (nm) to use.")
@click.option('--tight-layout/--no-tight-layout', '-t', default=None,
              help="If given, invoke `tight_layout()` before saving the figure.")
@click.option('--savetofile', '-o', multiple=True, help="Save plot to this file. Default = `filepath+.png`.")
@click.option('--showplot/--no-showplot', '-s', default=None,
              help="If given, invoke `show()` after creating the plot.")
# Other options:
@click.option('--yamlfile', help="If given, read options from this yaml-formatted file.")
@click.option('--verbose', '-v', count=True, help="The verbosity with which information is printed during execution.")
# Arguments:
@click.argument(
    'filepath', type=click.Path(exists=True),
    # help="Path of the nanodrop/denovix data file to plot.",  # Do not provide help for arguments, only options.
)
@click.argument(
    'query', nargs=-1,
    # help= # 'help' arg only for click options, not args.
)
def plot(
        filepath,
        yamlfile=None,
        header_fmt=None,
        query=None, query_match_method="glob",
        query_include_method='extend-unique',
        query_exclude_method='list-remove',
        min_query_selection=0,
        normalize=False,
        nm_range=None,
        tight_layout=None,
        savetofile=None,
        showplot=None,
        verbose=0
):
    """ Plot spectrograms from a given nanodrop data file.

    Command line usage:
        $ nanodrop_cli plot DATAFILE [SELECTION QUERIES]
    e.g.
        $ nanodrop_cli plot datafile.csv "RS511*" "-RS511 b*" "RS511 b-11"

    Args:
        filepath: path to nanodrop/denovix data file (.csv).
        yamlfile:
        header_fmt:
        query: Query list used to select which data to plot. If None, plot all samples in the data file.
            See 'Examples' for how to use the query parameter.
        query_match_method: How to match each query request. Default is "glob".
        nm_range: The range (wavelength min, max) to plot.
        tight_layout: Apply tight_layout to pyplot figure.
        savetofile: Save plotted figure to this file.
        showplot: Show plotted figure.
        verbose: Increase this to print more information during the data parsing+plotting process.

    Returns:

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
        if verbose:
            print(f"\nUsing the header/legend (as generated by `header_fmt` = {header_fmt!r}) to select columns...")
        selected_idxs = translate_all_requests_to_idxs(
            query, candidates=df.columns, match_method=query_match_method,
            include_method=query_include_method, exclude_method=query_exclude_method,
            min_query_selection=min_query_selection
        )
        selected_cols = [df.columns[idx] for idx in selected_idxs]
        if verbose >= 2:
            print(" query_list:", query)
            print("Selected:")
            print("\n".join(f"  {i:2} {n}" for i, n in zip(selected_idxs, selected_cols)))
    else:
        selected_cols = None

    ax = denovix.plot_nanodrop_df(
        df=df, selected_columnnames=selected_cols, nm_range=nm_range, normalize=normalize,
        plot_kwargs=plot_kwargs, tight_layout=tight_layout,
        savetofile=savetofile, showplot=showplot, verbose=verbose
    )

    # return ax


@click.command(help="List samples in a Nanodrop/Denovix data file.")
@click.argument('filepath', type=click.Path(exists=True))  # Do not provide help to arguments only options.
# @click.option('--print-fmt', default="       {meta['Sample Number']:>3} \t{meta['Sample Name']:20} \t{header:30}")
@click.option('--print-fmt', default='default1')
@click.option('--report-header-fmt', default=None)
@click.option(
    '--header-fmt', default="{Sample Name}-{Sample Number}",
    help="Format the DataFrame column names/headers with this format string using metadata fields from the file."
)
@click.option('--extinction', '-e', default=None, nargs=2)
@click.option('--verbose', '-v', count=True, help="The verbosity with which information is printed during execution.")
@click.option('--query-match-method', default='glob',
              help="How to query select the nanodrop data set to plot. Default: glob.")
@click.option('--query-include-method', default='extend-unique',
              help="How to build/merge the list of selected samples for each query. "
                   "Default: 'extend-unique'. Alternatively: 'set-sorted' (for sorted idxs list).")
@click.option('--min-query-selection', default=0, type=int)
@click.argument('query', nargs=-1)
def ls(
        filepath,
        header_fmt="{Sample Name}-{Sample Number}",  # how to generate column names
        print_fmt="       {meta['Sample Number']:>3} \t{meta['Sample Name']:20} \t{header:30}",
        report_header_fmt=None,
        extinction=None,  # two-tuple of (wavelength, ext-coeff) in (nm, AU/cm/M)
        pathlength=0.1,  # Light path, in cm.
        query=None, query_match_method="glob",
        query_include_method='extend-unique',
        query_exclude_method='list-remove',
        min_query_selection=0,
        unescape_backslashes=True,
        verbose=0,
):
    """ Print/list information about sample data in a Nanodrop file.

    Args:
        filepath: The nanodrop file to list information from.
        header_fmt: How to generate dataframe column names (column headers).
        print_fmt: How to print information for each sample (python format string).
        report_header_fmt: Add this header on top of the reported list.
        extinction: Provide sample extinction (wavelength, ext. coeff) tuple,
            and the program will calculate concentration (M, mM, uM).
        pathlength: The pathlength (light path) used when acquiring the data, in cm. Typically 0.1 cm for Nanodrop.
        query: Only list samples matching these selection queries.
        query_match_method: The query matching method used. Default is glob, which allows wildcards, e.g "RS511*".
        query_include_method: How to merge idxs for each request with the existing idxs list from preceding requests.
        query_exclude_method: How to remove idxs for negative selection requests (starting with minus-hyphen).
            Queries are processed sequentially, and supports '-' prefix to negate the selection,
            and special 'all' keyword, e.g.
                ["all", "-John*", "John Hancock"]
            to select all people except if their name starts with John, although do include John Hancock.

    Returns:


    Examples:

        $ nanodrop-cli ls UVvis_merged.csv -e 290 12500 -v -v \
            --print-fmt "{meta[Sample Number]:2}\t {meta[Sample Name]:16}\t {A[290]: 6.3f}  {uM: 5.0f}"  \
            --report-header-fmt "#:\t Sample Name     \t  A290 \t    uM\n----------------------------------------------"
            "RS531*" "*dUTP" "KCl*"

    Notes:

        As always, you can use '--' to separate options and arguments, if you need to input arguments
        that looks like options (e.g. starts with '-').
    """
    df, metadata = denovix.csv_to_dataframe(filepath, header_fmt=header_fmt)
    if query:
        selected_idxs = translate_all_requests_to_idxs(
            query, candidates=df.columns, match_method=query_match_method,
            include_method=query_include_method, exclude_method=query_exclude_method,
            min_query_selection=min_query_selection,
        )
        selected_cols = [df.columns[idx] for idx in selected_idxs]
        if verbose >= 2:
            print("\nSelected idxs:", selected_idxs)
            print("Selected cols:", selected_cols)
            # print(df.iloc[:, 0:2])  # 0-based indexing; equivalent to df.loc[:, selected_cols]
        assert len(selected_idxs) == len(set(selected_idxs))
        df = df.iloc[:, selected_idxs]  # 0-based indexing; equivalent to df.loc[:, selected_cols]
        # Also need to update metadata list:
        metadata = [metadata[idx] for idx in selected_idxs]
    if unescape_backslashes:
        if report_header_fmt:
            report_header_fmt = report_header_fmt.replace("\\t", "\t").replace("\\n", "\n")
        if print_fmt:
            print_fmt = print_fmt.replace("\\t", "\t").replace("\\n", "\n")
    if verbose >= 2:
        print("\n\n")
        print(f"report_header_fmt:\n{report_header_fmt!r}")
        print(f"print_fmt:\n{print_fmt!r}")
        print("\n\n")
    if verbose > -1:
        print(f"\n\nThe following samples / datasets were found in {filepath!r}:\n")
    # print("Sample Number:\tSample Name:           \tHeader/Legend: (generated with `header-fmt`)")
    # print("--------------\t------------           \t--------------------------------------------")
    if report_header_fmt is None and print_fmt == 'default1':
        report_header_fmt = 'default1'
    if report_header_fmt:
        if report_header_fmt in ('default1', 1):
            report_header_fmt = """
Sample Number:\tSample Name:           \tHeader/Legend: (generated with `header-fmt`)
--------------\t------------           \t--------------------------------------------
"""
        print(report_header_fmt.format(df, metadata))
    if print_fmt == 'default1':
        print_fmt = "       {meta[Sample Number]:>3} \t{meta[Sample Name]:20} \t{header:30}"
    for header, meta in zip(df.columns, metadata):
        # Note: f-strings and string.format have slightly different signature for e.g. accessing items:
        # "{dic[key]}".format(dic=dic)  vs  f"{dic['key']}"
        A = values = df[header]
        # print(f"df[{header!r}]:")
        # print(df[header])
        if extinction:
            wavelength, ext_coeff = tuple(map(float, extinction))
            AU = values[wavelength]
            c = conc = M = AU / ext_coeff / pathlength  # A = ext * c * L  <=> c = A / c / L
            mM = M * 1_000
            uM = M * 1_000_000
        # click.echo(print_fmt.format(header=header, meta=meta, values=values, A=values, c=conc, M=conc, mM=mM, uM=uM, AU=AU))
        click.echo(print_fmt.format(**locals()))


@click.group()
def cli():  # context_settings=CONTEXT_SETTINGS
    pass


cli.add_command(plot)
cli.add_command(ls)


if __name__ == '__main__':
    cli()

