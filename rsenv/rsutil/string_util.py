import hashlib
import itertools

class Simhash():
    def __init__(self, text):
        self.hashbits = 384
        self.hash = self.simhash(text.split())

    def __str__(self):
        return str(self.hash)

    def __int__(self):
        return int(self.hash)

    def __float__(self):
        return float(self.hash)

    def simhash(self, tokens):
        v = [0]*self.hashbits

        for t in [self.string_hash(x) for x in tokens]:
            bitmask = 0
            for i in range(self.hashbits):
                bitmask = 1 << i
                if t & bitmask:
                    v[i] += 1
                else:
                    v[i] -= 1

        fingerprint = 0

        for i in range(self.hashbits):
            if v[i] >= 0:
                fingerprint += 1 << i

        return fingerprint

    def string_hash(self, v):
        return int(hashlib.sha384(v.encode()).hexdigest(), 16)

    def similarity(self, other_hash):
        hash1 = float(self.hash)
        hash2 = float(other_hash)

        if hash1 > hash2:
            return hash2/hash1
        else:
            return hash1/hash2


def simhash_compare(new, old):
    newsimhash, oldsimhash = Simhash(new), Simhash(old)
    return newsimhash.similarity(oldsimhash)


def text_to_table(text, ncols, sep='\n', nskip=0):
    """
    Takes a table where each cell is an independent line and returns a list-of-tuples struct,
    where each tuple is a row in the table.
    nskip can be used to skip the first few entries.
    As one-liner: list( itertools.izip_longest(*[(line for line in text.split(sep)[1:])]*ncols) )
    """
    return list( itertools.izip_longest(*[(line for line in text.split(sep)[nskip:])]*ncols) )



def text_to_table_string(text, ncols, sep='\n', outsep='constantwidth', doprint=True, nskip=0):
    """
    Takes a table where each cell is an independent line, and formats back to a table-like string.
    E.g. for text:
Page
Key
Type
Value
id
long
the id of the page
space
String
the key of the space that this page belongs to
    text_to_table_string(text, 3, sep='\n', outsep='constantwidth', nskip=1, doprint=False) would return:
Key           Type    Value                                         
id            long    the id of the page                            
space         String  the key of the space that this page belongs to
    """
    tl = text_to_table(text, ncols, sep, nskip)
    if outsep == 'constantwidth':
        fieldwidths = map(lambda *x: max(map(len, x)), *tl)
        linefmt = " ".join("{:<%s}" %i for i in fieldwidths)
    else:
        linefmt = outsep.join("{}" for i in ncols)
    ret = "\n".join( linefmt.format(*fields) for fields in tl )
    if doprint:
        print ret
    return ret

