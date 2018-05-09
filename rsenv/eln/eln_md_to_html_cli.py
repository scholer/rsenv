
"""

CLI Module specifically for converting Pico-ELN markdown pages to HTML.


Note regarding image resizing:

    If you want to resize images, the only consistent way to do it is to use html:

        <img src="drawing.jpg" alt="Drawing" style="width: 200px;"/>
        <img src="drawing.jpg" alt="Drawing" width="200px"/>

    Another consistent way is to add HTML divs around the images:

        <div style="width:50%">![Chilling](https://www.w3schools.com/w3images/fjords.jpg)</div>

    Some Markdown flavors/parsers support different ways to add styles or attributes.
    E.g. in Python-Markdown with the 'attrs-list' extension, you can do:

        ![Flowers](/flowers.jpeg){: .callout}

    While e.g. GitHub pages uses kramdown which supports additional attributes as such:

        ![smiley](smiley.png){:height="36px" width="36px"}

    With Pandoc: ![drawing](drawing.jpg){ width=50% }

    Other styles I've found around the web:

        ![pic][logo]{.classname}  # Uses a CSS-defined classname.

    And, of course, the best solution may just be to make a resized image file with the size you intend it to have.


    Refs:
    * https://stackoverflow.com/questions/255170/markdown-and-image-alignment
    * https://stackoverflow.com/questions/14675913/changing-image-size-in-markdown
    * https://stackoverflow.com/questions/24383700/resize-image-in-the-wiki-of-github-using-markdown
    * https://kramdown.gettalong.org/syntax.html#attribute-list-definitions


"""

import os
import glob
import sys
import pathlib
import webbrowser
import yaml
import requests
import click
from collections import OrderedDict
from pprint import pprint
# import markdown  # https://pypi.org/project/markdown/
# import frontmatter  # https://pypi.org/project/python-frontmatter/

from .eln_md_pico import read_journal, pico_variable_substitution

GITHUB_API_URL = 'https://api.github.com'


DEFAULT_CONFIG = yaml.load(r"""
outputfn: '{inputfn}.html'
overwrite: null
open_webbrowser: null
# Parser options are: 'github', or 'python-markdown'.
# See `markdown_to_html()` for more info on `parser` and `extensions` options.
parser: python-markdown
extensions:
 - markdown.extensions.fenced_code
 - markdown.extensions.attr_list
 - markdown.extensions.tables
 - markdown.extensions.sane_lists
# - 'markdown.extensions.toc
# See `substitute_template_variables()` for more info on template variables and templating systems.
template_type: jinja2
# template_dir: A directory with templates; each markdown file can specify its own template.
template_dir: D:/Dropbox/_experiment_data/templates/
apply_template: True
# A config (dict or file) containing options for each run, takes precedence over any given arguments!
config: null
default_config: null
""")

# > "Q: Is there an official extension for YAML files?"
# > "A: Please use ".yaml" when possible."
# - c.f. http://yaml.org/faq.html
# Although this is still somewhat contested in practice,
# c.f. https://stackoverflow.com/questions/21059124/is-it-yaml-or-yml,
#      http://markdblackwell.blogspot.dk/2013/07/use-file-extension-yml-for-yaml.html
# Specifically, Symphony and other larger projects are using .yml, not .yaml.
# Although even Symphony recommends .yaml for package recipes,
# - c.f. https://github.com/symfony/recipes/blob/master/README.rst#validation
# Drupal and Symphony issues:
# * https://github.com/symfony/symfony-standard/issues/595
# * https://www.drupal.org/node/2091669
# A search on my own computer has 429 *.yml files and 1145 *.yaml files.
# * The majority (392) of the *.yml files comes from myself, especially .labfluence.yml and gelannotator files.
# * The majority of the *.yaml comes from (a) Anaconda packages, (b) NVIDIA, (c) myself.
# Googling "filetype:yml" and "filetype:yaml" gives 272'000 vs 85'000 results, with .yaml often not being extension.
# I feel like I've had this discussion before, and I've still used different standards for different projects...
# TODO: Decide on a standard YAML file extension across all my dev projects!
CONFIG_PATHS = OrderedDict()
CONFIG_PATHS['global'] = [
    '~/.config/rsenv/eln-config-global.yaml',
    '~/.config/eln-config-global.yaml',
    '~/.rsenv/eln-config-global.yaml',
]
CONFIG_PATHS['local'] = [
    './eln-config.yaml',
    '~/.config/eln-config-global.yaml',
    '~/.rsenv/eln-config-global.yaml',
]

# TODO: Move all config-related functions to a shared config module.


def get_app_config_filepaths():
    """ Search the file system for global and local config files.

    Returns:
        {'global': global_path, 'local': local_path) dict of file paths for the global config and local config.

    Item values can be None, if no config files were found.

    Examples:
        >>> get_app_config_filepaths()
        '~/.config/rsenv/eln-config-global.yaml', './eln-config.yaml'
    """
    return OrderedDict([
        (k, next(iter(path for path in paths if os.path.isfile(path)), None))
        for k, paths in CONFIG_PATHS.items()]
    )


def get_app_configs():
    config_paths = get_app_config_filepaths()
    print("Using config files:")
    pprint(config_paths)
    configs = {}
    for k, path in config_paths.items():
        if path is None:
            configs[k] = None
        else:
            try:
                configs[k] = yaml.load(open(path, 'r'))
            except yaml.YAMLError as exc:
                raise exc
    return configs


def get_combined_app_config():
    configs = get_app_configs()
    merged_config = DEFAULT_CONFIG.copy()  # Maybe deepcopy?
    for k in ('global', 'local'):
        this_config = configs.get(k)
        if this_config:
            merged_config.update(this_config)
    return merged_config


def markdown_to_html(content, parser='python-markdown', extensions=None, template=None, template_type='jinja'):
    """ Convert markdown to HTML, using the specified parser/generator.

    Args:
        content: Markdown content (str) to convert HTML.
        parser: A string specifying which parser to use.
            Options include: 'github', and 'python-markdown' (default).
        extensions: A list of extensions to pass to the parser, or None for the default extensions set.

    Returns:
        HTML (string)

    Examples:
        >>> markdown_to_html("hello world!", parser='github')
        '<p>hello world</p>'

    Notes on the different parsers:
    -------------------------------

    Advantages of 'github' vs 'python-markdown' parser:
    * Github adds style="max-width:100%;" attribute to all <img> image elements.
        This can be accomplished globally, using a template,
        on a page-by-page basis by adding a <style> tag at the top of the page,
        or on a image-by-image basis by inserting images with <img> tags, or using markdown `{: attribute lists}`.

    These are the same, with the proper extension:
    * Code blocks (incl inside lists) renders as expected, if "Fenced code" extension is enabled.

    Python-Markdown extensions: https://python-markdown.github.io/extensions/
    * Extra: markdown.extensions.extra
        Enable 'extra' features from [PHP Markdown](https://michelf.ca/projects/php-markdown/extra/).
        * Fenced Code: markdown.extensions.fenced_code
            Enable support for ```python\n...``` fenced code blocks.
        * Attribute list: markdown.extensions.attr_list
            Add HTML attributes to any element (header, link, image, paragraph) using trailing curly brackets:
            `{: #someid .someclass somekey='some value' }`.
        * Footnotes: markdown.extensions.footnotes
        * Tables: markdown.extensions.tables
    * Sane Lists: markdown.extensions.sane_lists
    * Table of Contents: markdown.extensions.toc


    Templating systems:
    -------------------

    Overview:
    * Jinja2 - by the Pocoo team (Flask, Sphinx, Pygments).
    * Django template system (on which Jinja was modelled). Uses `{{` tags and `{%` blocks.
    * Twig - PHP, uses a {% similar %} {{ syntax }} to Django/Jinja.
        By Fabien Potencier (Symfony author) and Armin Ronacher (Jinja author).
    * Liquid - Another Django-inspired templating language. For Ruby.
    * Mustache - Also uses {{ curly }} braced syntax, but "Logic-less templating language".
    * Handlebars - extension of Mustache, originally JS.
    * Nunjucks - JS, similar to Jinja2.
    * Velocity - Java originating templating engine. Apache project.
    * Mako - Another popular Python templating language, using `<%` tags and `%` blocks.
    * Cheetah - Uses '#' line prefix and '$' variables, like Velocity. Very similar to writing Python code.
    * Genshi
    * Hiccup, Sneeze
    * Template Attribute Language (TAL)
    * HAML, JADE, Pug - Alternative "languages" to write the DOM.
    * Python-based templating: %s interpolation, {} formatting, and $ templating.
    *

    Typical extensions:
    * *.jinja2 (or just *.j2), *.twig, etc.
    * Can be single, *.jinja2, or *.html.jinja2 - similar to *.tar.gz.
    *


    Refs:
    * http://vschart.com/list/template-language/
    * http://jinja.pocoo.org/docs/2.10/switching/
    * https://en.wikipedia.org/wiki/Comparison_of_web_template_engines
    * https://www.quora.com/Was-Twigs-syntax-inspired-by-Liquid


    """
    if parser is None:
        parser = 'python-markdown'
    if parser == 'python-markdown':
        if extensions is None:
            extensions = [
                'markdown.extensions.fenced_code',
                'markdown.extensions.attr_list',
                'markdown.extensions.tables',
                'markdown.extensions.sane_lists',
                # 'markdown.extensions.toc',
            ]
        print("\nExtensions:", extensions)
        import markdown
        html_content = markdown.markdown(content, extensions=extensions)
    elif parser in ('github', 'ghmarkdown'):
        try:
            # Try to use the `ghmarkdown` package, and fall back to a primitive github api call
            import ghmarkdown
            return ghmarkdown.html_from_markdown(content)
        except ImportError:
            html_content = github_markdown(content)
    else:
        raise ValueError(f"parser={parser!r} - value not recognized.")

    return html_content


def github_markdown(markdown, verbose=None):
    """ Takes raw markdown, returns html result from GitHub api """
    endpoint = GITHUB_API_URL + "/markdown/raw"
    headers = {'content-type': 'text/plain', 'charset': 'utf-8'}
    res = requests.post(endpoint, data=markdown.encode('utf-8'), headers=headers)
    res.raise_for_status()
    return res.text


def substitute_template_variables(template, template_type, template_vars):
    if isinstance(template, pathlib.Path):
        template = open(template, encoding='utf-8').read()
    if template_type is None:
        template_type = 'jinja2'
    if template_type.startswith('jinja'):
        import jinja2
        print("template length:", len(template))
        template = jinja2.Template(template)
        html = template.render(**template_vars)
    elif template_type == 'pico':
        html = pico_variable_substitution(content=template, template_vars=template_vars)
    else:
        raise ValueError(f"Value {template_type!r} for `template_type` not recognized.")
    return html


def get_templates_in_dir(template_dir, glob_patterns=('*.twig',)):

    files = [fn for pat in glob_patterns for fn in sorted(glob.iglob(os.path.join(template_dir, pat)))]
    print(f"\nTemplate files in {template_dir!r}:", file=sys.stderr)
    print("\n".join(f" - {fn!r}" for fn in files), file=sys.stderr)

    templates_by_name = {os.path.splitext(os.path.basename(fn))[0]: fn for fn in files}
    templates_by_name.update({fn: fn for fn in files})
    pprint(templates_by_name)

    return templates_by_name


# You can control rewrapping of the help text either by adding a single \b escape character above each section,
# or using the 'context_settings' dict argument, setting the 'max_content_width' item to e.g. 400,
# c.f. https://github.com/pallets/click/issues/441
# @click.command(context_settings={'context_settings': 400})
# @click.option('--outputfn', default='github', help="Specify the Markdown parser/generator to use.")
# @click.option('--parser', default='github', help="Specify the Markdown parser/generator to use.")
# @click.option('--extensions', default=None, multiple=True, help="Specify which Markdown extensions to use.")
# @click.option('--template', default=None, help="Load and apply a specific template (file).")
# @click.option('--template-dir', default=None,
#               help="The directory to look for templates. Each markdown file can then choose which template (name) "
#                    "to use to render the converted markdown.")
# @click.option('--apply-template/--no-apply-template', default=None, help="Enable/disable template application.")
# @click.option('--open-webbrowser/--no-open-webbrowser', help="Open the generated HTML file in the default web browser.")
# @click.option('--config', default=None, help="Read a specific configuration file.")
# @click.option('--default-config/--no-default-config', default=False,
#               help="Enable/disable loading default configuration file.")
# @click.argument('inputfn')  # cannot add help to click arguments.
def convert_md_file_to_html(
        inputfn, outputfn='{inputfn}.html', overwrite=None, open_webbrowser=True,
        parser='python-markdown', extensions=None,
        template=None, template_type='jinja2', template_dir=None, apply_template=None,
        default_template_name='index',
        config=None, default_config=None
):
    """ Convert ELN markdown journal file to HTML.

    \b
    Args:
        inputfn: Input markdown file name/path.
        outputfn: Output HTML filename (format string).
        overwrite: Whether to overwrite existing files if it exists.
        open_webbrowser: Set to True to automatically open the generated HTML file with the default web browser.
        parser: The Markdown parser to use to generate the HTML.
            Options are: 'github', or 'python-markdown'.
            See `markdown_to_html()` for more info on `parser` and `extensions` options.
        extensions: The markdown extensions to use (parser-dependent).
        template: The template (file) to use for generating the HTML page.
            The html content converted from the .md input file is available as the `content` template variable.
        template_type: The templating system to use.
            See `substitute_template_variables()` for more info on template variables and templating systems.
        template_dir: Sometimes you may want to let each file itself decide which template it must be rendered with,
            typically specified via the YFM. In order to support this, we specify a folder where templates are stored,
            and each file can then select from the list of templates within this directory.
        apply_template: Can be used to disable template application on a run-by-run basis.
            Useful if a template_dir has been specified in the default config, and you want to disable that.
        config: A config (dict or file) containing options for each run.
            Note: The config takes precedence over any given arguments!
        default_config: A config (dict or file) containing default options (global config merged with local config).
            Note: Neither config or default_config has been implemented yet.
            Edit: This was actually added so I could enable/disable loading the system-wide default config. ¯\_(ツ)_/¯

    \b
    Returns:
        Outputfn, the filename of the generated HTML file (str).

    \b
    Regarding template/variable substitutions:
        * %pico_variables% are substituted *before* converting markdown to HTML.
        * {{ Twig_variables }} are substituted in the Twig template;
            Twig variables *cannot* be used in the Markdown page, only the template.

    \b
    Regarding arguments vs config vs default config:
            run-config > arguments > default config.
        Each variable takes its value as:
        >>> val = config.get('val', val if val is not None else default_config.get('val'))

    \b
    Examples:
        $ eln-md-to-html RS543.md \
            --outputfn
            --parser python-markdown \
            --

    \b
    TODOs:
        TODO: Add support for default global and local config files, and create a sensible default config.
            This includes setting all parameters to None by default,
            so we can determine if default values should be retrieved from the config.
        TODO: Split the "python API" function from the CLI command.
        TODO: It would be nice if the CLI command could use default values from the default configs for options.
            Although this would make it hard to know if, when an option has a given value,
            if the value is defined explicitly by the user, or through the default config.
            If we do it this way, then we need the run config to take precedence over the given arguments:
                run-config > command line arguments > default-config
            Whereas if we don't inject default values, we can let:
                command line arguments > run-config > default-config.
    """
    journal = read_journal(inputfn, add_fileinfo_to_meta=True, warn_yaml_scanner_error='raise')
    # returns journal dict with keys 'content', 'meta', 'fileinfo', etc.
    # Pico %variable.attribute% substitution:
    pico_vars = journal.copy()
    pico_vars.update(journal['fileinfo'])  # has 'dirname', 'basename', etc.
    pico_vars.update({
        'template_filename': template,
        'template_dir': os.path.dirname(template) if template else None,
        'assets_url': None,
        'theme_url': None,
    })

    # Perform %pico_variable% substitution:
    journal['content'] = pico_variable_substitution(journal['content'], template_vars=pico_vars, errors='print')

    # Markdown to HTML conversion:
    html_content = markdown_to_html(journal['content'], parser=parser, extensions=extensions)
    pico_vars['content'] = html_content

    if (template is None or not os.path.isfile(template)) and template_dir is not None:
        print("\n\n(template is None or not os.path.isfile(template)) and template_dir is not None\n\n")
        if template is None:
            template_name = journal['meta'].get('template', default_template_name)
            print(f"No template given, using template name from YFM (or default): {template_name!r}.")
        else:
            template_name = template
        template_selection = get_templates_in_dir(template_dir)
        try:
            template = template_selection[template_name]
        except KeyError:
            print(f"WARNING: Template directory does not contain any templates matching"
                  f" {template_name!r} (case sensitive).")
        else:
            print(f"Using template {template_name!r} from template directory {template_dir!r}.")

    # Twig/Jinja template interpolation:
    if template:
        html = substitute_template_variables(
            template=pathlib.Path(template), template_type=template_type, template_vars=pico_vars
        )
    else:
        html = html_content

    # Write to output filename:
    # TODO: Support writing to stdout instead of file.
    outputfn = outputfn.format(inputfn=inputfn, **journal)
    with open(outputfn, 'w', encoding='utf-8') as fd:
        print(f"\nWriting {len(html)} characters to file: {outputfn!r}\n", file=sys.stderr)
        fd.write(html)

    # Post processes:
    if open_webbrowser:
        webbrowser.open(outputfn)

    return outputfn


def convert_md_files_to_html(inputfns, **kwargs):
    """ Wrapper around `convert_md_file_to_html` for multi-file input.
    This also supports expansion of glob patterns, particularly useful on Windows.

    Args:
        inputfns:
        **kwargs: All other arguments are passed directly to `convert_md_file_to_html`.

    Returns:
        None
    """

    # Expand glob symbols:
    inputfns = [
        f for inputfn in inputfns
        for f in (glob.glob(inputfn, recursive=True) if '*' in inputfn else [inputfn])
    ]
    print("inputfns:", inputfns, file=sys.stderr)
    for inputfn in inputfns:
        convert_md_file_to_html(inputfn, **kwargs)


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
    convert_md_file_to_html_cli()


