class fairtask_scoring:
    '''
    translates the list of pairs (buyer [0] -> whom [1]) If product [2] is provided, favorite product is issued for consumer
    into dict of buyer : (rating, fav product)
    '''
    def recalculate_scoring(self, list):
        #TODO Add favorite product finder/exposure
        served={}
        offered={}
        for one in list:
            try:
                served[one[0]]+=1
            except KeyError:
                served[one[0]]=1
            try:
                offered[one[1]]+=1
            except KeyError:
                offered[one[1]]=1

        for one in served.keys():
            served[one]=served[one]/offered[one]
        return served

# scoring = fairtask_scoring()
# test = ( ('a', 'b'), ('a', 'a'),('a', 'c'),('a', 'd'),('b', 'a'),('b', 'd'),('b', 'b'),('d', 'b'), ('d', 'd') )
# served = scoring.recalculate_scoring(test)
# print(served)
