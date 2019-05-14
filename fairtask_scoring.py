class fairtask_scoring:
    '''
    Translates the allContracts list of three (buyer [0] -> whom [1] -> what [2])
    into dict of buyer : (rating, fav product)
    allContracts is the all time contracts history of (whom->to who-> what)
    presentContractors is the list of active order makers
     to narrow down the 'winner' within the present order makers
    '''

    def recalculate_scoring(self, allContracts, presentContractors=[]):
        if len(presentContractors):
            allContracts = self.filterContracts(allContracts, presentContractors)

        served = self.getCount(allContracts, i=0)
        offered = self.getCount(allContracts, i=1)
        resultScoring = {}
        for one in sorted(set(served.keys()) | set(offered.keys())):
            servedPerOne = served.get(one, 0)
            offeredPerOne = offered.get(one, 0)
            if len(presentContractors):
                if one in presentContractors:
                    resultScoring[one] = self.getScoringFor(servedPerOne, offeredPerOne)
                else:
                    continue
            else:
                resultScoring[one] = self.getScoringFor(servedPerOne, offeredPerOne)
        return resultScoring

    def getScoringFor(self, servedPerOne,offeredPerOne):
        return (servedPerOne - offeredPerOne)

    def filterContracts(self, list, elementsLookFor, i=1):
        toReturn = []
        for one in list:
            if one[i] in elementsLookFor:
                toReturn.append(one)
        return toReturn

    def getCount(self, list, i=0):
        result = {}
        for one in list:
            try:
                result[one[i]] += 1
            except KeyError:
                result[one[i]] = 1
        return result
