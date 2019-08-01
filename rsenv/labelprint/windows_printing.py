# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

Functions, references, and docs for printing on Windows.

This module includes a range of different functions, each function
using a different way to print files and content on Windows.

For instance:

    print_file_using_copy_cmd() - uses the `copy` command line command to print a file.
    print_file_using_print_cmd() - uses the `print.exe` command line program to print a file.
    print_file_using_lpr_cmd() - uses the `lpr.exe` command line program to print a file.
    print_file_using_notepad_cmd() - uses `notepad.exe` program to print a file.

    print_raw_win32print() - uses the `win32print` library to start a printing job directly.


Ways to communicate with and send print job s to a printer:
------------------------------------------------------------

## Printing on Windows:

Options:

1. Send a file to the printer using `COPY`, `PRINT`, `LP`, `LPR`, or similar command prompt command.

2. Use `win32print` module.

3. Open a socket and communicate with the printer directly.

    * This is how e.g. qztray prints.


What do other programs do?

* Socket communication: qztray (large project).
* Win32 module:
* Using wxPyhon.
    * wx.Printer()  - "Phoenix Printing framework"
* Send file to printer:



## Windows printing-related commands:


To list printers:

	wmic printer list brief
	wmic printer get name

Use `lpq` to display the status of a print queue on a computer running Line printer Daemon (LPD).

    lpq -S <server> -P <printer>



To capture/redirect all printed output to file:

* Go Printer properties -> Ports -> Add port -> Local port -> New Port -> Enter filename.
* https://stackoverflow.com/questions/13586865/get-zpl-code-from-zebra-designer



Prior art:
-----------



## Apps that actually prints labels (and optionally also generates them):

Python:

* https://github.com/stevelittlefish/easyzebra

* https://github.com/NewWorldVulture/zebra_printing
    * Uses win32print to print.

* https://github.com/lucas-hopkins/zebrapy
    * Uses the `usb` module to find printers: `dev = usb.core.find(idVendor=0xa5f)`
    * Then sends to printer with `dev.write(endpoints, bytearray.fromhex(content))`
    * Also has a socket communication option for IP printers.
    * Unfortunately, the git repo is a bit of a mess.

* https://github.com/w3blogfr/zebra-zpl
    * "Library used to generated commons ZPL command to print label on Zebra printer with java"
    * Has a `printZpl()` function, which uses a socket connection to communicate.
    * An alternative `printZpl()` function uses javax.print.PrintServiceLookup.lookupPrintServices()
        to find printer and send print job to it.

* https://github.com/artschwagerb/django-zebraprinters
    * Uses a socket connection to print to network printer (tasks.py)

* https://github.com/johncobb/print_services
    * Connects to a connected serial printer.
    * Uses a bash setup script to find available printers.

* https://github.com/twam/Zebra
    * "Python scripts to print on a Zebra label printer".
    * Uses `zpl2` package.
    * Uses `cups` package to print - I don't think this will work on Windows.
        * https://github.com/zdohnal/pycups
            * "These Python bindings are intended to wrap the CUPS API.".
        * https://pypi.org/project/pycups/
            * Yes, is listed with OS: Unix.

Non-python:

* qztray
    * https://github.com/qzind/tray

* https://github.com/bbulpett/zebra-zpl
    * Gem for using Ruby to print Zebra labels.
    * Can both generate labels and print them.
    * Prints using `rlpr`, falls back to `lp`.
    * # try printing to LPD on windows machine first:
        * `result = system("rlpr -H #{@remote_ip} -P #{@printer} -o #{path} 2>&1")`
    * # print to unix (CUPS) if rlpr failed:
        * `system("lp -h #{@remote_ip} -d #{@printer} -o raw #{path}") if !result`
    * Requires a printer with an IP address. (Maybe hostname is OK?)

* Zebra provides both Java and .NET SDKs for printing to Zebra printers.



## Apps for generating labels:


Python:

* https://github.com/cod3monk/zpl
    * Can be used to generate ZPL labels using an OOP approach to build the labels from ground up.
    * It is basically just a slightly nicer way to write the ZPL code by hand.
        E.g. the `label.origin` command just adds a new `^FO` command:
            def origin(self, x,y):
                self.code += "^FO%i,%i" % (x*self.dpmm, y*self.dpmm)
    * Uses the Labelary API for previewing labels.

* https://github.com/PetrKudy/zebrabase
    * Not really sure what this is.


Non-python:

* Labelary.
* https://github.com/dpavlin/Printer-Zebra
    * Has information about printing issues that may occur on Windows.
    * Recommends setting printer up as Generic Text printer driver on Windows,
        and share it using `lpd`.

*


### Commercial apps:

* https://qz.io/
* https://www.easypost.com/printing-with-printnode
* https://docs.evolabel.com/index.html


## Utility tools for printing on Windows


* http://www.lerup.com/printfile




## Refs:


* https://stackoverflow.com/questions/12723818/print-to-standard-printer-from-python



"""


import os
import sys
import subprocess
import tempfile


def print_content(content, printer, method='print-cmd', job_description=None, verbose=0):
    """ Unified function to print content.

    Args:
        content: The content to print.
        printer: The printer to print on.
        method: String used to select the printing method to use.
        job_description: Job description, passed on to the printing method (if available).
        verbose: If verbose is larger than zero, debug information is printed to stderr.

    Returns:
        The result of the sub-function actually used to print.


    Examples:
        >>> print_content("Hej der", printer=)


    OBS: To see available printers on Windows from the command prompt, use one of these:
        `wmic printer get name`
        `wmic printer list brief`
        `wmic printer list full`


    """

    if not printer:
        raise ValueError("ERROR: `printer` argument must be specified in order to print. "
                         "You can use `wmic printer get name` to find the name of your label printer.")

    if printer[:2] != r"\\":
        print(f"\nWARNING: The given printer, {printer!r}, does not use a fully-qualified name. "
              f"This may not work. \n"
              r"The printer should typically be specified as '\\hostname\printername', e.g. "
              r"\\D34669\ZDesigner_ZD420-203dpi_ZPL or \\localhost\usb001_generic_text_printer. "
              "This typically requires you to share the printer as a network share.\n", file=sys.stderr)
    if " " in printer:
        print(f"\nWARNING: The given printer, {printer!r}, includes spaces. This may not work! "
              "Consider renaming the printer.\n", file=sys.stderr)

    if method is None:
        # Select good default Windows printing method:
        method = 'print-cmd'

    if method == 'win32print':
        if verbose:
            print(f"Printing {len(content)} {'characters' if isinstance(content, str) else 'bytes'} "
                  f"to printer {printer} using {method!r}...", file=sys.stderr)
        return print_raw_win32print(content, printer_name=printer, job_description=job_description)

    # Use a persistent tempfile for methods that require a file to work:
    if isinstance(content, str):
        is_binary = False
        mode = "w"
    else:
        is_binary = True
        mode = "wb"
    file = tempfile.NamedTemporaryFile(mode=mode, delete=False)
    file.write(content)
    file.close()
    if verbose:
        print(f"Printing {len(content)} {'chars' if isinstance(content, str) else 'bytes'} "
              f"in file '{file.name}' to printer '{printer}' using {method!r}...", file=sys.stderr)
    if method == 'print-cmd':
        return print_file_using_print_cmd(filename=file.name, printer_name=printer)
    if method == 'copy-cmd':
        return print_file_using_copy_cmd(filename=file.name, printer_name=printer, binary_mode=is_binary)


def print_raw_win32print(content, printer_name, job_description):
    """ Start a print job and send raw data to the printer.

    Args:
        content: The raw data to print.
        printer_name: The printer's name.
        job_description: A description of the job.

    Returns:
        None

    References:
        * http://timgolden.me.uk/python/win32_how_do_i/print.html
        * http://timgolden.me.uk/pywin32-docs/win32print.html
            Even Tim Golden recommends just calling `print <filename> /d:<printer>` on the shell.
        * https://docs.microsoft.com/en-us/windows/win32/printdocs/using-the-printing-functions
            (For C++ applications).
        * http://www.icodeguru.com/WebServer/Python-Programming-on-Win32/ch10.htm
    """
    import win32print
    p = win32print.OpenPrinter(printer_name)
    job = win32print.StartDocPrinter(p, 1, (job_description, None, "RAW"))
    win32print.StartPagePrinter(p)
    win32print.WritePrinter(p, content)
    win32print.EndPagePrinter(p)
    win32print.EndDocPrinter(p)
    win32print.ClosePrinter(p)


# def print_win32ui(content, printer_name, job_description):
#     """ Print using the win32ui module (from pywin32 project).
#
#     Args:
#         content:
#         printer_name:
#         job_description:
#
#     Returns:
#
#
#     Refs:
#         * http://timgolden.me.uk/pywin32-docs/win32ui.html
#         * https://www.oreilly.com/library/view/python-programming-on/1565926218/ch10s03.html
#
#     """
#     import win32ui
#     dc = win32ui.CreateDC()
#     dc.CreatePrinterDC()
#     dc.StartDoc(job_description)
#     dc.StartPage()
#     # Add content to page... not sure about this.
#     dc.TextOut(1, 1, 'Python Prints!')
#     dc.EndPage()
#     dc.EndDoc()
#     # I think this still just uses win32print to actually print the document.


def execute_and_process(cmd_args, capture_output=True, check=True, verbose=1):
    """ Execute shell command and process (utility function).

    Args:
        cmd_args:
        capture_output:
        check:
        verbose:

    Returns:

    """
    if verbose:
        print("Executing:", " ".join(cmd_args), file=sys.stderr)

    proc = subprocess.run(cmd_args, capture_output=capture_output)
    if proc.stderr:
        print("stderr output:", file=sys.stderr)
        print(proc.stderr)
    if proc.stdout:
        print("stdout output:", file=sys.stderr)
        print(proc.stdout)
    if check:
        proc.check_returncode()
    return proc


def print_file_using_copy_cmd(
        filename, printer_name, job_description=None,
        binary_mode=False, check=True, capture_output=True):
    """ Print file using the Windows `copy` command line function.
    Effectively:
        copy <file> <printer>

    Args:
        filename: The file to print.
        printer_name: The printer to print on.
            OBS: The printer must be fully-qualified.

    Returns:
        CompletedProcess

    If printing to USB printer, it will look something like this:

        copy /B <file> USB001:

    The above may not work, in which case you can share the printer
    and print to it as a network resource.

    Printing to network printer:

        copy /B <file> \\host\printer_name

    You can also mount network printers locally:

        net use lpt1: \\computername\printersharename /persistent:yes
        copy /B <file> lpt1:

    Note the colon after LPT1:

    """
    cmd_args = ["copy", filename, printer_name]
    if binary_mode:
        cmd_args.insert(1, "/b")
    return execute_and_process(cmd_args, check=check, capture_output=capture_output)


def print_file_using_print_cmd(
        filename, printer_name, job_description=None,
        check=True, capture_output=True):
    r""" Print file using the Windows `print` command line function.

    Args:
        filename: The file to print.
        printer_name: The printer to print on.
        job_description: Not used.

    Returns:
        CompletedProcess

    OBS: The print command has a file path limit of only 127 characters!

    Examples of using print command (confirmed working):

        print /D:"\\D34669\ZDesigner_ZD420-203dpi_ZPL" latest_label.zpl
        print latest_label.zpl /D:"\\D34669\ZDesigner_ZD420-203dpi_ZPL"
        print latest_label.zpl /D:"\\D34669\usb001_generic_text_printer"
        print latest_label.zpl /D:"\\localhost\usb001_generic_text_printer"

    Examples that did not work:

        print latest_label.zpl /D:"\\D34669\ZDesigner ZD420-203dpi ZPL"

    Conclusions:
        * It doesn't seem to matter if /d:printer is before or after the filename.
        * Printer name should not contain any spaces.
        * Printer should be shared, and you should specify fully qualified name including computer.



    Hmm, I'm getting errors:
        Unable to initialize device usb001_generic_text_printer
        Unable to initialize device ZDesigner ZD420-203dpi ZPL
    This is AFTER I've tried to send one print job (that didn't print).
        > print /d:"ZDesigner ZD420-203dpi ZPL" C:\Users\au206270\AppData\Local\Temp\tmpg78ojwv9
        C:\Users\au206270\AppData\Local\Temp\tmpg78ojwv9 is currently being printed


    """
    cmd_args = ["print", f"/d:{printer_name}", filename]
    return execute_and_process(cmd_args, check=check, capture_output=capture_output)


def print_file_using_lpr_cmd(
        filename, server=None, printer=None, classification=None, job_description=None,
        binary_mode=False, send_data_first=False, use_rlpr=False,
        check=True, capture_output=True):
    """ Print file using the Windows `lpr` command line program.

    Args:
        filename: File to print.
        server: Server providing the printer (optional).
        printer: The printer name to print on.
        classification: Print job classification.
        job_description: Print job description.
        binary_mode: Use binary mode when printing.
        check: Check if the print commmand completed properly.
        capture_output: Capture output from the print command.

    Returns:
        CompletedProcess object

    OBS: Filename/path is restricted to 127 characters max when using Windows' `lpr` command.

    Setting up an LPD/LPR printer on Windows:

    * https://github.com/dpavlin/Printer-Zebra
    * https://github.com/bbulpett/zebra-zpl
    * https://www.blackice.com/Help/Internet/BILPDManager/WebHelp/How_to_set_up_LPR_LPD_Printer_on_Windows_10_and_Windows_Server_2016.htm


    """
    if len(filename) >= 127:
        print("WARNING: filename is longer than 127 characters - lpr may not work on Windows.", file=sys.stderr)
    cmd_args = ["rlpr"] if use_rlpr else ["lpr"]
    if server:
        cmd_args.extend(["-S", server])
    if printer:
        cmd_args.extend(["-P", printer])
    if classification:
        cmd_args.extend(["-C", classification])
    if job_description:
        cmd_args.extend(["-J", job_description])
    if binary_mode:
        cmd_args.extend(["-o" "l"])
    if send_data_first:
        cmd_args.extend(["-d"])
    cmd_args.extend([filename])

    return execute_and_process(cmd_args, check=check, capture_output=capture_output)


def print_file_using_notepad_cmd(filename, check=True, capture_output=True):
    """ Print file using the Windows `print` command line function.

    Args:
        filename: The file to print.
        printer_name: The printer to print on.
        job_description: Not used.

    Returns:
        CompletedProcess

    """
    cmd_args = ["notepad", "/p", filename]
    return execute_and_process(cmd_args, check=check, capture_output=capture_output)





