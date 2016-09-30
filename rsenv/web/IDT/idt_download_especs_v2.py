
"""


Update: IDT has switched to a completely javascript based frontend.
Orderstatus no longer holds the links directly.
Parsing/simulating the javascript here is tedious.
But, you can just load the orderstatus page manually in a browser, click get source,
and save the html to a file.
Then search for something like:
<a target="_self" data-bind="attr: { href: COA }" class="fa fa-file-excel-o" href="/site/OrderStatus/specs/coa?SalesOrdNbr=11769778">&nbsp;<span style="font-family:sans-serif;" onclick="TrackPageEvent('Document Download', 'COA')">COA</span></a>


See RS359i


 How to download:
------------------

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


3. Copy idt_download_especs_v2.py and idt_download_especs.bat to your working directory
    Or: have them available from a folder in your %PATH% (win) or $PATH (unix)
    Or: prefix/modify the commands below so you invoke the bat file.


4. Run idt_download_especs:

    $> idt_download_especs --cookiefile cookies.yaml orderhistory.html

    You can take a look at the available command line parameters by calling
    $> idt_download_especs --help


See also: espec_grep


TODO: Consolidate with idt_download_especs_v2.py script in RsUtils python package!


"""
import sys
import os
import re
import argparse
from urllib.parse import quote_plus  # quote does not quote/encode forward slash '/'
from urllib.parse import urljoin
import requests
import yaml


def get_directories(args):
    # Specify folder for especs files, creating it if needed:
    especs_folder = os.path.abspath(os.path.join(".", "especs"))
    qc_folder = os.path.abspath(os.path.join(".", "qc_files"))
    if not os.path.exists(especs_folder):
        print("Creating folder:", os.path.abspath(especs_folder))
        os.mkdir(especs_folder)

    if not os.path.exists(qc_folder):
        print("Creating folder:", os.path.abspath(qc_folder))
        os.mkdir(qc_folder)
    print("Downloading especs to folder: %s" % especs_folder)
    print("Downloading qc files to folder: %s" % especs_folder)
    return especs_folder, qc_folder


def get_link_patterns():
    """
    """
    ## Specify regex patterns to parse the file.
    # http://pythex.org/ is gold
    # The SalesOrdNbr can contain '/', e.g. "/Pj6lkN8o3oiXv94CD6nMA=="

    # COA url example: href="/site/OrderStatus/specs/coa?SalesOrdNbr=11769778"  # These are currently the ones you want
    return dict(
        # Note: For qc_pat the keyword is "SalesOrderNbr", but for coa_pat it is "SalesOrdNbr".
        qc_pat=re.compile(r'href="(qc\/zip\?SalesOrderNbr=([\w=\/]+))"', re.MULTILINE),
        coa_pat=re.compile(r'href="(specs\/coa\?SalesOrdNbr=([\w=\/]+))"'),
        invoice_pat=re.compile(r'href="(\/site\/OrderStatus\/OrderStatus\/InvoiceDownloadRaw\?SalesOrdNbr=([\w=\/]+))"')
    )


def save_response_content(r, fpath):
    response_is_text = "text" in r.headers["content-type"].lower()
    try:
        with open(fpath, 'w' if response_is_text else 'wb') as fd:
            nbytes = fd.write(r.text if response_is_text else r.content)
    except UnicodeEncodeError:
        with open(fpath, 'wb') as fd:
            nbytes = fd.write(r.content)
    print(" -", nbytes, "bytes written to file", fpath)
    return nbytes


def download_coa(orderstatus_html, session, dl_directory=None, redownload_existing=False, require_csv=True, max=None):
    """
    If require_csv is set to True (default), then only
    Note: If you get the wrong file type, check if your session is still valid.
    (They expire after about 15 minutes idle time...)
    """
    if not os.path.exists(dl_directory):
        print("Creating CoA download directory:", dl_directory)
        os.mkdir(dl_directory)
    elif not os.path.isdir(dl_directory):
        print("ERROR: %s exists but is not a directory, aborting...")
        return
    # coa_pat = re.compile(r'href="(specs\/coa\?SalesOrdNbr=([\w=\/]+))"') # Notice: SalesOrdNbr, not SalesOrderNbr.
    # coa_pat = re.compile(r'href="([/\w]*specs\/coa\?SalesOrdNbr=([\w=\/]+))"') # Notice: SalesOrdNbr, not SalesOrderNbr.
    coa_pat = re.compile(r'href="([/\w-]*specs\/coa\?SalesOrdNbr=([\w=\/]+))"') # Notice: SalesOrdNbr, not SalesOrderNbr.

    orderstatus_baseurl = "https://www.idtdna.com/site/OrderStatus/orderstatus"
    # COA url example: href="/site/OrderStatus/specs/coa?SalesOrdNbr=11769778"  # These are currently the ones you want

    # findall returns the capturing groups: (point, orderno) = ('qc/zip?SalesOrderNbr=11285499', '11285499')
    groups = coa_pat.findall(orderstatus_html)
    # Set to True to re-download for existing especs csv files that already exists in the folder
    print("Downloading CoA specs for {} orders".format(len(groups)))
    n_saved = 0
    for i, (url_endpoint, orderno) in enumerate(groups, 1):
        print("CoA link found: %s (orderno. %s)" % (url_endpoint, orderno))
        # To download, use either the url_endpoint, or reconstitute the end-point using the orderno.
        fpath = os.path.join(dl_directory, quote_plus(orderno.strip("=")) + ".csv")
        if os.path.exists(fpath):
            print("Especs already exists for order:", orderno)
            continue
        print("Downloading CoA especs csv for order", orderno, "({} of {})".format(i, len(groups)))
        #params = {"SalesOrdNbr": orderno} # # params are sent in the query string; data or json is sent in the body
        #r = session.get(coa_endpoint, params=params)
        r = session.get(urljoin(orderstatus_baseurl, url_endpoint)) # Using the url_endpoint, relative to orderstatus_baseurl
        content_type = r.headers["content-type"].lower()
        response_is_text = "text" in content_type
        response_is_csv = "csv" in content_type
        print("Saving especs (%s, %s lines) to file: %s" %
              (r.headers["content-type"], len(r.text.split("\n")) if response_is_text else "?", fpath))
        if not response_is_csv:
            print("WARNING: Response is not csv! (%s - status %s)" % (r.headers["content-type"], r.status_code))
        # 11073833 => "7FUU96RvhPAiXv94CD6nMA=="   # Not really sure how that conversion is done...
        if response_is_csv or not require_csv:
            nbytes = save_response_content(r, fpath)
            n_saved += 1
        if max and i >= max:
            print("Max number of downloads has been reached, breaking...")
            break
        print(" - ")
    print("\n\nDone! - %s files saved to folder %s\n\n" % (n_saved, dl_directory))

#
# def download_qc(html, redownload_existing=False, require_zip=True, break_if_html=False):
#     # findall returns the capturing groups: (point, orderno) = ('qc/zip?SalesOrderNbr=11285499', '11285499')
#     groups = qc_pat.findall(html)
#     # Set to True to re-download for existing especs csv files that already exists in the folder
#     print("Downloading QC files for {} orders".format(len(groups)))
#     for i, (url_endpoint, orderno) in enumerate(groups, 1):
#         # To download, use either the url_endpoint, or reconstitute the end-point using the orderno.
#         fpath = os.path.join(qc_folder, quote_plus(orderno.strip("=")) + ".zip")
#         if os.path.exists(fpath):
#             print("Especs already exists for order:", orderno)
#             continue
#         print("Downloading CoA especs csv for order", orderno, "({} of {})".format(i, len(groups)))
#         #params = {"SalesOrdNbr": orderno} # # params are sent in the query string; data or json is sent in the body
#         #r = session.get(coa_endpoint, params=params)
#         r = session.get(urljoin(orderstatus_baseurl, url_endpoint)) # Using the url_endpoint, relative to orderstatus_baseurl
#         content_type = r.headers["content-type"].lower()
#         response_is_text = "text" in content_type
#         response_is_zip = "zip" in content_type
#         print("Saving QC info (%s, %s lines) to file: %s" % (r.headers["content-type"],
#                                                             len(r.text.split("\n")) if response_is_text else "?",
#                                                             fpath))
#         if response_is_text:
#             # QC files should be zips, not text. Something is probably wrong, we may only have a temp file:
#             new_fn = os.path.join(qc_folder, quote_plus(orderno.strip("=")) + ".txt")
#             print("Changing filename: %s -> %s" % (fpath, new_fn))
#             fpath = new_fn
#         # 11073833 => "7FUU96RvhPAiXv94CD6nMA=="   # Not really sure how that conversion is done...
#         if "html" in content_type:
#             print("WARNING - Response (%s) is %s:" % (r.status_code, content_type))
#             print(r.text)
#             if break_if_html:
#                 break
#         elif not response_is_zip:
#             print("WARNING: Response is not zip! (%s - status %s)" % (content_type, r.status_code))
#         # 11073833 => "7FUU96RvhPAiXv94CD6nMA=="   # Not really sure how that conversion is done...
#         if require_zip and not response_is_zip:
#             print("- Response content type must be zip; not saving...")
#         else:
#             nbytes = save_response_content(r, fpath)
#         print(" - ")
#     print("Done!")


def get_cookies(args):
    """
    The cookie file is yaml formatted dict with the following entries:
        ASP.NET_SessionId: nudyatxxxxxxxxxxxxxxtmft
        IDTAUTH: 0AFA7..................2D6
        LoginName: zSLxxxxxxxxxxxxxxxxxPE/hxxxxxQ==
        # These are not needed to download files, but are required to retrieve the orderstatus page:
        Country: CN=US&DateSet=6/6/2016 11:49:36 PM
        PagesAff: 2d08fa...............e47
        liveagent_oref: ''
        liveagent_ptid: xxxxx-xxxx-xxx-xxxx-xxxxxxxxxxxxxxx
        liveagent_sid: xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxxxx
        liveagent_vc: '2'
    """
    cookie_file = args.get("cookiefile", "idt_cookies.yaml")
    cookies = yaml.load(open(cookie_file))
    return cookies


def get_session(args):
    """Create session object.
    :param args:
    :return: session object with cookies from args if available.
    """

    print("Creating new session object...")
    session = requests.Session()
    try:
        cookies = get_cookies(args)
    except KeyError:
        pass
    else:
        print("Updating session cookies with")
        print(cookies)
        session.cookies.update(cookies)

    return session


def retrieve_orderstatus_page(args, session=None):
    """
    Update: IDT has switched to a completely javascript based frontend for orderstatus page.
    Orderstatus no longer holds the links directly.
    Parsing/simulating the javascript here is tedious.
    But, you can just load the orderstatus page manually in a browser, click get source,
    and save the html to a file.
    Then search for something like:
    <a target="_self" data-bind="attr: { href: COA }" class="fa fa-file-excel-o"
    href="/site/OrderStatus/specs/coa?SalesOrdNbr=11769778">&nbsp;<span style="font-family:sans-serif;"
    onclick="TrackPageEvent('Document Download', 'COA')">COA</span></a>

    :param args: dict with config
    :param session: a requests session.
    :return: The response text (html).
    """
    if session is None:
        session = get_session(args)

    orderstatus_url = "https://www.idtdna.com/site/OrderStatus/orderstatus"

    res = session.get(orderstatus_url)
    res.raise_for_status()
    print(res)
    return res.text


def parse_args(argv=None):
    """ Parse command line args. """

    parser = argparse.ArgumentParser()
    parser.add_argument("htmlfile")
    parser.add_argument("--cookiefile", "-c")
    parser.add_argument("--overwrite", "-y", action="store_true")
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument("--outputdir", "-d")
    return parser.parse_args(argv)


def main(args=None):
    """
    # URLs:
    idt_baseurl = " https://www.idtdna.com/"
    # orderstatus_base = "https://www.idtdna.com/orderstatus/"
    orderstatus_baseurl = "https://www.idtdna.com/site/OrderStatus/orderstatus"
    qc_endpoint = urljoin(orderstatus_baseurl, "qc/zip")  # https://www.idtdna.com/site/OrderStatus/qc/zip
    coa_endpoint = urljoin(orderstatus_baseurl, "specs/coa")  # https://www.idtdna.com/site/OrderStatus/specs/coa
    invoice_endpoint = urljoin(orderstatus_baseurl, "OrderStatus/InvoiceDownloadRaw")

    """

    if args is None:
        argsns = parse_args()
        args = vars(argsns)

    # Create requests Session and load cookies:
    session = get_session(args)
    print("\nCreating session...")
    print(session)

    print("\nLoading order status html...")
    htmlfile = args.get("htmlfile") or "orderstatus.html"
    if args.get("retrieve_orderstatus"):
        print("retrieve_orderstatus not yet implemented.")
        orderstatus_html = retrieve_orderstatus_page(args, session)
        print(orderstatus_html)
        with open(htmlfile, 'w') as fd:
            fd.write(orderstatus_html)
    else:
        with open(htmlfile) as fd:
            orderstatus_html = fd.read()

    dl_directory = os.path.abspath(args.get("outputdir") or os.path.join(".", "CoA"))
    print("Downloading CoA spec files to directory '%s'" % (dl_directory, ))
    download_coa(orderstatus_html, session, dl_directory=dl_directory)


def test(args=None):
    if args is None:
        args = {}
    cookies = get_cookies(args)
    print("Cookies:")
    print(cookies)

    session = get_session(args)
    print("Session:")
    print(session)

    print("Order status html:")
    use_orderstatus_file = True
    if use_orderstatus_file:
        with open("orderstatus.html", 'r') as fd:
            orderstatus_html = fd.read()
    else:
        orderstatus_html = retrieve_orderstatus_page(args, session)
        print(orderstatus_html)
        with open("orderstatus.html", 'wr') as fd:
            fd.write(orderstatus_html)

    dl_directory = os.path.abspath(os.path.join(".", "CoA"))
    download_coa(orderstatus_html, session, dl_directory=dl_directory)




if __name__ == "__main__":
    if "--test" in sys.argv:
        test()
    else:
        main()
