

#From doPcAnalysis():

                #if xrngindex == 0: rngidx[0] = 0
                #else: rngidx[1] = len(self.Xdata)-1
        if xrng[0] is None: rngidx[0] = 0
        else: 
            print self.Xdata
            # Need to cast Xdata value to int (or perhaps decimal) to make it not be '230.0' string.
            # Uh, problem... equipment does not record nearly all integer x values. So, instead, find the one closest.
            # Well, good thing I just saw this in Trine Okholm's exam: k,v = max(d.items(), key = lambda x:x[1])
            # d.items ^ returns a list of tuples. The key can be used to specify a sorting function.
            # All list elements are then passed through the key function, and sorted based on the return value.
            # Applying this to finding the Xdata point closest to xmin in xrng: (calling the index,val tuple for 'iv')
            

            #print dict([(index,int(val)) for index,val in enumerate(self.Xdata)])
            #print dict([(int(val),index) for index,val in enumerate(self.Xdata)]) #[xrng[0]]
#            rngidx[0] = dict([(val,index) for index,val in enumerate(self.Xdata)])[xrng[0]]
        if xrng[0] is None: rngidx[1] = len(self.Xdata)-1
        else: rngidx[1] = dict([(val,index) for index,val in enumerate(self.Xdata)])[xrng[1]]
        
