# -*- coding: UTF-8 -*-
"""
Based on FilenameCompare java program (developed by Rasmus Sorensen)
 * StringCompareLimit
 * Optimerer ved at vide om en bestemt streng har mulighed for at nå limit
 * Optimering 1: Længdesammenligning (ca. 50% optimering ved få ens strenge og mange meget uens)
 *  - Hvis limit fx er 0.9, og en streng er 20 tegn, _skal_ den anden streng være 17-24 tegn.
 * Optimering 2: Løbende vurdering af om sammenligningen kan nå limit ( ca. 30% optimering )
 * 
 """
from .Paper import Paper
#import random

class StringCompareLimit:
    """/**
    * Field variabler
    */
    #protected String a, b;
    #// private long maxresKald;
    #protected Paper paperP;
    #private double goodness;
    #private double limit;
    #private boolean isPossible = true;
    /** 
     * Konstruktor
     */"""
    
    def __init__(self, a='', b='', limit = 0.9):
        self.goodness = 0
        self.a = a
        self.b = b
        self.n = len(a)
        self.m = len(b)
        self.paperP = Paper(self.n,self.m)
        #self.restart()
        self.limit = limit
        self.setMinRes()
        #print self.minimumres
        self.isPossible = True
        
    def setLimit(self, lim):
        self.limit = lim
    
   
    def restart(self):
        self.paperP.restart( self.n, self.m )
    
    def calculate(self):
        self.goodness = self.resToGoodness(self.result())
        return self.goodness
        
    def recalculate(self, a, b):
        self.a = a
        self.b = b
        self.n = len(self.a)
        self.m = len(self.b)
        
        # Quick tests:
        if ( a == b ): return 1 #// Kan måske optimere hvis der er mange ens strenge
        # Længdeforskel gør at vi ikke nå limit - for meget forskellige filer halverer dette den samlede beregningstid!
        #if ( self.resToGoodness(min(self.n,self.m)) < self.limit ): return 0

        # Reset attributes:
        self.setMinRes()        
        self.isPossible = True
        self.paperP.restart( self.n, self.m );
        
        return self.calculate()
        
        
    # Sepererer lige resToGoodness beregningsmetoden, i tilfælde af at den bliver ændret senere
    def resToGoodness(self, res):
        return 2*float(res)/(self.n+self.m)

    # Should use the same algorihm as resToGoodness
    def setMinRes(self):
        self.minimumres = int(self.limit/2*(self.n+self.m))
    
    """
    Selve beregningsalgoritmen
    maxres beregner hvor mange tegn der maxresimalt kan alignes i de to strenge a og b.
    gøres ved at lave en matrix med rækker=len(a) og søjler=len(b)
    Procedure: Find først det bedste resultat fra hver nabo (til venstre og for oven)
    Se derefter om du har en alignment med aktuelle chars, i.e. at self.a[i]==self.b[j]
    PS: When calculating a stringpair with 0.6 similarity using a limit of 0.9, 
    you can cut away approx two-thirds of the maxres calls (both before and after initial checks)
    For strings with less similarity, this should drop even further.
    """
    
    def maxres(self, i, j):
        
        if (not self.isPossible): return 0

        if (self.paperP.isWritten(i,j)): 
            #self.herecount += 1
            #print "Calls times here: %d" % self.herecount
            return self.paperP.read(i,j)
        
        if ( i == 0 or j == 0 ) : return 0
        
        
        resultat = max(self.maxres(i-1, j), self.maxres(i, j-1))
        
        # Re-do checks after calling maxres ?
        if (not self.isPossible): # This check avoids n unneeded proceedings 
            return 0
        
        # When we have reached a certain point start to check if we can even reach the limit.
        if (i*5 > self.n and j*5 > self.m ):
            if (resultat + max(self.n - i, self.m - j) +1 < self.minimumres):
                self.isPossible = False
                return 0
        
        # Investigate whether the new res is better:
        if self.a[i-1] == self.b[j-1]: 
            if (self.maxres(i-1, j-1) + 1 > resultat):
                resultat = self.maxres(i-1, j-1) + 1 # Add one to the previous high-score (if this is better than the neighbours)

        # PS: Since all calls goes "up or left" (i-x and j-y), no further checks with paperP.isWritten is needed.
            
        self.paperP.write(i,j,resultat)
        
        return resultat
    
    
    """/**
     * Returner resultatet af beregningsalgoritmen
     */"""    
    def result(self):
        res = self.maxres(self.n, self.m) #; // Start fra neden
        #print "Result for " + self.a + " vs " + self.b + " is " + str(res)
        return res;
        
    """
    Return the highest value that is still possible
    // Svært at bruge helt optimalt, når vi er langt inde i en rekurssion...
    // Skal adderes med 1, ellers giver den for lavt resultat
    """
    def getMaxRes(self, currentRes, i, j):
        return currentRes + max(self.n - i, self.m -j) +1
    
    
    #def setCanReachLimit(self, currentRes, i, j):
        #if ( self.resToGoodness(self.getMaxRes(currentRes, i, j)) < self.limit ): # // Vi kan ikke nå limit
        if (currentRes + max(self.n - i, self.m - j) +1 < self.minimumres):
            self.isPossible = False;
            print("Cannot reach")
