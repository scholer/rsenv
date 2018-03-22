from distutils.core import setup


long_description = """

Various tools/utilities and modules for work.



"""


# update 'version' and 'download_url', as well as qpaint_analysis.__init__.__version__
setup(
    name='RsEnv',
    description='Various tools/utilities and modules for work.',
    long_description=long_description,
    # long_description=open('README.txt').read(),
    version='0.1.0dev',  # Update for each new version
    packages=['rsenv'],  # List all packages (directories) to include in the source dist.
    url='https://github.com/scholer/rsenv',
    # download_url='https://github.com/scholer/rsenv/tarball/0.1.0',
    download_url='https://github.com/scholer/rsenv/archive/master.zip',  # Update for each new version
    author='Rasmus Scholer Sorensen',
    author_email='rasmusscholer@gmail.com',
    license='GNU General Public License v3 (GPLv3)',
    keywords=[
        #"GEL", "Image", "Annotation", "PAGE", "Agarose", "Protein",
        #"SDS", "Gel electrophoresis", "Typhoon", "GelDoc",
        "Molecular biology", "Biotechnology", "Bioinformatics",
        "DNA", "DNA sequences", "sequence manipulation",
        "Data analysis", "Data processing", "plotting",
        "Image analysis", "AFM", "Microscopy", "TEM",
    ],

    # scripts or entry points..
    # scripts=['bin/annotate_gel.py'],

    # Automatic script creation using entry points has largely super-seeded the "scripts" keyword.
    # you specify: name-of-executable-script: module[.submodule]:function
    # When the package is installed with pip, a script is automatically created (.exe for Windows).
    # Note: The entry points are stored in ./gelutils.egg-info/entry_points.txt, which is used by pkg_resources.
    entry_points={
        'console_scripts': [
            # These should all be lower-case, else you may get an error when uninstalling:
            'json_redump_fixer=rsenv.seq.cadnano.json_redump_fixer:main',
            # 'annotategel_debug=gelutils.gelannotator_gui:main',  # Run as console script for debugging.
        ],
        # 'gui_scripts': [
        #     'AnnotateGel=gelutils.gelannotator_gui:main',
        # ]
    },

    install_requires=[
        'pyyaml',
        'yaml',
        'six',
        'requests',
        # 'pillow',
        'numpy',
        'scipy',
        'biopython',
        'matplotlib',
        'pptx-downsizer',
        # 'svgwrite',
        # 'cffi',      # Cairo is only required to convert SVG files to PNG
        # 'cairocffi',
        # 'cairosvg',
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Operating System :: MacOS',
        'Operating System :: Microsoft',
        'Operating System :: POSIX :: Linux',
    ],

)
