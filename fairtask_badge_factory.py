
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

    def find(self, date, user, earlierDate=None):
        raise NotImplementedError('AbstractClass - should be implemented')


class Abstract_Badge_On_Limit(Abstract_Badge):
    _limit = 0

    def __init__(self, storage, id, unique, limit):
        Abstract_Badge.__init__(self,
                                storage=storage,
                                id=id,
                                unique=unique)
        self._limit = limit

    def executeAndCompare(self, sql):
        toReturn = {}
        for oneContrat in self._storage.execute_get_sql(sql):
            if oneContrat[1] >= self._limit:
                toReturn[oneContrat[0]] = \
                    int((oneContrat[1] - (oneContrat[1] % self._limit))/self._limit)
        return toReturn


class badge_multiple_servings(Abstract_Badge_On_Limit):

    def __init__(self, storage):
        Abstract_Badge_On_Limit.__init__(self,
                                         storage=storage,
                                         id=4,
                                         unique=False,
                                         limit=10)

    def find(self, date, user, earlierDate=None):
        sqlAdd = self.getDateLimiter(date=earlierDate)
        sql ="select buyerId, count(buyerId) from (select buyer buyerId from contract where buyer=%d and date <= '%s' %s group by date) group by buyerId" %(user, date, sqlAdd)
        return self.executeAndCompare(sql)


class badge_fifty_coffees_consumed(Abstract_Badge_On_Limit):

    def __init__(self, storage):
        Abstract_Badge_On_Limit.__init__(self,
                                         storage=storage,
                                         id=3,
                                         unique=False,
                                         limit=50)

    def find(self, date, user, earlierDate=None):
        sqlAdd = self.getDateLimiter(date=earlierDate)
        sql = "select to_whom userId, count(to_whom) consumed from contract where to_whom=%d and date<='%s' %s group by to_whom" % (user, date, sqlAdd)
        return self.executeAndCompare(sql)


class badge_five_expensive_coffees(Abstract_Badge_On_Limit):
    FIXED_NUMBER = 5

    def __init__(self, storage):
        Abstract_Badge_On_Limit.__init__(self,
                                         storage=storage,
                                         id=2,
                                         unique=False,
                                         limit=5)

    def find(self, date, user, earlierDate=None):
        expensiveCoffeeId = self._storage.execute_get_sql('select id from product order by price desc limit 1 ')[0]
        sqlAdd = self.getDateLimiter(date=earlierDate)
        sql = "select to_whom userId, count(to_whom) consumed from contract where to_whom={} and  product={} and date <='{}' {} group by to_whom".format(user, expensiveCoffeeId[0], date, sqlAdd)
        return self.executeAndCompare(sql)


class badge_ten_minus_penalty(Abstract_Badge):
    FIXED_NUMBER = -10

    def __init__(self, storage):
        Abstract_Badge.__init__(self,
                                storage=storage,
                                id=6,
                                unique=True)

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


class badge_ten_plus_buffer(Abstract_Badge):
    FIXED_BUFFER = 10

    def __init__(self, storage):
        Abstract_Badge.__init__(self,
                                storage=storage,
                                id=1,
                                unique=False)

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
