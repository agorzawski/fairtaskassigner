class fairtask_scoring:
    '''
    Translates the allContracts list of pairs (buyer [0] -> whom [1]) into dict of buyer : (rating, fav, product)
    allContracts is the all time contracts history of (whom->to who-> what)
    presentContractors is the list of active order makers -> to narrow down the winner
    '''
    def recalculate_scoring(self, allContracts, presentContractors=[]):
        #TODO Add favorite product finder/exposure

        served={}
        offered={}
        for one in allContracts:
            try:
                served[one[0]]+=1
            except KeyError:
                served[one[0]]=1
            try:
                offered[one[1]]+=1
            except KeyError:
                offered[one[1]]=1

        for one in served.keys():
            try:
                served[one] = round(served[one]-offered[one], 1)
            except KeyError:
                served[one] = round(served[one], 1)

        return served
