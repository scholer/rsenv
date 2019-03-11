

import os
import itertools
from collections import Counter, OrderedDict, defaultdict
import yaml
import click
import pandas as pd

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

unit_prefixes = {
    'm': 1_000,
    'u': 1_000_000,
    'µ': 1_000_000,
    'n': 1_000_000_000,
    'p': 1_000_000_000_000,
    'f': 1_000_000_000_000_000,
}

# From http://click.pocoo.org/6/arguments/:
# Click will not attempt to document arguments for you and wants you to document them manually (...).

# @click.option(
# '--query', '-q',
CONTEXT_SETTINGS = dict(
    max_content_width=200,  # Set to very high to prevent rewrapping completely.
)


@click.command(context_settings=CONTEXT_SETTINGS)  #
# Other options:
@click.option('--yamlfile', help="If given, read options from this yaml-formatted file.")
@click.option('--verbose', '-v', count=True,
              help="The verbosity with which information is printed during execution. "
                   "Specify multiple times to increase verbosity.")
@click.option('--user-vars', '-u', nargs=2, multiple=True, metavar="NAME VALUE",
              help="Add custom variables that can be used in filenames and query requests. "
                   "You can specify as many user-vars as you want, "
                   "and each user-var name can be specified multiple times to loop over the different variations.")
# Dataset naming and selection:
@click.option('--header-fmt',
              help="A python format string used to generate DataFrame column headers using metadata fields from the "
                   'input file. To only include Sample Name, use `--header-fmt "{Sample Name}"')
@click.option('--query-match-method', default='glob',
              help="How to query select the data sets to plot (matching against the generated header). "
                   "Options: 'glob', 'regex', 'full-word', 'exact', 'contains', etc. Default: glob.")
@click.option('--query-include-method', default='extend-unique',
              help="How to build/merge the list of selected samples for each query. "
                   "Default: 'extend-unique'. Alternatively: 'set-sorted' (for sorted idxs list).")
@click.option('--min-query-selection', default=0, type=int,
              help="Raise an error if query-selections return less than this number of candidates. (Query debugging)")
@click.option('--normalize/--no-normalize', default=False, help="Normalize the spectrograms before plotting.")
@click.option('--normalize-to', default=None, type=int, metavar="NM-VALUE",
              help="Normalize the spectrograms at a specific wavelength.")
@click.option('--normalize-range', nargs=2, type=int, metavar="LOWER UPPER",
              help="Normalize, using the average value within a certain range.")
# Plotting options and styles:
@click.option('--nm-range', nargs=2, type=int, metavar="MIN MAX",
              help="The range of wavelengths (nm) to use (data slicing).")
# @click.option('--AU-range', nargs=2, type=int, help="The range of absorbance values (AU/cm) to use.")
@click.option('--xlim', '-x', nargs=2, type=int, metavar="XMIN XMAX", help="Limit the plot to this x-axis range.")
@click.option('--ylim', '-y', nargs=2, type=int, metavar="YMIN YMAX", help="Limit the plot to this y-axis range.")
@click.option('--linestyles', '-l', multiple=True,
              help="The line style(s) to use when plotting. Will be combined combinatorically with colors."
              " Click options doesn't support an undefined number of values per option,"
              " so linestyles, colors, and markers must be given multiple times, once for each color."
              " Example: ` -l '-' -l ':', -l '--' `."
              " See https://matplotlib.org/gallery/lines_bars_and_markers/line_styles_reference.html for reference.")
@click.option('--colors', '-c', multiple=True,
              help="The color(s) to use when plotting. Will be combined combinatorially with line styles."
              " Example: `-c r -c #DD8833` to use red and orange lines.")
@click.option('--markers', multiple=True,
              help="The marker(s) to use when plotting. Will be combined combinatorially with other styles."
              ' Example: ` --markers "" --markers . --markers 1 --markers + `')
@click.option('--style-combination-order', nargs=3, default=('linestyle', 'color', 'marker'),
              help="The order in which linestyles, colors, and markers are combinatorically combined.")
@click.option('--mpl-style', help="Use this matplotlib style.")
@click.option('--figsize', nargs=2, type=float, metavar="WIDTH HEIGHT", help="Figure size (width, height).")
@click.option('--use-seaborn/--no-use-seaborn', default=False, help="Import seaborn color/style schemes.")
@click.option('--tight-layout/--no-tight-layout', '-t', default=None,
              help="If given, invoke `tight_layout()` before saving the figure.")
@click.option('--savetofile', '-o', multiple=True, help="Save plot to this file. Default = `filepath+.png`.")
@click.option('--saveformat', '-f', multiple=True, help="The file format(s) to save plot in. Default: 'png'.")
@click.option('--showplot/--no-showplot', '-s', default=None,
              help="If given, invoke `show()` after creating the plot.")
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
        user_vars=(),
        header_fmt=None,
        query=None,
        query_match_method="glob",
        query_include_method='extend-unique',
        query_exclude_method='list-remove',
        min_query_selection=0,
        normalize=False,
        normalize_to=None,
        normalize_range=None,
        nm_range=None,
        xlim=None,
        ylim=None,
        linestyles=None,
        colors=None,
        markers=None,
        style_combination_order=('linestyle', 'color', 'marker'),
        mpl_style=None,
        use_seaborn=False,
        figsize=None,
        tight_layout=None,
        savetofile=None,
        saveformat='png',
        showplot=None,
        verbose=0
):
    """ Plot spectrograms from a given nanodrop data file.


    Command line usage:

        $ nanodrop_cli plot [--OPTIONS] DATAFILE [SELECTION QUERIES]

    Example:

        $ nanodrop_cli plot datafile.csv "RS511*" "-RS511 b*" "RS511 b-11"

    This will load datafile.csv and plot all samples starting with RS511, except samples starting with "RS511 b",
    although do include "RS511 b-11"

    \b
    Args:
        filepath: path to nanodrop/denovix data file (.csv).
        yamlfile:
        user_vars:
        header_fmt:
        query: Query list used to select which data to plot. If None, plot all samples in the data file.
            See 'Examples' for how to use the query parameter.
        query_match_method: How to match each query request. Default: 'glob'.
            Options: 'glob', 'regex', 'full-word', 'exact', 'contains', 'in', 'startswith', 'endswith'.
        query_include_method:
        query_exclude_method:
        min_query_selection:
        normalize: If specified, normalize each spectrogram so its max value is 1.0 (bool, default: False).
        normalize_to: If given, normalize each spectrogram to its value at this wavelength.
        normalize_range: If given, normalize each spectrogram to its average value within this wavelength range.
        nm_range: The range (wavelength min, max) to plot.
        ylim: Limit the y-axis to this range.
        linestyles: Use these line styles, e.g. '-' or ':'.
        colors: The colors (cycle) to use to plot the spectrograms.
        markers: Markers to use when plotting.
        style_combination_order: The order in which (linestyles, colors, markers) are combined to produce styles.
        mpl_style: Use this matplotlib style.
        use_seaborn: Import seaborn and use the seaborn styles and plots.
        tight_layout: Apply tight_layout to pyplot figure.
        savetofile: Save plotted figure to this file.
        saveformat:
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


    The `--user-vars <KEY> <VALUE>` option can be used to define user variables and avoid having to change both the
    filename and queries when invoking the command repeatedly to display different data selections:

        Example 1: Using `-u` to define `expid` and `plateno` uservars, used in filename and queries:

            $ nanodrop-cli data.csv -o "{expid}_Plate{plateno}.{ext}" "{expid}*P{plateno}*" -u expid RS535 -u plateno 1

        This will plot all samples from data.csv matching "RS535*P1*" and save to file "RS535_Plate1.png"

        The `ext` extension is already defined with a default value 'png'.
        We currently have the following predefined variables and default values:
            ext         'png', depending on the value of 'saveformat'.
            normstr     'normX', depending on which normalization is used, or 'absorbance' if no normalization is used.

        Example 2: Specifying the same user variable multiple times:

            $ nanodrop-cli data.csv -o "RS535b_Plate{p}.{ext}" "*P{p}*" -u p 1 -u p 2 -u p 3

        \b
        This will load spectrograms from data.csv
             and plot all samples matching "*P1*" and save to file "RS535_Plate1.png",
            then plot all samples matching "*P2*" and save to file "RS535_Plate2.png",
            then plot all samples matching "*P3*" and save to file "RS535_Plate3.png".

        Note: You can specify multiple values for multiple user-vars to loop over the cartesian product combinations.

        Note: The input file is only loaded once and cannot contain user vars.
        If you need to loop over multiple input data files, you should use a command script, or use find/xargs/etc.

    """

    rootpath, ext = os.path.splitext(filepath)
    if yamlfile is None and os.path.isfile(rootpath+'.yaml'):
        # If no yamlfile was specified but we have a yaml file with same name as the input data file, use that one.
        yamlfile = rootpath+'.yaml'
    if yamlfile:
        yamlconfig = yaml.load(open(yamlfile))
    else:
        yamlconfig = {}
    if not savetofile:
        savetofile = yamlconfig.get('savetofile', rootpath+'.{ext}')
    if not saveformat:
        saveformat = yamlconfig.get('saveformat', 'png')
    if showplot is None:
        showplot = yamlconfig.get('showplot', False)
    if header_fmt is None:
        header_fmt = yamlconfig.get('header_fmt', "{Sample Number:>2} {Sample Name}")  # OBS: Sample Number is str.
    if not query:
        query = yamlconfig.get('query_list')
    if not nm_range:
        nm_range = yamlconfig.get('nm_range')
    if tight_layout is None:
        tight_layout = yamlconfig.get('tight_layout')
    if not user_vars:
        user_vars = yamlconfig.get('user_vars', [('we-need-at-least-one-loop-variable', 'this')])

    if isinstance(user_vars, (list, tuple)):
        # TODO: Detect user variables that have been specified multiple times, and define those as 'loop variables'.
        # You then extract loop combinations as itertools.product(*loop_vars.values())
        # user_vars_dict = dict(user_vars)
        # user_var_count = Counter([k for k, v in user_vars]) - Counter(user_vars_dict.keys())
        # # Zero counts should be removed. (The '+' unary operator can be used to remove negative counts).
        # user_loop_vars = OrderedDict([(k, [v_ for k_, v_ in user_vars if k_ == k]) for k in user_var_count])
        # for k in user_loop_vars:
        #     del user_vars_dict[k]
        # user_vars = user_vars_dict
        # In theory, we could just let all user vars be loop vars, with a repetition of 1?
        # Actually, that is probably a more consistent implementation path.
        user_loop_vars = defaultdict(list)
        for k, v in user_vars:
            user_loop_vars[k].append(v)
        print("User vars:", user_vars)
        print("Loop vars:", user_loop_vars)
        user_loop_keys, user_loop_vals = zip(*user_loop_vars.items())
        print("Loop keys:", user_loop_keys)
        print("Loop vals:", user_loop_vals)
    else:
        user_loop_keys, user_loop_vals = zip(*user_vars.items())
    loop_combinations = list(itertools.product(*user_loop_vals))
    print("Loop combinations:", loop_combinations)

    #
    # Load data:
    df, metadata = denovix.csv_to_dataframe(filepath, header_fmt=header_fmt, verbose=verbose)

    # Prepare for plot loops:
    fig_kwargs = yamlconfig.get('fig_kwargs', {})
    axes_kwargs = yamlconfig.get('axes_kwargs', {})
    plot_kwargs = yamlconfig.get('plot_kwargs', {})
    # * fig_kwargs - given to pyplot.figure() - https://matplotlib.org/api/_as_gen/matplotlib.pyplot.figure.html
    # * axes_kwargs - given to Figure.add_axes()
    # * plot_kwargs - given to pyplot.plot() or possibly df.plot()
    if figsize:
        fig_kwargs['figsize'] = figsize  # w, h?

    _query = query  # Make a copy
    ax = None

    for cno, comb in enumerate(loop_combinations, 1):
        user_vars = dict(zip(user_loop_keys, comb))
        print(f"{cno:01} User vars:", user_vars)
        print("savetofile:", savetofile)

        if query:
            if verbose:
                print(f"\nUsing the header/legend (as generated by `header_fmt` = {header_fmt!r}) to select columns...")
            if user_vars:
                # Update each request in the query list:
                print("Substituting user vars in query requests:", user_vars, end='\n')
                query = [request.format(**user_vars) for request in _query]
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

        print("Plotting, using fig_kwargs:")
        print(fig_kwargs)

        ax = denovix.plot_nanodrop_df(
            df=df, selected_columnnames=selected_cols,
            nm_range=nm_range, xlim=xlim, ylim=ylim,
            normalize=normalize, normalize_to=normalize_to, normalize_range=normalize_range,
            linestyles=linestyles, colors=colors, markers=markers, style_combination_order=style_combination_order,
            mpl_style=mpl_style, use_seaborn=use_seaborn,
            fig_kwargs=fig_kwargs, axes_kwargs=axes_kwargs, plot_kwargs=plot_kwargs,
            tight_layout=tight_layout,
            showplot=showplot, savetofile=savetofile, saveformat=saveformat,
            verbose=verbose, user_vars=user_vars,
        )

        print("\n - done plotting!\n\n\n")

    return ax


@click.command(help="List samples in a Nanodrop/Denovix data file.")
@click.argument('filepath', type=click.Path(exists=True))  # Do not provide help to arguments only options.
# @click.option('--print-fmt', default="       {meta['Sample Number']:>3} \t{meta['Sample Name']:20} \t{header:30}")
@click.option('--print-fmt', default='default1')
@click.option('--report-header-fmt', default=None)
@click.option(
    '--header-fmt', default="{Sample Name}-{Sample Number}",
    help="Format the DataFrame column names/headers with this format string using metadata fields from the file."
)
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
        header_fmt="{Sample Name}-{Sample Number}",  # how to generate measurement/column headers
        print_fmt="       {meta['Sample Number']:>3} \t{meta['Sample Name']:20} \t{header:30}",
        report_header_fmt=None,
        query=None, query_match_method="glob",
        query_include_method='extend-unique',
        query_exclude_method='list-remove',
        min_query_selection=0,
        unescape_backslashes=True,
        verbose=0,
):
    """ Print/list information about sample data in a Nanodrop file.

    OBS: This command was changed to make it more simple. Use `report` for advanced usage (concentration calc, etc.)
    Differences between `ls` and `report`:
        `ls` supports custom `print-fmt` and `header-fmt`; `report` uses a standard table layout format.
        `report` supports `extinction` (wavelength, ext.coeff) arguments to extract absorbance
            values and calculate concentrations; `ls` does not.

    Args:
        filepath: The nanodrop file to list information from.
        header_fmt: How to generate dataframe column names (column headers).
        print_fmt: How to print information for each sample (python format string).
        report_header_fmt: Add this header on top of the reported list.
        query: Only list samples matching these selection queries.
        query_match_method: The query matching method used. Default is glob, which allows wildcards, e.g "RS511*".
        query_include_method: How to merge idxs for each request with the existing idxs list from preceding requests.
        query_exclude_method: How to remove idxs for negative selection requests (starting with minus-hyphen).
            Queries are processed sequentially, and supports '-' prefix to negate the selection,
            and special 'all' keyword, e.g.
                ["all", "-John*", "John Hancock"]
            to select all people except if their name starts with John, although do include John Hancock.
        min_query_selection:
        unescape_backslashes: Can be activated to make it easier to provide special characters on the command line,
            e.g. tab. Useful when making reports.
        verbose: The verbosity with which to print informational messages during execution.


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
        A = values = df[header]  # All absorbance values
        # print(f"df[{header!r}]:")
        # print(df[header])
        # fmtdict = dict(header=header, meta=meta, values=values, A=values, c=conc, M=conc, mM=mM, uM=uM, AU=AU)
        # click.echo(print_fmt.format(**fmtdict))
        click.echo(print_fmt.format(**locals()))


@click.command(help="Report samples in a Nanodrop/Denovix data file.")
@click.argument('filepath', type=click.Path(exists=True))  # Do not provide help to arguments only options.
@click.option('--output-format', '-f', default='text')
# @click.option('--output-destination', '-o', default='-')
@click.option(
    '--header-fmt', default="{Sample Name}-{Sample Number}",
    help="Format the DataFrame column names/headers with this format string using metadata fields from the file."
)
@click.option('--wavelength', '-w', default=None, type=int, multiple=True,
              help="Specify a wavelength for which to include absorbance on in the report. See also `--extinction`."
              "Can be given multiple times to report at multiple wavelengths, e.g. `-w 230 -w 260 -w 280 -w 310`.")
@click.option('--extinction', '-e', default=None, type=(int, float), multiple=True,
              help="Provide extinction tuples (wavelength, ext. coeff), and the report will calculate concentrations."
              "Can be given multiple times to report at multiple wavelengths, e.g. `-e 230 8000 -e 260 10000`")
@click.option('--concentration-units', '-u', default=['mM', 'uM'], multiple=True,
              help="The units in which to report concentrations."
              "Can be given multiple times to report at multiple units, e.g. `-u mM -u uM`")
@click.option('--verbose', '-v', count=True, help="The verbosity with which information is printed during execution.")
@click.option('--query-match-method', default='glob',
              help="How to query-select the nanodrop data sets to include. Default: glob.")
@click.option('--query-include-method', default='extend-unique',
              help="How to build/merge the list of selected samples for each query. "
                   "Default: 'extend-unique'. Alternatively: 'set-sorted' (for sorted idxs list).")
@click.option('--min-query-selection', default=0, type=int,
              help="Raise an error if the query selection returns less than this number. "
                   "Can be used to debug and prevent accidental querying errors, especially in batch operations.")
@click.argument('query', nargs=-1)
def report(
        filepath,
        header_fmt="{Sample Name}-{Sample Number}",  # how to generate column names
        output_format='text',  # Text or HTML.
        wavelength=None,
        extinction=None,  # list of two-tuples with (wavelength, ext-coeff) floats in (nm, AU/cm/M)
        concentration_units=('mM', 'uM'),
        pathlength=1,  # Light path, in cm.
        query=None, query_match_method="glob",
        query_include_method='extend-unique',
        query_exclude_method='list-remove',
        min_query_selection=0,
        verbose=0,
):
    """ Print a report with information about sample/measurements in a Nanodrop/Denovix file.

    Args:
        filepath: The nanodrop file to list information from.
        header_fmt: How to generate dataframe column names/headers based on metadata (Sample Name, Sample Number, etc.)
        output_format: The format to output to, e.g. text or HTML.
        wavelength: A list of wavelength for which to include absorbance on in the report.
        extinction: Provide sample extinction (wavelength, ext. coeff) tuple,
            and the program will calculate concentration (M, mM, uM).
        concentration_units: The units to report the concentration in (e.g. 'M', 'mM', 'uM', etc).
        pathlength: The pathlength (light path) used when acquiring the data, in cm. Typically 0.1 cm for Nanodrop.
        query: Only list samples matching these selection queries.
        query_match_method: The query matching method used. Default is glob, which allows wildcards, e.g "RS511*".
        query_include_method: How to merge idxs for each request with the existing idxs list from preceding requests.
        query_exclude_method: How to remove idxs for negative selection requests (starting with minus-hyphen).
            Queries are processed sequentially, and supports '-' prefix to negate the selection,
            and special 'all' keyword, e.g.
                ["all", "-John*", "John Hancock"]
            to select all people except if their name starts with John, although do include John Hancock.
        min_query_selection:
        verbose: The verbosity with which to print informational messages during execution.

    Returns:
        None (all output is done to stdout).

    Examples:

        $ nanodrop-cli ls UVvis_merged.csv -e 290 12500 -v -v \
            --print-fmt "{meta[Sample Number]:2}\t {meta[Sample Name]:16}\t {A[290]: 6.3f}  {uM: 5.0f}"  \
            --report-header-fmt "#:\t Sample Name     \t  A290 \t    uM\n----------------------------------------------"
            "RS531*" "*dUTP" "KCl*"

    Notes:

        As always, you can use '--' to separate options and arguments, if you need to input arguments
        that looks like options (e.g. starts with '-').

    See also:

        * `ls` to list samples from a Nanodrop file (a simpler version of `report`).

    """
    if concentration_units is None or concentration_units == ():
        concentration_units = ['mM', 'uM']

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
    report_df = pd.DataFrame(data={'Measurement-Header:': df.columns})
    if extinction:
        print(f"\nUsing path length L = {pathlength} cm for concentration calculations (`--pathlength`)...\n\n")
    for wavelength in wavelength:
        AU = df.loc[wavelength, :].values  # This produces a series; use pd.Series.values to get values.
        abs_header, apl_header = f"A{wavelength}", f"A{wavelength}/cm"
        AU_per_cm = AU / pathlength  # A/cm, pathlength in cm.
        report_df[abs_header], report_df[apl_header] = AU, AU_per_cm
    print("concentration_units:")
    print(concentration_units)
    for wavelength, ext_coeff in extinction:
        AU = df.loc[wavelength, :].values  # This produces a series; use pd.Series.values to get values.
        abs_header, apl_header, = f"A{wavelength}", f"A{wavelength}/cm"
        AU_per_cm = AU / pathlength  # A/cm, pathlength in cm.
        conc = AU_per_cm / ext_coeff  # In moles/L
        report_df[abs_header], report_df[apl_header] = AU, AU_per_cm

        for unit in concentration_units:
            if len(unit) > 2:
                raise ValueError(f"Unit {unit!r} not recognized.")
            if unit == 'M':
                factor = 1
            else:
                factor = unit_prefixes[unit[0]]
            report_df[f"c_A{wavelength}/{unit}"] = conc * factor

    # Table styling:
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_string.html
    # pd.options.display.float_format = '{:,.2f}'.format  # Using the format() function of the string.
    # Use `float_format` parameter to control how floats are printed,
    # Use `formatters` to have per-column formats.

    output_format = output_format.lower()
    if output_format == "to_string":
        click.echo(report_df.to_string(index=False, header=True))
    elif output_format == "text":
        import tabulate
        # Other packages for pretty-printing tables include:
        # beautifultable terminaltables tabulate prettypandas fixedwidth
        click.echo(tabulate.tabulate(report_df, headers=report_df.columns, showindex=False))
    elif output_format == "html":
        click.echo(report_df.to_html(index=False, header=True))
    else:
        raise ValueError(f"`output_format` {output_format!r} not recognized.")


@click.group()
def cli():  # context_settings=CONTEXT_SETTINGS
    pass


cli.add_command(plot)
cli.add_command(ls)
cli.add_command(report)


if __name__ == '__main__':
    cli()

