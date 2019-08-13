import sqlite3
from datetime import datetime, timedelta
from fairtask_scoring import fairtask_scoring
import os

# use db/dbScheme.sql to create an sqlite db
DATABASE_NAME = os.environ.get("FN_DB_TO_USE", default=False)
NON_SELECTED_VALUE = -1
DUMMY_VALUE = -666
'''
utility class for SQLite connection
'''


class fairtaskDB:

    ALLOW_COMMIT = False

    def __init__(self, allowCommit=False):
        self.load_db()
        self.ALLOW_COMMIT = allowCommit

    def load_db(self):
        self.con = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
        self.c = self.con.cursor()

    def execute_sql(self, sql, commit=False):
        try:
            errors = []  # TODO add SQL injection check on sql
            if len(errors) > 0:
                return False
            self.c.execute(sql)
            if commit and self.ALLOW_COMMIT:
                self.con.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def execute_get_sql(self, sql):
        self.c.execute(sql)
        data = self.c.fetchall()
        return data

    # ####################
    # Customized calls
    def add_user(self, name, email, creator, validated=0):
        sql = 'insert into user (email, username, rating, creator, validated, added, active) values (\'%s\', \'%s\', 0.0, %s, %s, CURRENT_TIMESTAMP, 1)' % (email, name, creator, validated)
        self.execute_sql(sql, commit=True)
        sql = 'select id from user where username=\'%s\' and email=\'%s\'' % (name, email)
        return self.execute_get_sql(sql)[0][0]

    def update_user(self, existingId, email, creator, validated=0):
        sql = 'update user set email=\'%s\', creator=%s, validated=%s where id=%s' % (email, creator, validated, existingId)
        self.execute_sql(sql, commit=True)

    def update_user_active(self, existingId, active=0):
        sql = 'update user set active=%d where id=%s' % (active, existingId)
        self.execute_sql(sql, commit=True)

    def add_product(self, name, price, size, coffeine):
        sql = 'insert into product (name, price, size, caffeine) values (\'%s\', %.1f, %.1f, %.1f)' % (name,
                                                            price,
                                                            size,
                                                            coffeine)
        self.execute_sql(sql, commit=True)

    def add_transaction(self, who, whom, what, creator, commit=False):
        if who == NON_SELECTED_VALUE or whom == NON_SELECTED_VALUE or what == NON_SELECTED_VALUE:
            raise ValueError('Cannot save transaction for an unspecified person or goods!')
        else:
            sql = 'insert into contract (buyer, to_whom, product, date, creator) values (%s, %s, %s, CURRENT_TIMESTAMP, %s)' % (who, whom, what,creator)
            self.execute_sql(sql, commit=commit)
            self.calculate_actal_scoring(commit=commit)
            return True

    def add_to_bucket(self, whom, what):
        if int(whom) > 0 and int(what) > 0:
            sql = 'insert into  contract_temp (to_whom, product) values (%s, %s)' % (whom, what)
            self.execute_sql(sql)
            self.calculate_actal_scoring(commit=True)

    def check_if_in_bucket(self, userId):
        result = self.execute_get_sql('select * from contract_temp where to_whom=%d' % userId)
        if result:
            return True
        return False

    def get_favorite_product(self, userId):
        sql = 'SELECT product, COUNT(product) AS vo FROM contract where to_whom=%d GROUP BY product ORDER BY vo DESC LIMIT 1'%userId
        result = self.execute_get_sql(sql)
        if len(result) > 0 and result[0]:
            return self.get_product_details(result[0][0])
        else:
            return (NON_SELECTED_VALUE, 'NOT FOUND')

    def get_scoring_from_badges(self, date=None):
        sqlDate = ''
        if date is not None:
            sqlDate =' and user_badges.date <= \'%s\'' % date
        scoringFromBadgesData = self.execute_get_sql('select userId, sum(effect) from user_badges join badges on user_badges.badgeId = badges.id  where user_badges.valid>0 %s group by userId' % sqlDate)
        scoringFromBadges = {}
        for one in scoringFromBadgesData:
            scoringFromBadges[one[0]] = one[1]
        return scoringFromBadges

    def get_scoring_from_transfers(self, date=None):
        sqlDate = ''
        if date is not None:
            sqlDate =' and date <= \'%s\'' % date
        scoringFromTransfersData = self.execute_get_sql('select from_user, to_user, value from rating_transfer where valid>0 %s ' % sqlDate)
        scoringFromTransfers = {}
        for one in scoringFromTransfersData:
            try:
                scoringFromTransfers[one[0]] += -1 * one[2]
            except KeyError:
                scoringFromTransfers[one[0]] = -1 * one[2]
            try:
                scoringFromTransfers[one[1]] += one[2]
            except KeyError:
                scoringFromTransfers[one[1]] = one[2]
        return scoringFromTransfers

    def calculate_actal_scoring(self, date=None, updateDb=True, commit=False, presentContractors=[]):
        sqlDate = ''
        if date is not None:
            sqlDate =' where date <= \'%s\'' % date
        data = self.execute_get_sql('select buyer, to_whom, product from contract %s' % sqlDate)
        scoring = fairtask_scoring()
        scoring.setScoringFromBadges(self.get_scoring_from_badges(date=date))
        scoring.setScoringFromTransfers(self.get_scoring_from_transfers(date=date))
        result = scoring.recalculate_scoring(data, presentContractors=presentContractors)
        if updateDb:
            for one in result.keys():
                self.c.execute('update user set rating=%f where id=%s' % (result[one], one))
        if commit and self.ALLOW_COMMIT:
            try:
                self.con.commit()
                return (True, result)
            except sqlite3.IntegrityError:
                return (False, result)
        else:
            return (True, result)

    def clean_bucket(self):
        self.execute_sql('delete from contract_temp', commit=True)

    def get_bucket_raw(self):
        return self.execute_get_sql('select * from contract_temp')

    def remove_item_in_bucket(self, towhom, what):
        sql = 'delete from contract_temp where product=%d and to_whom=%d' % \
            (what, towhom)
        self.execute_sql(sql, commit=True)

    def get_bucket(self):
        dataBucket = self.execute_get_sql('select username, what, rating, user.id, whatId from (select to_whom whom, name what, product.id whatId from contract_temp join product on product.id = product) join user on user.id=whom')
        # (whom, what, rating) with origanl scorings
        if dataBucket:
            dataBucketSimple = self.execute_get_sql('select to_whom from contract_temp')
            data = self.execute_get_sql('select buyer, to_whom, product from contract')
            scoring = fairtask_scoring()
            scoring.setScoringFromBadges(self.get_scoring_from_badges())
            presentContractors = []
            for one in dataBucketSimple:
                presentContractors.append(one[0])
            resultForOrdering = scoring.recalculate_scoring(data,
                                                 presentContractors=presentContractors)
            toReturn = [
                (data[0], data[1], resultForOrdering.get(data[3], 0), data[3], data[4], data[2])
                for data in dataBucket
            ]
            return toReturn
        return dataBucket

    def get_granted_badges(self, date=None):
        sqlAdd = ""
        if date is not None:
            sqlAdd = " and date <=\'%s\'" % date
        sql = "select * from user_badges where valid>0 %s" % sqlAdd
        data = self.execute_get_sql(sql)
        toReturn = {}
        for one in data:
            toReturn[one[0]] = {'id': one[0],
                                'userId': one[1],
                                'badgeId': one[2],
                                'date': one[3],
                                'valid': one[4],
                                'grantBy': one[5]}
        return toReturn

    def get_all_badges(self, badgeUniqe=None, adminBadges=False):
        whereBadge = ''
        if badgeUniqe is not None:
            whereBadge = ' where adminawarded=1 '
            if not adminBadges:
                whereBadge += 'and name not like \'%admin%\' '

        sql = 'select * from badges %s order by effect, name' % whereBadge
        data = self.execute_get_sql(sql)
        toReturn = {}
        for one in data:
            toReturn[one[0]] = {'id': one[0],
                                'name': one[1],
                                'img': one[2],
                                'desc': one[3],
                                'effect': one[4],
                                'adminawarded': one[5]}
        return toReturn

    def get_badge_grant_history(self, allValidities=False, withUser=None):
        sqlOnUser = ''
        if withUser is not None:
            sqlOnUser = ' and username like \'%s\' ' % withUser
        sqlAdd = ' where valid=1 %s' % sqlOnUser
        if allValidities:
            sqlAdd = sqlOnUser.replace('and', 'where')
        sql = 'select grantId, username, badgeName, img, date, grantByUserName, badgeId, valid from badges_granted_timeline %s' % sqlAdd
        data = self.execute_get_sql(sql)
        toReturn = {}
        for i, one in enumerate(data):
            toReturn[i] = {'grantId': one[0],
                           'username': one[1],
                           'badgeName': one[2],
                           'img': one[3],
                           'date': one[4],
                           'grantByUserName': one[5],
                           'badgeId': one[6],
                           'valid': one[7]}
        return toReturn

    # def get_users_badges_timeline(self):
    #     # TODO combine with the above
    #     sql = 'select * from badges_granted_timeline'
    #     data = self.execute_get_sql(sql)
    #     toReturn = {}
    #     for one in data:
    #         toReturn[one[0]] = {'grantId': one[0],
    #                             'userId': one[1],
    #                             'username': one[2],
    #                             'date': one[3],
    #                             'img': one[4],
    #                             'badgeName': one[5],
    #                             'badgeId': one[6],
    #                             'grantById': one[7],
    #                             'grantByUserName': one[8],
    #                             'valid': one[9]}
    #     return toReturn

    def get_users_badges(self, userId=None):
        where = ' where user_badges.valid=1 '
        if userId is not None:
            where = ' where user_badges.valid=1 and user.id=%d ' % userId
        sql = 'select * from (select user.id userId, date, badgeId from user join user_badges on user.id=user_badges.userId %s ) a join badges on badges.id=a.badgeId' % (where)
        toReturn = {}
        data = self.execute_get_sql(sql)
        for i, one in enumerate(data):
            toReturn[i] = {'userId': one[0],
                           'date': one[1],
                           'badgeId': one[2],
                           'id': one[3],
                           'name': one[4],
                           'img': one[5],
                           'desc': one[6],
                           'effect': one[7],
                           'adminawarded': one[8]}
        return toReturn

    def insert_user_badges(self, badgeId, userId, date, grantBy, valid=1):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql='insert into user_badges (userId, badgeId, date, valid, grantby) values (\'%d\', \'%d\',\'%s\', \'%d\', \'%d\')'  % (badgeId, userId, date, valid, grantBy)
        self.execute_sql(sql, commit=True)

    def remove_user_bagde(self, badgeGrantId, valid, removigUserId):
        sql='update user_badges set valid=%d, grantby=%d where id=%d' % (valid, removigUserId, badgeGrantId)
        self.execute_sql(sql, commit=True)

    def remove_users_bagde_by_system(self):
        sql = 'delete from user_badges WHERE user_badges.badgeId IN (select id from badges where badges.adminawarded=0)'
        self.execute_sql(sql=sql, commit=True)

    def get_products(self):
        data = self.execute_get_sql('select * from product order by price, name')
        toReturn = {}
        for one in data:
            toReturn[one[0]] = {'id': one[0],
                                'name': one[1],
                                'price': one[2],
                                'size': one[3],
                                'caffeine': one[4]}
        return toReturn

    def get_product_details(self, productId):
        data = self.execute_get_sql('select * from product where id=%s'%str(productId))
        if data:
            one = data[0]
            return {'id': one[0],
                    'name': one[1],
                    'price': one[2],
                    'size': one[3],
                    'caffeine': one[4]}
        else:
            raise ValueError('No Product with that ID ', id)

    def get_users(self, onlyNotValidated=False, active=None):
        # TODO move to dict
        addSql = ''
        if active is not None:
            addSql = ' and active=%d'%active
        sql = 'select * from user where id > 0 %s order by username' % addSql
        if onlyNotValidated:
            sql = 'select * from user where validated=0 and id > 0 %s order by username' % addSql
        data = self.execute_get_sql(sql)
        toReturn = {}
        for one in data:
            toReturn[one[0]] = {'id': one[0],
                                'email': one[1],
                                'username': one[2],
                                'rating': one[3],
                                'creator': one[4],
                                'validated': one[5],
                                'added': one[6],
                                'active': one[7]
                                }
        return toReturn

    def get_users_stats(self):
        toReturn = {}
        sql = 'select  buyer, count(buyer) from all_list where buyer!=to_whom group by buyer'
        for one in self.execute_get_sql(sql):
            toReturn[one[0]] = {'consumed': 0, 'served': 0, 'offered': one[1]}

        sql = 'select  to_whom, count(to_whom) from all_list where buyer!=to_whom group by to_whom'
        #sql = 'select  to_whom, count(to_whom) from all_list group by to_whom'
        for one in self.execute_get_sql(sql):
            try:
                toReturn[one[0]]['consumed'] = one[1]
            except KeyError:
                toReturn[one[0]] = {'consumed': one[1], 'served': 0, 'offered': 0}

        sql = 'select buyer, count(buyer) from (select buyer from all_list where buyer!=to_whom group by date) group by buyer'
        for one in self.execute_get_sql(sql):
            try:
                toReturn[one[0]]['served'] = one[1]
            except KeyError:
                toReturn[one[0]] = {'served': one[1], 'consumed': 0, 'offered': 0}

        return toReturn

    def get_last_transaction(self, n=None):
        extra = ''
        if n is not None:
            extra = ' desc limit %d' % n
        sql = 'select date from contract group by date order by date %s' % extra
        return self.execute_get_sql(sql)

    def get_admins(self):
        #badges 7(admin) and 8(badgeadmin)
        sql = 'select userId, email, username, badgeId from user_badges join user on user_badges.userId=user.id where user_badges.valid=1 and (user_badges.badgeId=7 or user_badges.badgeId=8)'
        toReturn = {'admin': {},
                    'badgeadmin': {}}
        for one in self.execute_get_sql(sql):
            if one[3] == 7:
                toReturn['admin'][one[1]] = (one[0], one[2])
            if one[3] == 8:
                toReturn['badgeadmin'][one[1]] = (one[0], one[2])

        return toReturn

    def get_username_and_email(self, id=None, email=None):
        if id is None and email is None:
            raise ValueError('Need at least one parameter!')
        if id is None:
            sql = 'select id,username,email,rating from user where email=\'%s\'' % email
        if email is None:
            sql = 'select id,username,email,rating from user where id=\'%s\'' % id
        data = self.execute_get_sql(sql)
        user = {}
        for one in data:
            user['id'] = one[0]
            user['username'] = one[1]
            user['email'] = one[2]
            user['scoring'] = one[3]
        return user

    def get_job_summary(self, jobDate):
        sql = "select * from contract where date like \'{}%\' ".format(jobDate)
        data = self.execute_get_sql(sql)
        toReturn = {'date': jobDate, 'jobs': []}
        for one in data:
            toReturn['jobs'].append({'who': one[1],
                                     'to_whom': one[2],
                                     'what': one[3],
                                     'creator': one[5],
                                     'date': one[4]})
        return toReturn

    def get_jobs_summary(self, today=False, buffer_seconds=3*3600, withUser=None):
        sqlOnUser=''
        if withUser is not None:
            sqlOnUser = ' where (buyer like \'%s\' or to_whom like \'%s\') '%(withUser, withUser)
        if today:
            now = datetime.now() - timedelta(seconds=buffer_seconds)
            sql = 'select * from all_list where date > \'%s\'   %s  order by date desc' % (now.strftime("%Y-%m-%d %H:%M:%S"), sqlOnUser.replace('where','and'))
        else:
            sql = 'select * from all_list %s order by date desc'%(sqlOnUser)
        return self.execute_get_sql(sql)

    def get_summary_per_user(self, user):
        return self.execute_get_sql('select * from all_list where buyer like \'\% %s \%\' '%user)

    def get_top_buyers(self):
        return self.execute_get_sql('select buyer, count(buyer) count, sum(price) total_spent, max(buyer_rating) from all_list group by buyer order by count desc limit 5')

    def get_top_candidates(self):
        return self.execute_get_sql('select id, username, rating from user order by rating limit 5')

    def get_main_statistics(self):
        lastDateBuyer = self.execute_get_sql('select date,buyer from all_list group by date order by date desc limit 1')[0]
        totalBudgetSpent = self.execute_get_sql('select sum(price), count(price) from all_list')[0]
        totalServings = self.execute_get_sql('select count(distinct(date)) from all_list')[0][0]
        totalRatingBalance = self.execute_get_sql('select sum(rating) from user ')[0][0]
        onePlusBadges = self.execute_get_sql('select sum(effect) from (select * from user_badges join badges on badges.id=user_badges.badgeId where user_badges.valid=1 and effect = 1)')[0][0]
        oneMinusBadges = self.execute_get_sql('select sum(effect) from (select * from user_badges join badges on badges.id=user_badges.badgeId where user_badges.valid=1 and effect = -1)')[0][0]
        activeUsers = self.execute_get_sql('select count(id) from user where active>0 and id>0 ')[0][0]
        return {
            'lastDate': lastDateBuyer[0],
            'lastServant': lastDateBuyer[1],
            'totalServings': totalServings,
            'totalBudgetSpent': totalBudgetSpent[0],
            'totalJobs': totalBudgetSpent[1],
            'totalRating': totalRatingBalance,
            'oneMinusBadges': oneMinusBadges,
            'onePlusBadges': onePlusBadges,
            'activeUsers': activeUsers,
        }

    def get_dependecy_data(self):
        sql = 'select buyer, to_whom, count(to_whom) from all_list where buyer!=to_whom group by buyer, to_whom '
        return self.execute_get_sql(sql)

    def get_points_evolution(self, specificUser=None):
        dateToUserPoints = {}
        users = {}
        for user in self.get_users().values():
            users[user['id']] = user['username']
        for a in self.get_last_transaction():
            dateAndTime = a[0]
            date = dateAndTime.split(' ')[0]
            scoringToDate = self.calculate_actal_scoring(date=dateAndTime,
                                                         updateDb=False,
                                                         commit=False)[1]
                                                        # second paramter
            dateToUserPoints[date] = {}
            for userId in scoringToDate.keys():
                if specificUser is not None and userId != specificUser:
                    continue
                dateToUserPoints[date][users[userId]] = scoringToDate[userId]
        userToPointsEvolution = {}
        for user in users.values():
            userToPointsEvolution[user] = []
            lastValue = DUMMY_VALUE
            for date in dateToUserPoints.keys():
                value = dateToUserPoints[date].get(user, DUMMY_VALUE)
                if value == DUMMY_VALUE or value == lastValue:
                    continue
                userToPointsEvolution[user].append((date,  value,
                                                    (date.split('-')[0],
                                                     int(date.split('-')[1])-1,
                                                     date.split('-')[2])))
                lastValue = value
        return userToPointsEvolution

    def get_products_summary(self, userId=None):
        sqlUser=''
        if userId is not None:
            sqlUser=' where to_whom=%d ' % userId
        data = self.execute_get_sql('select contract.product pId, product.name, count(contract.product) pCount, sum(product.price) pPrice, sum(product.size) pSize, sum(product.caffeine) pCaf from contract join product on contract.product=product.id %s group by contract.product'%sqlUser)
        result = {}
        for one in data:
            result[one[0]] = {'name': one[1],
                              'value': one[2],
                              'totalprice': one[3],
                              'totalsize': one[4],
                              'totalcaffeine': one[5]}
        return result

    def add_debt_transfer(self, rating, fromUserId, toUserId):
        self.execute_sql('insert into rating_transfer (value, from_user, to_user, date, valid) values (%d, %d, %d, CURRENT_TIMESTAMP,1)' % (rating, fromUserId, toUserId),
                         commit=True)

    def get_debt_transfer_history(self):
        history = {}
        data = self.execute_get_sql('select a.id, from_user, a.username, to_user, user.username, date, value, valid from (select * from rating_transfer left join user on user.id= from_user) a  left join user on a.to_user=user.id')
        for one in data:
            history[one[0]]={'transferId': one[0],
                             'fromUserId': one[1],
                             'fromUserName': one[2],
                             'toUserId': one[3],
                             'toUserName': one[4],
                             'date': one[5],
                             'value': one[6],
                             'valid': one[7]}
        return history

    def close_db(self):
        self.con.close()
