
"""



"""
import os
import argparse
import requests
import yaml
import re
from urllib.parse import quote_plus  # quote does not quote/encode forward slash '/'
from urllib.parse import urljoin, urlsplit




def save_response_content(r, fpath):
    response_is_text = "text" in r.headers["content-type"].lower()
    try:
        with open(fpath, 'w' if response_is_text else 'wb') as fd:
            nbytes = fd.write(r.text if response_is_text else r.content)
    except UnicodeEncodeError:
        with open(fpath, 'wb') as fd:
            nbytes = fd.write(r.content)
    # print(" -", nbytes, "bytes written to file", fpath)
    return nbytes


def find_links(html, link_pat=r'href="([/\w-]+?([\w-]+.xlsx))"'):
    """
    file link example:
    <a href="/104/images/9/9a/IDT_order.xlsx" class="internal" title="IDT_order.xlsx">Media:IDT_order.xlsx</a>

    Default expression captures (link, filename) for all excel files.
    """
    if isinstance(link_pat, str):
        link_pat = re.compile(link_pat)
    # findall returns the capturing groups: (point, orderno) = ('qc/zip?SalesOrderNbr=11285499', '11285499')
    groups = link_pat.findall(html)
    return groups


def download_links(link_groups, session, baseurl, dl_directory=".", redownload_existing=False,
                   content_type_validator=lambda ct: None, max=None):
    """
    If require_csv is set to True (default), then only
    Note: If you get the wrong file type, check if your session is still valid.
    (They expire after about 15 minutes idle time...)

    Args:
        content_type_validator: A function(content_type). Return None if validation passes.
    """

    if dl_directory is None:
        dl_directory = "."

    if not os.path.exists(dl_directory):
        print("Creating download directory:", dl_directory)
        os.mkdir(dl_directory)
    elif not os.path.isdir(dl_directory):
        print("ERROR: %s exists but is not a directory, aborting...")
        return

    # Set to True to re-download for existing especs csv files that already exists in the folder
    print("Downloading CoA specs for {} orders".format(len(link_groups)))
    for i, (href, filename) in enumerate(link_groups, 1):
        print('File link found: %s, href="%s"' % (filename, href))
        # To download, use either the url_endpoint, or reconstitute the end-point using the orderno.
        fpath = os.path.join(dl_directory, quote_plus(filename.strip("=")))
        if os.path.exists(fpath):
            print("File already exists (skipping):", fpath)
            continue
        print("Downloading file {:03} of {:03}: {}".format(i, len(link_groups), filename))
        r = session.get(urljoin(baseurl, href))
        content_type = r.headers["content-type"].lower()

        content_type_error = content_type_validator(content_type)
        if content_type_error is not None:
            print("Content type ERROR:", content_type_error)
            continue

        print("Saving content (%s, %s bytes) to file: %s" % (
            r.headers["content-type"], len(r.text if "text" in content_type else r.content), fpath))
        nbytes = save_response_content(r, fpath)
        print(" - %s bytes written to file %s" % (nbytes, fpath))

        if max and i >= max:
            print("Max number of downloads has been reached, breaking...")
            break
    print("\nAll links downloaded OK!")


def get_cookies(args):
    # Note: All cookie keys and values must be strings or bytes, not e.g. ints.
    if args.get("open_id_session_id") is not None:
        cookies = {"open_id_session_id": args.get("open_id_session_id")}
    elif args.get("cookiefn") is not None:
        cookies = yaml.load(open(args['cookiefn']))
    else:
        cookies = yaml.load("""
    open_id_session_id: b5909b05197438fa89d1c409afdaefdb
    """)
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


def get_mainpage_html(args, session=None):
    """Get the HTML source with links:
    Note: In Chrome, you cannot simply click "view source" on the order page after you have adjusted "Number of Records" to 500.
    This will still only show you a page html with 15 results.
    Instead, open the developer console, mark the initial <html> element, right-click, copy to a text editor and save.

    :param args:
    :param session:
    :return:
    """
    if session is None:
        session = get_session(args)

    htmlfile = args.get("htmlfile")
    mainpage = args.get("mainpage", "https://lab.wyss.harvard.edu/shih/DFCI_Oligo_Plate_Log")
    save_htmlfile = args.get("save_htmlfile")

    if mainpage:
        assert mainpage.startswith("https://") or mainpage.startswith("http://")
        res = session.get(mainpage)
        res.raise_for_status()
        # print(res)
        html = res.text
        if save_htmlfile:
            if save_htmlfile is True:
                save_mainpage = urlsplit(mainpage).path.rsplit('/')[-1] + ".html"
            print("Saving mainpage to file:", save_htmlfile)
            with open(save_htmlfile, "w") as fd:
                fd.write(html)
    else:
        with open(htmlfile) as fd:
            print("Loading mainpage from file:", htmlfile)
            html = fd.read()
    return html


def parse_args(argv=None):
    """ Parse command line args. """

    parser = argparse.ArgumentParser()
    parser.add_argument("htmlfile")
    parser.add_argument("--mainpage", "-l")
    parser.add_argument("--cookiefile", "-c")
    parser.add_argument("--config", "-C")
    parser.add_argument("--overwrite", "-y", action="store_true")
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument("--outputdir", "-d")
    parser.add_argument("--save-htmlfile", "-s", action="store_true")

    return parser.parse_args(argv)


# Main entry point:
def main(args):
    """Download file links as specified by commmand line arguments."""

    if args is None:
        args = vars(parse_args())
    if args.get("config"):
        config = yaml.load(open(args["config"]))
        config.update(args)
        args = config

    # Create requests Session and load cookies:
    session = get_session(args)
    print("Session:")
    print(session)

    print("Mainpage html:")
    html = get_mainpage_html(args, session)
    print("\n\n\n")
    print(type(html))

    link_groups = find_links(html, None)
    print("link_groups:", link_groups)

    download_links(link_groups, session=session, baseurl=args.get("mainpage") or args["baseurl"])


# Ad-hoc testing:
def test(args=None):
    if args is None:
        args = {
            "baseurl": "https://lab.wyss.harvard.edu/",
            "mainpage": "https://lab.wyss.harvard.edu/shih/DFCI_Oligo_Plate_Log",
            # "htmlfile": "DFCI_Oligo_Plate_Log",
            "save_mainpage": True,
            "outputdir": "."
        }
    cookies = get_cookies(args)
    print("Cookies:")
    print(cookies)

    session = get_session(args)
    print("Session:")
    print(session)

    print("Mainpage html:")
    html = get_mainpage_html(args, session)
    print("\n\n\n")
    print(type(html))

    dl_directory = "."
    link_groups = find_links(html, None)
    print("link_groups:", link_groups)

    download_links(link_groups, session, args.get("mainpage") or args["baseurl"])
    # download_links(html, session, )


if __name__ == "__main__":
    # test()
    main()
