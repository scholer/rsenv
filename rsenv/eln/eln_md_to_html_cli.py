
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
import pathlib
import webbrowser
import requests
import click
# import markdown  # https://pypi.org/project/markdown/
# import frontmatter  # https://pypi.org/project/python-frontmatter/

from .eln_md_pico import read_journal, pico_variable_substitution

GITHUB_API_URL = 'https://api.github.com'


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


@click.command()
@click.option('--parser', default='github', help="Specify the Markdown parser/generator to use.")
@click.option('--extensions', default=None, multiple=True, help="Specify which Markdown extensions to use.")
@click.option('--template', default=None, help="Load and apply a specific template (file).")
@click.option('--template-dir', default=None, help="The directory to look for templates.")
@click.option('--apply-template/--no-apply-template', default=None, help="Enable/disable template application.")
@click.option('--config', default=None, help="Read a specific configuration file.")
@click.option('--default-config/--no-default-config', default=False,
              help="Enable/disable loading default configuration file.")
@click.argument('inputfn')  # cannot add help to click arguments.
def convert_md_file_to_html_cli(
        inputfn, outputfn_fmt='{inputfn}.html', overwrite=None, open_webbrowser=True,
        parser='python-markdown', extensions=None,
        template=None, template_type='jinja2', template_dir=None, apply_template=None,
        config=None, default_config=None
):
    """ Convert ELN markdown journal file to HTML.

    Args:
        inputfn: Input markdown file name/path.
        outputfn_fmt: Output HTML filename (format string).
        overwrite: Whether to overwrite existing files if it exists.
        open_webbrowser: Set to True to automatically open the generated HTML file with the default web browser.
        parser: The Markdown parser to use to generate the HTML. Options are: 'github', or 'python-markdown'.

    Returns:
        Outputfn, the filename of the generated HTML file (str).

    Regarding template/variable substitutions:

        * %pico_variables% are substituted *before* converting markdown to HTML.
        * {{ Twig_variables }} are substituted in the Twig template;
            Twig variables *cannot* be used in the Markdown page, only the template.

    """
    journal = read_journal(inputfn, add_fileinfo_to_meta=True, warn_yaml_scanner_error='raise')
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
    html_content = markdown_to_html(journal['content'], parser=parser)
    pico_vars['content'] = html_content

    # Twig/Jinja template interpolation:
    if template:
        html = substitute_template_variables(
            template=pathlib.Path(template), template_type=template_type, template_vars=pico_vars
        )
    else:
        html = html_content

    # Write to output filename:
    outputfn = outputfn_fmt.format(inputfn=inputfn, **journal)
    with open(outputfn, 'w', encoding='utf-8') as fd:
        fd.write(html)

    # Post processes:
    if open_webbrowser:
        webbrowser.open(outputfn)

    return outputfn


if __name__ == '__main__':
    convert_md_file_to_html_cli()


