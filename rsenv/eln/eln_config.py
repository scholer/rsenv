# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>


import os
import yaml
from collections import OrderedDict
from pprint import pprint


DEFAULT_CONFIG = yaml.load(r"""
outputfn: '{inputfn}.html'
overwrite: null
open_webbrowser: null
# Parser options are: 'github', or 'python-markdown'.
# See `compile_markdown_to_html()` for more info on `parser` and `extensions` options.
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
