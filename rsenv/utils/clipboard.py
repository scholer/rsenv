#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright 2014-2018 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

Module for interacting with the OS clipboard.

Possible options for working with the clipboard:

* tkinter           cross-platform, starts a brief Tk GUI.
* Qt                cross-platform, starts a brief Qt GUI.
* pygtk             Linux, using GTK.
* Xerox             cross-platform. Requires win32 module. https://github.com/kennethreitz/xerox
* richxerox         https://pypi.python.org/pypi/richxerox
* pyperclip         cross-platform  Uses Ctypes (windows) or subprocess. https://github.com/asweigart/pyperclip
* win32clipboard    windows
* AppKit            Mac


Qt example:
    # from https://www.daniweb.com/software-development/python/threads/422292/getclipboarddata#post1802945
    from PySide.QtGui import QApplication
    app = QApplication([])
    clipboard = app.clipboard()
    text = clipboard.text()  # gets clipboard
    app.processEvents()  # Is required to avoid hanging...


Xerox:
    On Mac, uses `pbcopy` and `pbpaste` via `subprocess.Popen()` to read/write to/from the clipboard.
    This would not work for binary inputs.
    On Windows uses pywin32/win32clipboard.
    Also has tkinter-based copy/paste which it falls back to on windows if pywin32 is not available.

richxerox:
    Extension of Xerox to provide multiple formats other than text (rtf, html).
    https://bitbucket.org/jeunice/richxerox
    Uses pyobjc AppKit.NSPasteboard


pyperclip:
    "Currently only handles plaintext."
    On Windows, uses Ctypes, no additional modules are needed.
    On Mac, this module makes use of the pbcopy and pbpaste commands, which should come with the os.
    On Linux, this module makes use of the xclip or xsel commands, which should come with the os.
    Can also use `qdbus org.kde.klipper` via `subprocess`, or use Qt or gtk.
    OBS: Is used by Pandas for reading/writing from/to clipboard.


AppKit from the pyobjc package (Mac):
    1. Install pyobjc:
        pip install pyobjc
        conda install -c conda-forge pyobjc-core  # core is not enough, you need the full package.


    NOT THIS: http://nitipit.github.io/appkit/
    AppKit.NSPasteboard provides functions for interacting with the macOS pasteboard server.
    https://developer.apple.com/documentation/appkit/nspasteboard
    https://stackoverflow.com/questions/7083313/python-get-mac-clipboard-contents
    https://genbastechthoughts.wordpress.com/2012/05/20/reading-urls-from-os-x-clipboard-with-pyobjc/
    http://blog.carlsensei.com/post/88897796
    http://www.macdrifter.com/2011/12/python-and-the-mac-clipboard.html (old)


Carbon (Mac):
    http://blog.carlsensei.com/post/88897796
    Carbon.Scrap.ClearCurrentScrap()
    Carbon.Scrap.GetCurrentScrap().PutScrapFlavor('TEXT', 0, arg)
    Carbon.Scrap.GetCurrentScrap().GetScrapFlavorData('TEXT')


Other:

    Pythonista iOS Python IDE has a clipboard module that can read image data:
    http://omz-software.com/pythonista/docs/ios/clipboard.html
    https://github.com/Pythonista-Tools has extra scripts but not actually source

    Pillow has an `ImageGrab` module (Mac, Windows) that can be used to grab image data from clipboard.
    Uses `osascript` (AppleScript) to write clipboard image data to file.
    https://github.com/python-pillow/Pillow/blob/master/PIL/ImageGrab.py



Regarding multiple clipboards and data:
* Most OS'es have multiple clipboards.
* In many OS'es, the clipboard can also contain different data types, sometimes simultaneously.


"""
from rsenv.fileutils.fileutils import get_next_unused_filename

import os
import sys
import click
import inspect

try:
    from tkinter import Tk
except ImportError:
    from tkinter import Tk

# Clipboard in GTK:
try:
    import pygtk
    pygtk.require('2.0')
    import gtk # gtk provides clipboard access:
    # clipboard = gtk.clipboard_get()
    # text = clipboard.wait_for_text()
except ImportError:
    # Will happen on Windows/Mac:
    pass

# win32clipboard:
try:
    import win32clipboard
    print("win32clipboard is available.")
except ImportError:
    pass

# pyperclip:
try:
    import pyperclip
    print("pyperclip is available.")
except ImportError:
    # check for import with
    # globals(), locals(), vars() or sys.modules.keys()
    #>>> if 'pyperclip' in sys.modules.keys()
    pass

# xerox:
try:
    import xerox
except ImportError:
    pass


def set_clipboard(text, datatype=None):
    """
    Arg datatype currently not used. Will generally assumed to be unicode text.
    From http://stackoverflow.com/questions/579687/how-do-i-copy-a-string-to-the-clipboard-on-windows-using-python
    """
    if 'xerox' in list(sys.modules.keys()):
        xerox.copy(text)
    elif 'pyperclip' in list(sys.modules.keys()):
        pyperclip.copy(text)
    elif 'gtk' in list(sys.modules.keys()):
        clipboard = gtk.clipboard_get()
        text = clipboard.set_text(text)
    elif 'win32clipboard' in list(sys.modules.keys()):
        wcb = win32clipboard
        wcb.OpenClipboard()
        wcb.EmptyClipboard()
        # wcb.SetClipboardText(text)  # doesn't work
        # SetClipboardData Usage:
        # >>> wcb.SetClipboardData(<type>, <data>)
        # wcb.SetClipboardData(wcb.CF_TEXT, text.encode('utf-8')) # doesn't work
        wcb.SetClipboardData(wcb.CF_UNICODETEXT, str(text)) # works
        wcb.CloseClipboard() # User cannot use clipboard until it is closed.
    else:
        # If code is run from within e.g. an ipython qt console, invoking Tk root's mainloop() may hang the console.
        r = Tk()
        # r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.mainloop() # the Tk root's mainloop() must be invoked.
        r.destroy()


def get_clipboard():
    """
    Get content of OS clipboard.
    """
    if 'xerox' in list(sys.modules.keys()):
        print("Returning clipboard content using xerox...")
        return xerox.paste()
    elif 'pyperclip' in list(sys.modules.keys()):
        print("Returning clipboard content using pyperclip...")
        return pyperclip.paste()
    elif 'gtk' in list(sys.modules.keys()):
        print("Returning clipboard content using gtk...")
        clipboard = gtk.clipboard_get()
        return clipboard.wait_for_text()
    elif 'win32clipboard' in list(sys.modules.keys()):
        wcb = win32clipboard
        wcb.OpenClipboard()
        try:
            data = wcb.GetClipboardData(wcb.CF_TEXT)
        except TypeError as e:
            print(e)
            print("No text in clipboard.")
        wcb.CloseClipboard()  # User cannot use clipboard until it is closed.
        return data
    else:
        print("locals.keys() is: ", list(sys.modules.keys()).keys())
        print("falling back to Tk...")
        r = Tk()
        r.withdraw()
        result = r.selection_get(selection="CLIPBOARD")
        r.destroy()
        print("Returning clipboard content using Tkinter...")
        return result


# Aliases:
copy = set_clipboard
paste = get_clipboard


def addToClipBoard_windows(text):
    """
    This uses the external 'clip' program to add content to the windows clipboard by invoking:
        >>> echo <text> | clip
    Example:
        >>> addToClipBoard('penny lane')

    """
    command = 'echo ' + text.strip() + '| clip'
    os.system(command)


def copy_file_to_clipboard(fd):
    """
    Copies the content of open file <fd> to clipboard.
    If fd is a string it is assumed that you want to
    open that file and read its content into the clipboard.
    Usage:
    >>> myfd = open('/path/to/a/textfile.txt')
    >>> copy_file_to_clipboard(myfd)
    Shortcut:
    >>> copy_file_to_clipboard('/path/to/a/textfile.txt')
    >>> content = get_clipboard() # returns content of file.
    """
    if isinstance(fd, str):
        fd = open(fd)
    set_clipboard(fd.read())


def clipboard_image_to_file(
        filename=None, fnpattern="{prefix}_{i:03}.{ext}",
        prefix="image", ext='png',
        quiet=False, verbose=0
):
    """Save clipboard image data to file.

    Args:
        filename: An exact filename to export to. Will overwrite exisitng files if they exists.
        fnpattern: Instead of specifying a precise filename, it may be desirable to specify a *pattern*,
            e.g. image_001.png, image_002.png, etc. This may be achieved by through this parameter which is just a
            python format string, with variables such as `i` and `date`, e.g. "image_{i:03}.png".
            See `utils.fileutils.get_next_unused_filename()` for more info.
        prefix: Used to generate filename from pattern, see `.fileutils.get_next_unused_filename()`.
        ext: Used to generate filename from pattern, see `.fileutils.get_next_unused_filename()`.

    Returns:
        filename of the exported image file.

    """
    import PIL.ImageGrab

    if filename is None:
        filename = get_next_unused_filename(fnpattern, prefix=prefix, ext=ext)

    img = PIL.ImageGrab.grabclipboard()
    if img is None:
        print("WARNING: No image data in clipboard, aborting.")
        return
    # PIL.ImageGrab.grabber only on win32.
    if not quiet:
        print(f"Saving image ({img.width} x {img.height} pixels) to file: {filename}")
    img.save(filename)
    if not quiet:
        print(" - done! ({} bytes)".format(os.path.getsize(filename)))
    return filename


clipboard_image_to_file_cli = click.Command(
    callback=clipboard_image_to_file,
    name=clipboard_image_to_file.__name__,
    help=inspect.getdoc(clipboard_image_to_file),
    params=[
        click.Option(['--fnpattern', '-f'], default="{prefix}_{i:03}.{ext}"),
        click.Option(['--prefix'], default="image"),  # remember: param_decls is a list, *decls.
        click.Option(['--ext'], default="png"),
        click.Option(['--verbose', '-v'], count=True),
        click.Option(['--quiet/--no-quiet']),
        click.Argument(['filename'], required=False)
])


