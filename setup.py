from distutils.core import setup


"""

Install or update from source, in editable mode:

    cd <directory containing this setup.py file>
    pip install -e .


"""


long_description = """

Various tools/utilities and modules for work.



"""

# To update entry points, just bump verison number and do `$ pip install -e .`

# update 'version' and 'download_url', as well as qpaint_analysis.__init__.__version__
setup(
    name='RsEnv',
    description='Various tools/utilities and modules for work.',
    long_description=long_description,
    version='0.4.3',  # Update for each new version
    packages=['rsenv'],  # List all packages (directories) to include in the source dist.
    url='https://github.com/scholer/rsenv',
    download_url='https://github.com/scholer/rsenv/archive/master.zip',
    author='Rasmus Scholer Sorensen',
    author_email='rasmusscholer@gmail.com',
    license='GNU General Public License v3 (GPLv3)',
    keywords=[
        # "GEL", "Image", "Annotation", "PAGE", "Agarose", "Protein",
        # "SDS", "Gel electrophoresis", "Typhoon", "GelDoc",
        "Molecular biology", "Biotechnology", "Bioinformatics",
        "DNA", "DNA sequences", "sequence manipulation",
        "Data analysis", "Data processing", "plotting", "Data visualization",
        "Image analysis", "AFM", "Microscopy", "TEM", "HPLC", "Chromatograms",
    ],

    # Automatic script creation using entry points has largely super-seeded the "scripts" keyword.
    # you specify: name-of-executable-script: [package.]module:function
    # When the package is installed with pip, a script is automatically created (.exe for Windows).
    # The entry points are stored in ./gelutils.egg-info/entry_points.txt, which is used by pkg_resources.
    entry_points={
        'console_scripts': [
            # console_scripts should all be lower-case, else you may get an error when uninstalling:
            # Remember to copy changes to `rsenv.rsenv_cli.py` to keep `rsenv-help` command up to date.
            'nanodrop-cli=rsenv.dataanalysis.nanodrop.nanodrop_cli:cli',
            'hplc-cli=rsenv.hplcutils.cli:hplc_cli',
            'hplc-cdf-to-csv=rsenv.hplcutils.cdf_csv:cdf_csv_cli',
            'hplc-rename-cdf-files=rsenv.hplcutils.rename_cdf_files:rename_cdf_files_cli',

            # file converters and clipboard utils:
            'json-redump-fixer=rsenv.seq.cadnano.json_redump_fixer:main',
            'json-to-yaml=rsenv.fileconverters.jsonyaml:json_files_to_yaml_cli',
            'csv-to-hdf5=rsenv.fileconverters.hdf5csv:csv_to_hdf5_cli',
            'hdf5-to-csv=rsenv.fileconverters.hdf5csv:hdf5_to_csv_cli',
            'clipboard-image-to-file=rsenv.utils.clipboard:clipboard_image_to_file_cli',

            # `sha256sum` is used by UNIX sha256sum.exe distributed with e.g. Git
            'sha256sumsum=rsenv.utils.hash_utils:file_sha256sumsum_cli',
            'sha256setsum=rsenv.utils.hash_utils:file_sha256setsum_cli',
            'sequencesethash=rsenv.utils.hash_utils:file_sequencesethash_cli',

            # Text extraction and web batch downloader:
            'generic-text-extractor=rsenv.web.generic_text_extraction:generic_text_extractor_cli',
            'generic-batch-downloader=rsenv.web.generic_batch_download:generic_batch_downloader_cli',

            # Oligo-management:
            'convert-IDT-espec-to-platelibrary-file-cli='
            'rsenv.seq.oligomanagement.IDT_coa_to_platelibrary_file:convert_IDT_espec_to_platelibrary_file_cli',

            # Sequences and cadnano:
            'cadnano_maptransformer=rsenv.seq.cadnano.cadnano_maptransform:cadnano_maptransformer_cli',

            # File indexing and duplication finder:
            'duplicate-files-finder=rsenv.utils.duplicate_files_finder:find_duplicate_files_cli',

            # ELN: Print information about Pico/Markdown pages/files (based on the YAML header)
            # These have been moved to zepto-eln-core package.

            # Git commands/scripts:
            'git-add-and-commit-to-branch=rsenv.git.git_clis:git_add_and_commit_to_branch',
            'git-add-and-commit-script=rsenv.git.git_clis:git_add_and_commit_script',
            # OBS: There is a bug when setup.py contains two entry points with same name except one
            # has -script postfix, which prevents the other entry point from being generated correctly.

            # RsEnv help/docs/reference utils:
            'rsenv-help=rsenv.rsenv_cli:print_rsenv_help',
            'rsenv=rsenv.rsenv_cli:rsenv_cli',

        ],
        # 'gui_scripts': [
        #     'AnnotateGel=gelutils.gelannotator_gui:main',
        # ]
    },

    install_requires=[
        'pyyaml',
        'six',
        'requests',
        # 'pillow',
        'numpy',
        'scipy',
        'biopython',
        'matplotlib',
        'seaborn',    # Used by rsenv.hplcutils.chromviz
        # 'svgwrite',
        # 'cffi',      # Cairo is only required to convert SVG files to PNG
        # 'cairocffi',
        # 'cairosvg',
        'xarray',    # For reading CDF format.
        # 'pytables',  # For reading HDF5
        'pandas',    # General purpose reading/writing/plotting/manipulation of data.
        'click',     # Easy creation of command line interfaces (CLI).
        # 'openpyxl',  # Excel files package, required for xlsx-to-csv converter.
        'gitpython',  # GitPython, for git add-commit scripts

        # My own packages:
        # You may want to consider installing these first with `pip install -e <project dir>`.
        'pptx-downsizer',
        # 'gelutils',  # I'm disabling this for now, since gelutils currently only works with old Pillow version.
        # 'rstodo',
        # 'git_status_checker',
        # 'zepto-eln-server',
        # 'zepto-eln-core',
    ],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        # 'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Healthcare Industry',

        # 'Topic :: Software Development :: Build Tools',
        'Topic :: Education',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',

        'Operating System :: MacOS',
        'Operating System :: Microsoft',
        'Operating System :: POSIX :: Linux',
    ],

)
