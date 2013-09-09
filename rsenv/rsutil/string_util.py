import hashlib

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
