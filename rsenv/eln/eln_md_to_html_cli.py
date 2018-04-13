
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

import webbrowser
import click
import requests
# import markdown  # https://pypi.org/project/markdown/
# import frontmatter  # https://pypi.org/project/python-frontmatter/

from .eln_md_pico import read_journal, pico_variable_substitution

GITHUB_API_URL = 'https://api.github.com'


def markdown_to_html(content, parser='python-markdown'):
    if parser is None:
        parser = 'python-markdown'
    if parser == 'python-markdown':
        import markdown
        return markdown.markdown(content)
    elif parser in ('github', 'ghmarkdown'):

        try:
            import ghmarkdown
            return ghmarkdown.html_from_markdown(content)
        except ImportError:
            return github_markdown(content)
    else:
        raise ValueError(f"parser={parser!r} - value not recognized.")


def github_markdown(markdown, verbose=None):
    """ Takes raw markdown, returns html result from GitHub api """
    endpoint = GITHUB_API_URL + "/markdown/raw"
    headers = {'content-type': 'text/plain', 'charset': 'utf-8'}
    res = requests.post(endpoint, data=markdown.encode('utf-8'), headers=headers)
    res.raise_for_status()
    return res.text


@click.command()
@click.option('--parser', default='github')
@click.argument('inputfn')
def convert_md_to_html(
        inputfn, outputfn_fmt='{inputfn}.html', overwrite=None, open_webbrowser=True,
        parser='python-markdown',
):
    """"""
    journal = read_journal(inputfn, add_fileinfo_to_meta=True, warn_yaml_scanner_error='raise')
    # Pico %variable.attribute% substitution:
    journal['content'] = pico_variable_substitution(journal['content'], journal, errors='print')
    # html = markdown.markdown(journal['content'])
    html = markdown_to_html(journal['content'], parser=parser)
    journal.update(journal['fileinfo'])  # has 'dirname', 'basename', etc.
    outputfn = outputfn_fmt.format(inputfn=inputfn, **journal)
    with open(outputfn, 'w', encoding='utf-8') as fd:
        fd.write(html)
    if open_webbrowser:
        webbrowser.open(outputfn)
    return outputfn


if __name__ == '__main__':
    convert_md_to_html()


