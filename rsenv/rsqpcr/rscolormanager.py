# -*- coding: utf-8 -*-
"""
Created 2013/09/05

@author: scholer


"""

#from itertools import cycle
import itertools
# alternatively, use collections.deque
from collections import deque

levenshtein_available = jellyfish_available = fuzzywuzzy_available = difflib_available = simhash_available = False

try:
    import Levenshtein # from 2008, code.google.com/p/pylevenshtein/
    levenshtein_available = True
except ImportError:
    try:
        import jellyfish # pypi.python.org/pypi/jellyfish
        jellyfish_available = True
    except ImportError:
        try:
            import fuzzywuzzy # github.com/seatgeek/fuzzywuzzy
            # http://seatgeek.com/blog/dev/fuzzywuzzy-fuzzy-string-matching-in-python
            fuzzywuzzy_available = True
        except ImportError:
            try:
                import difflib # standard library, should be available.
                difflib_available = True
            except ImportError:
                try:
                    # Charikar’s hash, http://blog.simpliplant.eu/calculating-similarity-between-text-strings-in-python/
                    from rsenv.rsutil import simhash_compare 
                    simhash_available
                except ImportError:
                    pass
                    # Other alternatives:
                    # github.com/dracos/double-metaphone


class ColorManager(object):
    def __init__(self):
        self.Colors = self.makeColors()
        self.Colorcycle = itertools.cycle(self.Colors)  # get the next using .next() or __next__()
        # http://docs.python.org/2/library/collections.html#collections.deque
        # can also be achieved using numpy.roll(array, int)
        self.Colorque = deque(self.Colors)    # can be rotated using .rotate(N)
        self.Lastswithstring = None
        self.LastComparedString = None
        self.VERBOSE = 4

    def makeColors(self, scheme='standard'):
        return [c for c in 'rgbcmyk'] + ['slate'] #,'aqua','marine']

    def strCompare(self, new, ratiomin=0.8):
        if self.Lastswithstring is None:
            self.Lastswithstring = ""
        old = self.Lastswithstring # can be Lastswithstring or LastComparedString
        if levenshtein_available:
            ratio = Levenshtein.ratio(new, old)
        elif jellyfish_available:
            ratio = jellyfish.jaro_distance(new, old)
        elif fuzzywuzzy_available:
            fuzzywuzzy.fuzz.ratio(new, old)
        elif difflib_available:
            print "Comparing {} with {} using difflib.SequenceMatcher.".format(new, old)
            ratio = difflib.SequenceMatcher(None, new, old).ratio()
        elif rssimhash_available:
            ratio = simhash_compare(new, old)
        else:
            print "No string diff lib available!"
            ratio = 0.9
        return ratio


    def switchColor(self, new, ratiomin=0.85):
        """
        Evaluate whether to switch data or not.
        http://stackoverflow.com/questions/682367/good-python-modules-for-fuzzy-string-comparison
        """
        ratio = self.strCompare(new, ratiomin)
        self.LastComparedString = new
        if ratio < ratiomin:
            self.Lastswithstring = new
            self.Colorque.rotate(-1)
            if self.VERBOSE > 2:
                print "ColorManager.switchColor:: Ratio={}, SWITCHING color to: '{}'.".format(ratio, self.Colorque[0])
        elif self.VERBOSE > 3:
            print "ColorManager.switchColor:: > Ratio={}, keeping color: '{}'.".format(ratio, self.Colorque[0])
        return self.Colorque[0]
        



class StyleManager(ColorManager):
    def __init__(self):
        ColorManager.__init__(self)
        self.Linestyles = ['-', '--', '-.', ':']
        # http://matplotlib.org/api/markers_api.html#module-matplotlib.markers
        # marker can also be mathtext, vertices, paths, a tuple of (numsides, style, angle), etc.
        self.Markers = [c for c in '.*+xov^<>1234sphH8Dd,'] 
#        self.AllStyleTuples = itertools.product(self.Colors, self.Linestyles, self.Markers)
        self.AllStyleTuples = [ (c, ls, m) for m in self.Markers for ls in self.Linestyles for c in self.Colors]
        self.AllStyleTuplesQue = deque(self.AllStyleTuples)


    def swithedStyle(self, new, ratiomin=0.85):
        return self.switchStyle(new, ratiomin)[1]

    def switchStyle(self, new, ratiomin=0.85):
        """
        Evaluate whether to switch data or not.
        http://stackoverflow.com/questions/682367/good-python-modules-for-fuzzy-string-comparison
        """
        ratio = self.strCompare(new, ratiomin)
        self.LastComparedString = new
        styleswitch = False
        if ratio < ratiomin:
            styleswitch = True
            self.Lastswithstring = new
            self.AllStyleTuplesQue.rotate(-1)
            if self.VERBOSE > 2:
                print "ColorManager.switchColor() > Ratio is {}, switching style to: '{}'.".format(ratio, self.AllStyleTuplesQue[0])
        elif self.VERBOSE > 3:
            print "ColorManager.switchColor() > Ratio is {}, keeping style: '{}'.".format(ratio, self.AllStyleTuplesQue[0])
        return (styleswitch, self.AllStyleTuplesQue[0])




