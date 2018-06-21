# -*- coding: UTF-8 -*-

"""
/**
 * A paper to keep track of previous results.
 * 
 * @author Thomas G. Kristensen & Rasmus Sorensen
 * @version 1.0
 */"""
class Paper:
    """
    /**
     * Constructs a new paper with the dimensions 
     * <code>(n + 1)</code> X <code>(m + 1)</code>.
     * 
     * @param The length of string <code>a</code>
     * @height The length of string <code>b</code>
     */"""
    
    def __init__(self, n, m):
        self.n = n
        self.m = m
        self.array = [[0 for col in range(m+1)] for row in range(n+1)] #new int[n + 1][m + 1];
        self.written = [[False for col in range(m+1)] for row in range(n+1)] #new boolean[n + 1][m + 1];
        
    """
    /**
     * Returns the saved integer in position <i>(i, j)</i>
     */
    public int """
    def read(self, i, j):
        return self.array[i][j]
        
    
    """/**
     * Writes a value on the paper.
     */ """
    def write(self, i, j, value):
        self.array[i][j] = value
        self.written[i][j] = True
        
    def restart(self, n, m):
        self.n = n
        self.m = m
        self.array = [[None for j in range(m+1)] for i in range(n+1)] #new int[n + 1][m + 1]
        self.written = [[False for j in range(m+1)] for i in range(n+1)] #new boolean[n + 1][m + 1]

    def isWritten(self, i, j):
        return self.written[i][j]
    
    def printPaper(self):
        strArr = ""
        for i in range(self.n+1): #(int i=0; i <= n; i++):
        
            for j in range(self.m+1): #(int j=0; j<=m; j++):
            
                strArr += str(self.array[i][j])
            
            strArr += "\n"
        
        print strArr #System.out.println(strArr)
    
    def printPaperFull(self, strA, strB, tegnPerPlads):
        if (len(strA) < 1 or len(strB) < 1): 
            return ""

        strArr = " " + insertSpaces(strB,tegnPerPlads) + "\n"
        for i in range(self.n+1) : # // Printer matrix linie
        
            strArr += strA[i] #.charAt(i);
            for j in range(self.m+1): #(int j=0; j<m; j++) // Printer matrix tegn
                #// Tilføj spaces i matrix-plads
                for taeller in range(tegnPerPlads+1): #(double taeller=1; taeller <= tegnPerPlads; taeller+
                    if self.array[i+1][j+1] < int(pow(10,taeller)) :
                        strArr += " "
                    else:
                        strArr += ""
                
                strArr += self.array[i+1][j+1]
            strArr += "\n"

        return strArr
    
    def insertSpaces(self, myString, tegnPerPlads):
    
        newString = ""
        for i in range(myString.length()): #(int i=0; i < myString.length(); i++)
        
            for j in range(tegnPerPlads): #(int j=0; j<tegnPerPlads; j++):
                newString += " "
            
            newString += myString[i]
        
        return newString
