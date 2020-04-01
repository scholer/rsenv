

Note: `rsenv` is a command-line / terminal program. 
You need to use your Command Prompt / Terminal app to install and run `rsenv` 
and the associated packages.

It also helps if you have prior experience with using the Terminal, using Git, and using Python—although
I'm sure you can make it work even if you have no prior experience with either.



Installation:
-------------

Download the latest development package from Github using Git:

```cmd
cd <the directory where you would like to have rsenv, e.g. %HOME%/Dev/
git clone https://github.com/scholer/rsenv
```


(Optional) Create a new virtual environment, to prevent package conflicts.
There are many tools for creating and managing virtual python environments.
I recommend using either `conda` or `pipenv`.
To create and activate a new environment with conda:

```
conda create -n rsenv pyyaml numpy pandas requests scipy biopython matplotlib xarray click 
activate rsenv
```

Note: On OSX/Linux, you need to write `source activate rsenv` in your terminal.


(Optional) Download and install development releases of related pacakges:

```cmd
git clone https://github.com/scholer/pptx-downsizer
pip install -e pptx-downsizer

git clone https://github.com/scholer/gelutils
pip install -e gelutils

```

To install `rsenv` in "editable" mode using the git repository you just downloaded:

```cmd
cd rsenv
pip install -e .
```

To uninstall `rsenv`:

```cmd
pip uninstall rsenv
```



Usage:
------

The `rsenv` has two purposes:

First, to provide a bunch of command line interfaces (CLIs), that I frequently use to perform basic tasks,
e.g. plot and convert HPLC or Nanodrop data files, parse my notebook markdown files, do sequence analysis, etc.
These CLIs are all used from the Terminal / Command Prompt, or executed via batch/shell files,
or as regular windows applications (by dragging and dropping files onto the executable file).


Second, `rsenv` provides a bunch of modules with functions that I use when working *inside Python*.
These are generally the same functions that is used through the CLIs, but inside the convenience
of a Python environment such as a Jupyter Notebook or IPython interpreter.

To see the available CLI commands, just type:

```cmd
rsenv --help
```


Brief description of the various CLI tools provided by this package:
--------------------------------------------------------------------



### Instrument data analysis and conversion:

**`nanodrop-cli`**: Plot data from the "Nanodrop" or "Denovix" line of spectrophotometers.

**`hplc-cli`**: Plot HPLC chromatograms (Agilent series HPLCs).

**`hplc-cdf-to-csv`**: Convert CDF files to CSV (CDF files exported from Agilent series HPLCs).

**`hplc-rename-cdf-files`**: Rename CDF according to the sample name contained within the CDF file metadata (CDF files exported from Agilent series HPLCs).


### File converters and clipboard utils:

**`json-redump-fixer`**: Correct badly-formatted "JSON" files (e.g. created by dumping a Python object representation to file) by loading the file and saving it with the proper json module.

**`json-to-yaml`**: Convert JSON files to YAML, which is often easier to read.

**`csv-to-hdf5`**: Convert CSV file to HDF5.

**`hdf5-to-csv`**: Convert HDF5 file to CSV.

**`clipboard-image-to-file`**: Save clipboard image data to file. Alternatively, use ImageMagick.


### File and data comparison CLIs:

**`oil-diff`**: Order-independent line diff program. Report which lines in a file have been added/removed/changed, but ignore the specific order of the lines.

**`sha256sumsum`**: Calculate 
**`sha256setsum`**:
**`sequencesethash`**:


(OBS: `sha256sum` is used by UNIX sha256sum.exe distributed with e.g. Git.)


### Text extraction and web batch downloader:

**`generic-text-extractor`**:
**`generic-batch-downloader`**:


### Oligo-management:

**`convert-IDT-espec-to-platelibrary-file-cli`**:


### Hashing and comparing oligo sets / pools of oligo sequences:
**`oligoset-file-hasher-cli`**:


### Hashing cadnano designs (because cadnano adds a time-stamp)::

**`cadnano-json-vstrands-hashes`**:

**`cadnano-get-json-name`**:

**`cadnano-set-json-name`**:

**`cadnano-reset-json-name`**:


### Cadnano diff`ing and pretty-printing:

**`cadnano-neatprinted-json`**:

**`cadnano-diff-jsondata`**:


### Cadnano, staple strand mapping, pooling:

**`cadnano-maptransformer`**:

**`cadnano-colorname-mapper`**:

**`oligo-wellplate-mapper`**:


### File management and renaming:

**`regex-file-rename`**:


### File indexing and duplication finder:

**`duplicate-files-finder`**:


### Label printing CLI:

**`print-zpl-labels`**:

(OBS: I have also written a ZPL-Label-Print plugin for Sublime Text, available as a separate 
package https://github.com/scholer/sublime-zpl-label-print, and on https://packagecontrol.io.)


### ELN: Print information about Pico/Markdown pages/files (based on the YAML header):

(These have been moved to zepto-eln-core package.)


### Git commands/scripts:

**`git-add-and-commit-to-branch`**:

**`git-add-and-commit-script`**:


(OBS: There is a bug when setup.py contains two entry points with same name except one
has -script postfix, which prevents the other entry point from being generated correctly.)

### Other data-plotting CLIs:

**`ohwmon-log-plotter`**:


### Conda environments CLIs:

**`export-all-conda-envs`**:


### RsEnv help/docs/reference utils:

**`rsenv-help`**:

**`rsenv`**:






