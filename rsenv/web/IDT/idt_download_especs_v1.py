#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2015 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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
##

# pylintxx: disable-msg=C0103,C0301,C0302,R0201,R0902,R0904,R0913,W0142,W0201,W0221,W0402
# pylint: disable=C0103




"""


1. Get the order history html:
	Go to IDT "order history" page, select 500 under "records per page",
	right-click somewhere in the table and select "Inspect element" (Chrome),
	right-click the <table> tag (or any parent) and select copy,
	paste the html content into a file and save it in your working directory,
	as e.g. orderhistory.html


2. Get login cookies:
	Open Chrome's advanced settings, go to manage cookies, search for idtdna,
	under the "www.idtdna.com" you will find some cookies,
	copy the cookies to a yaml file. It should look like the following:

ASP.NET_SessionId: (insert your value here)
IDTAUTH: (insert your value here)
LoginName: (insert your value here)

	and save the file to e.g. cookies.yaml


3. Copy idt_download_especs.py and idt_download_especs.bat to your working directory
	Or: have them available from a folder in your %PATH% (win) or $PATH (unix)
	Or: prefix/modify the commands below so you invoke the bat file.


4. Run idt_download_especs:

	$> idt_download_especs --cookiefile cookies.yaml orderhistory.html

	You can take a look at the available command line parameters by calling
	$> idt_download_especs --help


See also: espec_grep



## Early notes:

URLs:
  - https://www.idtdna.com/orderstatus/default.aspx?red=true
  -

The table data is downloaded mostly using jquery.
However, using Chrome's developer console, it should be possible to deduce what is going on.
Under "network", you can see the requests sent and responses received.
The requsts are always POST to /orderstatus/default.aspx?red=true,
with the data as form data.
The  __VIEWSTATE   parameter seems important, but also very extensive.
Also __VIEWSTATEGENERATOR:B2F56943

However, in the response, essentially what you are looking for is:
    QCZipDownload.ashx?SalesOrdNbr=4CNQKxxxxxxxXv94CD6nMA==     # Quality control link
      COADownload.ashx?SalesOrdNbr=4CNQKxxxxxxxXv94CD6nMA==     # Certificate of Analysis excel sheet
    /site/OrderStatus/OrderStatus/InvoiceDownload?salesOrdNbr=4CNQKxxxxxxxXv94CD6nMA=="     # Invoice

Full links:
    <a href="QCZipDownload.ashx?SalesOrdNbr=7FUU96xxxxxxxv94CD6nMA==">
        <img border="0" src="/images/icons/zip_icon.gif" /></a>
    <a href="COADownload.ashx?SalesOrdNbr=7FUU96RvhPAiXv94CD6nMA==">
        <img border="0" src="/images/icons/excel_icon.gif" /></a>


Perhaps instead of trying to communicate with the site, just go to the order history page in your browser of choice,
set the "Records per page" to 500 and download/save the page as html. Then process the html for the links.


"""

#import sys
import os
import requests
import argparse
import yaml
#import json
import re
#import base64
from urllib.parse import quote_plus # quote does not quote/encode forward slash '/'


# Constants and regex patterns:
# http://pythex.org/ is gold
# The SalesOrdNbr can contain '/', e.g. "/Pj6lxxxxxxxXv94CD6nMA=="
qc_pat = re.compile(r'href="(QCZipDownload.ashx\?SalesOrdNbr=([\w=\/]+))"')
coa_pat = re.compile(r'href="(COADownload.ashx\?SalesOrdNbr=([\w=\/]+))"')
idt_baseurl = " https://www.idtdna.com/"
orderstatus_base = "https://www.idtdna.com/orderstatus/"
qc_endpoint = "https://www.idtdna.com/orderstatus/QCZipDownload.ashx"
coa_endpoint = "https://www.idtdna.com/orderstatus/COADownload.ashx"


def get_html(args):
    """
    Read html from htmlfile.
    Note: You cannot simply click "view source" in chrome on the order page
    after you have adjusted "Number of Records" to 500.
    This will still only show you a page html with 15 results.
    Instead, open the developer console, mark the initial <html> element,
    right-click, copy to a text editor and save.
    """
    #htmlfile = "www.idtdna.com_orderstatus_default.aspx.html-only.html"
    #htmlfile = "idt_orderstatus_all-129.html"
    htmlfile = args.htmlfile
    with open(htmlfile) as fd:
        html = fd.read()
    return html


def ensure_outputdir(args):
    """ Ensure that outputdir exists. """
    if not args.outputdir:
        args.outputdir = "."
        return True
    especs_folder = os.path.join(".", args.outputdir)
    if not os.path.exists(especs_folder):
        print("Creating folder:", os.path.abspath(especs_folder))
        os.mkdir(especs_folder)
    return True


def get_session(args):
    """ Load cookies and return session. """
    session = requests.Session()
    if args.cookiefile:
        cookies = yaml.load(open(args.cookiefile))
        session.cookies.update(cookies)
    return session


def download_especs(args):
    """ Download especs from IDT website. """
    html = get_html(args)
    session = get_session(args)
    ensure_outputdir(args)
    # list of (point, orderno) tuples:
    groups = qc_pat.findall(html)
    # Set to True to re-download for existing especs csv files that already exists in the folder
    print("Downloading CoA specs for {} orders".format(len(groups)))
    for i, (_, orderno) in enumerate(groups, 1):
        fpath = os.path.join(args.outputdir, quote_plus(orderno.strip("=")) + ".csv")
        if os.path.exists(fpath):
            print("Especs already exists for order:", orderno)
            if args.overwrite:
                print(" - Overwriting with updated espec file...")
            else:
                print(" - Skipping...")
                continue
        params = {"SalesOrdNbr": orderno} # # params are sent in the query string; data or json is sent in the body
        print("Downloading CoA especs csv for order", orderno, "({} of {})".format(i, len(groups)))
        r = session.get(coa_endpoint, params=params)
        print("Saving especs to file:", fpath)
        # 11073833 => "7FUU96RvhPAiXv94CD6nMA=="   # Not really sure how that conversion is done...
        with open(fpath, 'w') as fd:
            nbytes = fd.write(r.text)
        print(" -", nbytes, "bytes written to file", fpath)


def parse_args(argv=None):
    """ Parse command line args. """

    parser = argparse.ArgumentParser()
    parser.add_argument("htmlfile")
    parser.add_argument("--cookiefile", "-c")
    parser.add_argument("--overwrite", "-y")
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument("--outputdir", "-d")
    return parser.parse_args(argv)



def main(argv=None):
    """ main function. """
    argsns = parse_args(argv)
    download_especs(argsns)



if __name__ == '__main__':
    main()
