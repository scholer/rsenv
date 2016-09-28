#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.



## Common ids:
## - projects spaceid: 589826


def getFilepathFromIds(spaceid, pageid=None, attachmentid=None):
    folders = list()
    folders.append('ver003')                       # Level 1
    folders.append((spaceid % 1000) % 250 )        # Level 2
    folders.append((spaceid/1000) % 250 )          # Level 3
    folders.append(spaceid)                        # Level 4
    if pageid:
        folders.append((pageid % 1000) % 250)           # Level 5
        folders.append((pageid % 1000000)/1000 % 250)  # Level 6
        folders.append(pageid)                         # Level 7
        if attachmentid:
            folders.append(attachmentid)                   # Level 8

        # actual file name is <file-version>.<file-extension>

    path = "/".join([str(folder) for folder in folders])
    return path


def wikipagenamefromurl(source=None):
    if source is None:
        source = gtk.clipboard_get().wait_for_text()
    print(("wikipagenamefromurl(): source is : '" + source + "'"))
    print('source.strip().rsplit("/",1)[1].replace("+"," ")')
    try:
        ret = source.strip().rsplit("/", 1)[1].replace("+", " ")
        print(ret)
        return ret
    except IndexError:
        print(("IndexError: " + str(source.strip().split("/"))))



def tabTableToWikiMarkup(text=None, delimiter="\t", doprint=True):
    print("tabTableToWikiMarkup(), HINT: give ',' as second argument to delimit by comma instead of tab.")
    print("tabTableToWikiMarkup(), HINT: if no text is given, I will use clipboard (and replace!)")
    print('tabTableToWikiMarkup(), ONE-LINER: text.replace("\t","| ").replace("\n","|\n|").replace("|a|","|sample|")')

    clipboard = None
    # Perhaps do a linux test:
    if text is None:
        try:
            import gtk
            import gobject
            clipboard = gtk.clipboard_get()
            text = clipboard.wait_for_text()
            print("Text from clipboard: ")
            print(text)
        except ImportError:
            print("tabTableToWikiMarkup() : Clipboard not available (currently only implemented with gtk). You must input a text string as first argument.")
            return
    wiki = "|" + text.replace("\t", "| ").replace("\n", "|\n|").replace("|a|", "|sample|")+" |"
    if clipboard:
        clipboard.set_text(wiki)
        # This is required to persist X11 clipboard data after process termination:
        # http://stackoverflow.com/questions/15241203/effect-of-pygtk-clipboard-set-text-persists-only-while-process-is-running
        # Alternatively, use
        # gtk.get_clipboard().set_can_store(["UTF8_STRING", 0, 0]),
        # gtk.get_clipboard().store()
        gobject.timeout_add(100, gtk.main_quit)
        gtk.main()
    if doprint:
        if clipboard:
            print("Clipboard now contains:")
            print(wiki)
        else:
            print(wiki)

    return wiki



if __name__ == "__main__":
    path = getFilepathFromIds(589826, 2392080, 2883585)
    print(path)

    text = """Sample	A (AU/mm)	e (AU/mm/mM)	Conc (uM)	Vol (ul)	nmol	Input	Yield%
RS128c-b1 E2-3 (1:5 dilution)	0.298	1.3	1,146.00	50	57.30	90.00	64%
RS128c-b1 E9-10 (1:5 dilution)	0.193	1.3	742.00	50	37.10	90.00	41%
RS128c-b2 E8-10 (1:5 dilution)	0.409	1.3	1,573.00	50	78.65	85.00	93%
RS128c-b3 E11-12 (1:5 dilution)	0.478	1.3	1,838.00	50	91.90	200.00	46%
RS128c-b4 F11-10 (1:2 dilution)	0.15	0.71	423.00	20	8.46	35.00	24%"""
    print(text)
    tabTableToWikiMarkup()
