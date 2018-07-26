

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



