
class Abstract_Badge:
    _id = -1
    _storage = None
    _unique = False

    def __init__(self, storage, id, unique):
        self._storage = storage
        self._id = id
        self._unique = unique

    def isUnique(self):
        return self._unique

    def getBadgeId(self):
        return self._id

    def getDateLimiter(self, date=None):
        if date is not None:
            return ' and date > \'%s\'' % date
        return ''

    def find_number(self, contracts, number):
        '''
        Translates the list of ((a,b), ... ) into ((a, c),...) where c is the
        (b-b%number)/number
        '''
        toReturn = {}
        for oneContrat in contracts:
            if oneContrat[1] >= number:
                toReturn[oneContrat[0]] = \
                 int((oneContrat[1] - (oneContrat[1] % number)) / number)
        return toReturn

    def find(self, date, user, earlierDate=None):
        raise NotImplementedError('AbstractClass - should be implemented')


##########################################################################


class badge_multiple_servings(Abstract_Badge):
    FIXED_SERVINGS = 10

    def __init__(self, storage):
        Abstract_Badge.__init__(self, storage=storage, id=4, unique=False)

    def find(self, date, user, earlierDate=None):
        sqlAdd = self.getDateLimiter(date=earlierDate)
        sql ="select buyerId, count(buyerId) from (select buyer buyerId from contract where buyer=%d and date <= '%s' %s group by date) group by buyerId" %(user, date, sqlAdd)
        _contracts = self._storage.execute_get_sql(sql)

        toReturn = self.find_number(_contracts, self.FIXED_SERVINGS)
        return toReturn

##########################################################################


class badge_fifty_coffees_consumed(Abstract_Badge):
    FIXED_THRESHOLD = 50
    _storage = None

    def __init__(self, storage):
        Abstract_Badge.__init__(self, storage=storage, id=3, unique=False)

    def find(self, date, user, earlierDate=None):
        sqlAdd = self.getDateLimiter(date=earlierDate)
        sql = "select to_whom userId, count(to_whom) consumed from contract where to_whom=%d and date<='%s' %s group by to_whom" % (user, date, sqlAdd)
        _contracts = self._storage.execute_get_sql(sql)

        toReturn = self.find_number(_contracts, self.FIXED_THRESHOLD)
        return toReturn


##########################################################################


class badge_ten_minus_penalty(Abstract_Badge):
    FIXED_NUMBER = -10

    def __init__(self, storage):
        Abstract_Badge.__init__(self, storage=storage, id=6, unique=True)

    def find(self, date, user, earlierDate=None):
        sqlAdd = self.getDateLimiter(date=earlierDate)

        sql = "select buyer, to_whom, product from contract where (buyer=%d or to_whom=%d) and buyer!=to_whom and date<= \'%s\' %s "%(user, user, date, sqlAdd)
        allContracts = self._storage.execute_get_sql(sql)

        from fairtask_scoring import fairtask_scoring
        scoring = fairtask_scoring()
        result = scoring.recalculate_scoring(allContracts)
        toReturn = {}
        for one in result.keys():
            if result.get(one) <= self.FIXED_NUMBER:
                toReturn[one] = 1
        return toReturn


##########################################################################


class badge_ten_plus_buffer(Abstract_Badge):
    FIXED_BUFFER = 10

    def __init__(self, storage):
        Abstract_Badge.__init__(self, storage=storage, id=1, unique=False)

    def find(self, date, user, earlierDate=None):
        sqlAdd = self.getDateLimiter(date=earlierDate)

        sql = "select buyer, to_whom, product  from contract where (buyer=%d or to_whom=%d) and buyer!=to_whom and date<= \'%s\' %s "%(user, user, date, sqlAdd)
        allContracts = self._storage.execute_get_sql(sql)

        from fairtask_scoring import fairtask_scoring
        scoring = fairtask_scoring()
        result = scoring.recalculate_scoring(allContracts)
        toReturn = {}
        for one in result.keys():
            if result.get(one) >= self.FIXED_BUFFER:
                toReturn[one] = 1
        return toReturn


##########################################################################


class badge_five_expensive_coffees(Abstract_Badge):
    FIXED_NUMBER = 5

    def __init__(self, storage):
        Abstract_Badge.__init__(self, storage=storage, id=2, unique=False)

    def find(self, date, user, earlierDate=None):
        expensiveCoffeeId = self._storage.execute_get_sql('select id from product order by price desc limit 1 ')[0]

        sqlAdd = self.getDateLimiter(date=earlierDate)

        sql = "select to_whom userId, count(to_whom) consumed from contract where to_whom={} and  product={} and date <='{}' {} group by to_whom".format(user, expensiveCoffeeId[0], date, sqlAdd)

        _contracts = self._storage.execute_get_sql(sql)
        toReturn = toReturn = self.find_number(_contracts, self.FIXED_NUMBER)
        return toReturn
