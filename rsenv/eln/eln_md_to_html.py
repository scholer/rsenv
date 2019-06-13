# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>


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

from zepto_eln.md_utils.document_io import load_document
from zepto_eln.md_utils.markdown_compilation import compile_markdown_to_html

from .eln_md_pico import substitute_pico_variables

GITHUB_API_URL = 'https://api.github.com'



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
        html = substitute_pico_variables(content=template, template_vars=template_vars)
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
    """ ELN: Convert markdown journal/document file (.md) to HTML (.html).

    \b
    Args:
        inputfn: Input markdown file name/path.
        outputfn: Output HTML filename (format string).
        overwrite: Whether to overwrite existing files if it exists.
        open_webbrowser: Set to True to automatically open the generated HTML file with the default web browser.
        parser: The Markdown parser to use to generate the HTML.
            Options are: 'github', or 'python-markdown'.
            See `compile_markdown_to_html()` for more info on `parser` and `extensions` options.
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
    print(f"\nconvert_md_file_to_html started, inputfn {inputfn!r}, outputfn {outputfn!r} ...", file=sys.stderr)
    document = load_document(inputfn, add_fileinfo_to_meta=True, warn_yaml_scanner_error='raise')
    # returns journal dict with keys 'content', 'meta', 'fileinfo', etc.

    # Pico %variable.attribute% substitution:
    pico_vars = document.copy()
    pico_vars.update(document['fileinfo'])  # has 'dirname', 'basename', etc.
    pico_vars.update({
        'template_filename': template,
        'template_dir': os.path.dirname(template) if template else None,
        'assets_url': None,
        'theme_url': None,
    })
    document['content'] = substitute_pico_variables(document['content'], template_vars=pico_vars, errors='print')

    # Markdown to HTML conversion:
    html_content = compile_markdown_to_html(document['content'], parser=parser, extensions=extensions)
    pico_vars['content'] = html_content

    if (template is None or not os.path.isfile(template)) and template_dir is not None:
        print("\n(template is None or not os.path.isfile(template)) and template_dir is not None.\n", file=sys.stderr)
        if template is None:
            template_name = document['meta'].get('template', default_template_name)
            print(f"No template given, using template name from YFM (or default): {template_name!r}.", file=sys.stderr)
        else:
            template_name = template
        template_selection = get_templates_in_dir(template_dir)
        try:
            template = template_selection[template_name]
        except KeyError:
            print(f"WARNING: Template directory does not contain any templates matching"
                  f" {template_name!r} (case sensitive).", file=sys.stderr)
        else:
            print(f"Using template {template_name!r} from template directory {template_dir!r}.", file=sys.stderr)

    # Twig/Jinja template interpolation:
    if template:
        print("Performing template variable subsubstitution...", file=sys.stderr)
        html = substitute_template_variables(
            template=pathlib.Path(template), template_type=template_type, template_vars=pico_vars
        )
    else:
        html = html_content

    # Write to output filename:
    dirname = os.path.dirname(inputfn)  # e.g. '/path/to/Document.md'
    filepath_root, fnext = os.path.splitext(inputfn)  # e.g. '/path/to/Document', '.md'
    filename = os.path.basename(inputfn)  # e.g. 'Document.md'  (using 'basename' was a terrible choice, by the way)
    filename_noext = filebasename = os.path.basename(filepath_root)  # e.g. 'Document'
    filename_noext = filename_root = os.path.splitext(filename)[0]  # e.g. 'Document', alternative
    print("")
    outputfn = outputfn.format(
        inputfn=inputfn, dirname=dirname,
        # filename=filename,  # already included in `journal` dict.
        filebasename=filename_noext, filename_noext=filename_noext,
        fnroot=filepath_root, filepath_root=filepath_root,
        fnext=fnext.split('.'), filename_ext=fnext.split('.'),
        **document
    )
    if outputfn == "-":
        print(f"\nWriting {len(html)} characters to stdout...\n\n", file=sys.stderr)
        print(html, file=sys.stdout)
    else:
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





