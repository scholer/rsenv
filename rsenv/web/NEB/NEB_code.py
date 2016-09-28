
# Copyright 2015 Rasmus Sorensen

# pylint: disable=C0103

"""
Resources:

NEB:
* http://nc2.neb.com/NEBcutter2/cutshow.php?name=63ca7b3d-

* https://www.neb.com/tools-and-resources/interactive-tools/enzyme-finder
https://www.neb.com/sitecore/content/nebsg/home/tools-and-resources/selection-charts/time-saver-qualified-restriction-enzymes
https://www.neb.com/tools-and-resources/usage-guidelines/nebuffer-performance-chart-with-restriction-enzymes
https://www.neb.com/tools-and-resources/selection-charts/alphabetized-list-of-recognition-specificities
http://www.neb.uk.com/Product_Overview/high_fidelity.asp
https://www.neb.com/tools-and-resources/interactive-tools/enzyme-finder?searchType=9  # HF Restriction Endonucleases



asyncio refs:
* http://compiletoi.net/fast-scraping-in-python-with-asyncio.html
* http://aiohttp.readthedocs.org/
* https://docs.python.org/3/library/asyncio.html
* https://docs.python.org/3/library/asyncio-task.html
* https://www.youtube.com/watch?v=9WV7juNmyE8
* http://stackoverflow.com/questions/22190403/how-could-i-use-requests-in-asyncio
* http://geekgirl.io/concurrent-http-requests-with-python3-and-asyncio/
* https://glyph.twistedmatrix.com/2014/02/unyielding.html

"""

import sys
import os
import pickle
import requests
from requests.structures import CaseInsensitiveDict
from bs4 import BeautifulSoup
import logging
logger = logging.getLogger(__name__)



def init_logging(level=logging.INFO):
    """ Initialize logging. """
    logging.basicConfig(level=level)


def parse_row(row, td='td'):
    """
    Return a list of cells in the html row.
    Set td='th' to parse headers
    """
    #cells = row.findAll('td')
    find = td
    return [td.text for td in row.findAll(find)]

def table_to_dict_list(table, dict=dict):
    """
    Convert table to list of dicts.
    Set cls=OrderedDict to use an ordereddict.
    """
    rows = table.findAll('tr')
    header = parse_row(rows[0], td='th')
    #print("Header: ", header)
    data = [dict(zip(header, parse_row(row))) for row in rows[1:]]
    return data

def product_table(entry, name=None, url=None):
    """
    Entry can be 'r0137-alui',
    or entry can be just "r0137" and then name='alui'
    Returns a list of dicts, where each dict is a row in the product table, e.g.
    [
     {"Catalog #": "R0137S", "Size": "1,000 units", "Price": "$64.00", "Concentration": "10,000 units/ml"},
     {"Catalog #": "R0137L", "Size": "5,000 units", "Price": "$258.00", "Concentration": "10,000 units/ml"}
    ]
    """
    if url:
        pass
    elif entry[:4].lower() == 'http':
        url = entry
    if name:
        entry = "-".join((entry, name))
    if not url:
        url = "https://www.neb.com/products/" + entry
    r = requests.get(url)
    if not r:
        print(r)
        return None
    soup = BeautifulSoup(r.text)
    table = soup.find("table", {'class': "items add-to-cart-list"})
    return table_to_dict_list(table)

def price_repr(row):
    """ Produce a represenatitve price for product table row/rows. """
    if isinstance(row, list):
        # Passed in a list of rows. Use the first.
        row = row[0]
    return "%s/%s" % tuple(row[k] for k in ('Price', 'Size'))


def unit_price(row):
    """ Produce a represenatitve price for product table row/rows. """
    if isinstance(row, list):
        # Passed in a list of rows. Use the first.
        row = row[0]
    price = float(row['Price'].strip().strip('$'))
    units = float(row['Size'].strip().split()[0].replace(',', ''))
    return price/units




def neb_search_product_url(name, collection="Products", filter="Disabled"):
    url = "https://www.neb.com/search"
    r = requests.get(url, params={'collection': collection, 'filter': filter, 'q': name})
    r.raise_for_status()
    if not r:
        print("Failed request:", r)
        return
    soup = BeautifulSoup(r.text)
    div = soup.find("div", {"class": "column-right result-list"})
    if not div:
        print("No div found with class matching 'column-right result-list'")
        return
    for li in div.findAll("li", {"class": "xhrblind blind-active purchase-options-search"}):
        a = li.find("a")
        if a and a.text.strip().lower() == name.lower():
            return a.get('href')    # you can also just do a['href']
    print("No products found that matches name ", name)



class NEB_enzyme_manager(object):
    def __init__(self, pickle_filepath=None):
        # requests.structures.CaseInsensitiveDict
        # <name>: {'product_table': ..., 'url': ..., ', 'cat_entry': ..., }
        self.Pickle_filepath = pickle_filepath
        self.Enzymes = CaseInsensitiveDict()
        if pickle_filepath:
            try:
                self.load_enzymes()
            except IOError as e:
                print("Could not load initial enzymes from %s:: %s: '%s'",
                      pickle_filepath, type(e), e)



    def get(self, name):
        """ Get enzyme by name. """
        if name in self.Enzymes:
            return self.Enzymes[name]
        url = self.search_product_url(name)
        if url:
            return self.Enzymes[name]

    def search_product_url(self, name):
        """ Search NEB website for product with name <name> and return product page url. """
        if self.Enzymes.get(name) and self.Enzymes[name].get('url'):
            return self.Enzymes[name]['url']
        url = neb_search_product_url(name)
        if url:
            self.Enzymes.setdefault(name, {})['url'] = url
        return url

    def get_product_table(self, name, entryid=None):
        """ Get product table for enzyma <name> """
        if self.Enzymes.get(name) and self.Enzymes[name].get('product_table'):
            return self.Enzymes[name]['product_table']
        if entryid:
            table = product_table(entryid)
        else:
            product_url = self.search_product_url(name)
            if not product_url:
                print("Could not find product name", name)
                return
            table = product_table(product_url)
        # Save and return
        self.Enzymes.setdefault(name, {})['product_table'] = table
        return table

    def get_price(self, name):
        """ Return price of <name> (using the first row in product table) """
        pt = self.get_product_table(name)
        return pt[0]['Price']

    def get_catno(self, name):
        """ Return price of <name> (using the first row in product table) """
        pt = self.get_product_table(name)
        return pt[0]['Catalog #']

    def get_size(self, name):
        """ Return price of <name> (using the first row in product table) """
        pt = self.get_product_table(name)
        return pt[0]['Size']

    def get_unit_price(self, name):
        """ Return unit price as $/unit """
        if self.Enzymes.get(name) and self.Enzymes[name].get('unit_price'):
            return self.Enzymes[name]['unit_price']
        table = self.get_product_table(name)
        up = unit_price(table)
        # Save and return
        self.Enzymes.setdefault(name, {})['unit_price'] = up
        return up

    def get_order_info_str(self, name):
        """ Return a standard price/order string for enzyme <name>. """
        return " {:7}: {:<6} ({}, {} for {}, {})"\
               .format(name, self.get_unit_price(name), self.get_catno(name),
                       self.get_price(name), self.get_size(name),
                       self.search_product_url(name))

    def load_enzymes(self, filepath=None):
        """ Load enzymes data from filepath or self.Pickle_filepath and merge with self.Enzymes. """
        if filepath is None:
            filepath = self.Pickle_filepath
        with open(filepath, 'rb') as fd:
            enzymes = pickle.load(fd)
        self.Enzymes.update(enzymes)
        print("%s enzymes loaded from file %s" % (len(enzymes), filepath))
        self.Pickle_filepath = filepath

    def save_enzymes(self, filepath=None):
        """ Save enzymes data to filepath or self.Pickle_filepath """
        if filepath is None:
            filepath = self.Pickle_filepath
        with open(filepath, 'wb') as fd:
            pickle.dump(self.Enzymes, fd)
        print("%s enzymes saved to file %s" % (len(self.Enzymes), filepath))
        self.Pickle_filepath = filepath




def get_cutters():


    ######   LONG LEASH    #########

    cutters = """
#       Enzyme  Specificity     Sites & flanks  Cut positions (blunt - 5' ext. - 3' ext.)
 1       ApeKI  GCWGC   list    82/85
 2       AseI   ATTAAT  list    88/90
 3       BbvI   GCAGC(N)8NNNN   list    69/73
 4       BcoDI  GTCTCNNNNN      list    18/22
 5       BsaXI  NNN(N)9AC(N)5CTCC(N)7NNN        list    93/90+123/120
 6       BsmAI  GTCTCNNNNN      list    18/22
 7       BsmBI  CGTCTCNNNNN     list    *18/22
 8       BsmI   GAATGCN list    99/97
 9       BsrI   ACTGGN  list    19/17
 10      Cac8I  GCNNGC  list    *33
 11      CviAII         CATG    list    121/123
 12      FatI   CATG    list    120/124
 13      FauI   CCCGCNNNNNN     list    *90/92
 14      Fnu4HI         GCNGC   list    83/84
 15      HhaI   GCGC    list    *42/40
 16      HinP1I         GCGC    list    *40/42
 17      HphI   GGTGA(N)7N      list    8/7
 18      Hpy188I        TCNGA   list    53/52
 19      HpyCH4III      ACNGT   list    48/47
 20      HpyCH4V        TGCA    list    85
 21      MnlI   CCTC(N)6N       list    97/96
 22      MseI   TTAA    list    88/90
 23      MwoI   GCNNNNNNNGC     list    37/34
 24      NlaIII         CATG    list    124/120
 25      PsiI   TTATAA  list    73
 26      TseI   GCWGC   list    82/85
 27      Tsp45I         GTSAC   list    14/19
 """

    # For long leash:
    lleash = dict()
    lleash[1] = [line.strip().split()[1] for line in cutters.strip().split('\n')][1:]
    lleash[2] = ["AluI", "TspRI"]
    lleash[3] = ["CviKI-1"]


    ######   LONG TEMPLATE    #########

    ltempl = dict()
    # ltempl 1-cutters:
    cutters = """
#	Enzyme	Specificity	Sites & flanks	Cut positions (blunt - 5' ext. - 3' ext.)
 1 	 BanI 	GGYRCC	list	98/102
 2 	 BccI 	CCATCNNNNN	list	4/5
 3 	 BseYI 	CCCAGC	list	115/119
 4 	 BslI 	CCNNNNNNNGG	list	#93/90
 5 	 BsrBI 	CCGCTC	list	*62
 6 	 BsrI 	ACTGGN	list	26/24
 7 	 EcoP15I 	CAGCAG(N)25NN	list	19/21
 8 	 FauI 	CCCGCNNNNNN	list	*26/28
 9 	 HphI 	GGTGA(N)7N	list	73/72
"""
    ltempl[1] = [line.split()[1] for line in cutters.strip().split('\n')][1:]
    # ltempl 2-cutters:
    cutters = """
#	Enzyme	Specificity	Sites & flanks	Cut positions (blunt - 5' ext. - 3' ext.)
 1 	 BsaJI 	CCNNGG	list	92/96, 93/97
 2 	 BssKI 	CCNGG	list	#86/91, #92/97
 3 	 BstNI 	CCWGG	list	88/89, 94/95
 4 	 Cac8I 	GCNNGC	list	*19, *121
 5 	 MluCI 	AATT	list	50/54, 67/71
 6 	 NlaIV 	GGNNCC	list	100, 114
 7 	 PspGI 	CCWGG	list	#86/91, #92/97
 8 	 ScrFI 	CCNGG	list	#88/89, #94/95
 9 	 StyD4I 	CCNGG	list	#86/91, #92/97
"""
    #ltempl['2-cutters'] = ["MluCI", "NlaIV"]
    ltempl[2] = [line.split()[1] for line in cutters.strip().split('\n')][1:]
    ltempl[3] = ["CviKI-1", "HaeIII", "Sau96I"]

    #return lleash, ltempl
    return dict([('lleash', lleash), ('ltempl', ltempl)])

def all_cutters(strand):
    return set.union(*[set(v) for k, v in strand.items() if isinstance(v, (set, list))])


def main():

    init_logging()
    pickle_filepath = os.path.expanduser("~/NEB_enzymes.p")
    neb = NEB_enzyme_manager(pickle_filepath)

    # <strand name> : {<freq> : <list of enzymes with freq>}
    cutters = get_cutters()

    cutters_freq = {strand_name: {name: freq
                                  for freq, enzymes in strand.items()
                                  for name in enzymes}
                    for strand_name, strand in cutters.items()
                   }
    for strand in cutters.values():
        strand['all-cutters'] = all_cutters(strand)

    for s_name, strand in cutters.items():
        print("\nEnzymes cutting only %s and only once:" % s_name)
        strand['1-unique'] = set(strand[1]) - next(cutters[k]['all-cutters'] for k in cutters if k != s_name)
        print(", ".join(strand['1-unique']))

    for s_name, strand in cutters.items():
        print("\nUnit prices for enzymes cutting only %s and only once:" % s_name)
        for name in sorted(strand['1-unique']):
            print("  %s\t %s" % (name, neb.get_unit_price(name)))

    neb.save_enzymes()

    for s_name, strand in cutters.items():
        print("\nFive cheapest restriction enzymes cutting only %s and only once:" % s_name)
        strand['1-unique-with-prices'] = {name: neb.get_unit_price(name) for name in strand['1-unique']}
        sort_by_value = lambda tup: tup[1]
        print("\n".join(neb.get_order_info_str(name)
                        for name, up in sorted(strand['1-unique-with-prices'].items(), key=sort_by_value)[:5]))

    print("\nEnzymes cutting both strands:")
    both_strand_cutters = set.intersection(*[strand['all-cutters'] for strand in cutters.values()])
    print(", ".join(both_strand_cutters))
    for name in both_strand_cutters:
        print(neb.get_order_info_str(name) + \
              "\t-- cutting {0[1]} in {0[0]} and {1[1]} in {1[0]}".format(
              *[(sn, cutters_freq[sn][name]) for sn in cutters_freq]))






    # set operations:
    # https://docs.python.org/2/library/sets.html
    # | union
    # & intersection
    # - difference
    # ^ symmetric_difference   (elements in a or b but not both, XOR)

    neb.save_enzymes()

    # http://nc2.neb.com/NEBcutter2/enz.php?name=63ca7b3d-&enzname=BanI
    #


if __name__ == '__main__':

    main()
