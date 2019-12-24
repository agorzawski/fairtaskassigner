class fairtask_scoring:
    '''
    Translates the allContracts list of three (buyer [0]-> whom [1]-> what [2])
    into dict of buyer : (rating, fav product)
    allContracts is the all time contracts history of (whom->to who-> what)
    presentContractors is the list of active order makers
     to narrow down the 'winner' within the present order makers
    '''
    _scoringFromBadges = {}
    _scoringFromTransfers = {}

    def recalculate_scoring(self, allContracts,
                            presentContractors=[],
                            verbose=False):
        allContracts = self.remove_self_contracts(allContracts)
        if len(presentContractors):
            allContracts = self.filterContracts(allContracts,
                                                presentContractors)

        served = self.getCount(allContracts, i=0)
        offered = self.getCount(allContracts, i=1)
        resultScoring = {}
        for one in sorted(set(served.keys()) | set(offered.keys())):
            servedPerOne = served.get(one, 0)
            offeredPerOne = offered.get(one, 0)
            if verbose:
                print(one, 'Served:', servedPerOne, ', was offered: ',
                      offeredPerOne)
            if len(presentContractors):
                if one in presentContractors:
                    resultScoring[one] = self.getScoringFor(one,
                                                            servedPerOne,
                                                            offeredPerOne)
                else:
                    continue
            else:
                resultScoring[one] = self.getScoringFor(one,
                                                        servedPerOne,
                                                        offeredPerOne)
        return resultScoring

    def getScoringFor(self, one, servedPerOne, offeredPerOne):
        return (servedPerOne - offeredPerOne) +\
            self._scoringFromBadges.get(one, 0) +\
            self._scoringFromTransfers.get(one, 0)

    def setScoringFromBadges(self, scoringFromBadges):
        self._scoringFromBadges = scoringFromBadges

    def setScoringFromTransfers(self, scoringFromTransfers):
        self._scoringFromTransfers = scoringFromTransfers

    def filterContracts(self, list, elementsLookFor):
        toReturn = []
        for one in list:
            if one[1] in elementsLookFor and one[0] in elementsLookFor:
                toReturn.append(one)
        return toReturn

    def remove_self_contracts(self, list):
        toReturn = []
        for one in list:
            if one[0] != one[1]:
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
