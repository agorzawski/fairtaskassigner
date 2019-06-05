import sqlite3
from datetime import datetime, timedelta
from fairtask_scoring import fairtask_scoring
import os

# use db/dbScheme.sql to create an sqlite db
DATABASE_NAME = os.environ.get("FN_DB_TO_USE", default=False)
NON_SELECTED_VALUE = -1
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
        sql = 'insert into user (email, username, rating, creator, validated) values (\'%s\', \'%s\', 0.0, %s, %s)' % (email, name, creator, validated)
        self.execute_sql(sql, commit=True)

    def update_user(self, existingId, email, creator, validated=0):
        sql = 'update user set email=\'%s\', creator=%s, validated=%s where id=%s'%(email, creator, validated, existingId)
        self.execute_sql(sql, commit=True)

    def add_product(self, name, price):
        sql = 'insert into user vales (%s, %s) ' % (name, price)
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
        if len(result):
            return True
        return False

    def get_favorite_product(self, userId):
        sql = 'SELECT product, COUNT(product) AS vo FROM contract where to_whom=%d GROUP BY product ORDER BY vo DESC LIMIT 1'%userId
        result = self.execute_get_sql(sql)
        if len(result) > 0:
            return self.get_product_details(result[0][0])
        else:
            return (NON_SELECTED_VALUE, 'NOT FOUND')

    def get_scoring_from_badges(self):
        scoringFromBadgesData = self.execute_get_sql('select userId, sum(effect) from user_badges join badges on user_badges.badgeId = badges.id group by userId')
        scoringFromBadges = {}
        for one in scoringFromBadgesData:
            scoringFromBadges[one[0]] = one[1]
        return scoringFromBadges

    def calculate_actal_scoring(self, commit=False, presentContractors=[]):
        data = self.execute_get_sql('select buyer, to_whom, product from contract')
        scoring = fairtask_scoring()
        scoring.setScoringFromBadges(self.get_scoring_from_badges())
        result = scoring.recalculate_scoring(data, presentContractors=presentContractors)

        for one in result.keys():
            self.c.execute('update user set rating=%f where id=%s' % (result[one], one))
        if commit and self.ALLOW_COMMIT:
            try:
                self.con.commit()
                return True
            except sqlite3.IntegrityError:
                return False

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
        if len(dataBucket):
            dataBucketSimple = self.execute_get_sql('select to_whom from contract_temp')
            data = self.execute_get_sql('select buyer, to_whom, product from contract')
            scoring = fairtask_scoring()
            scoring.setScoringFromBadges(self.get_scoring_from_badges())
            presentContractors = []
            for one in dataBucketSimple:
                presentContractors.append(one[0])
            resultForOrdering = scoring.recalculate_scoring(data,
                                                 presentContractors=presentContractors)
            toReturn = []
            for data in dataBucket:
                toReturn.append((data[0],
                                 data[1],
                                 resultForOrdering.get(data[3], 0),
                                 data[3],
                                 data[4], ))
            return toReturn
        return dataBucket

    def get_granted_badges(self, date=None):
        sqlAdd = ""
        if date is not None:
            sqlAdd = " where date <=\'%s\'" % date
        sql = "select * from user_badges %s" % sqlAdd
        return self.execute_get_sql(sql)

    def get_all_badges(self, badgeUniqe=None):
        whereBadge = ''
        if badgeUniqe is not None:
            whereBadge = ' where adminawarded=1 '

        sql = 'select * from badges %s order by effect, name' % whereBadge
        return self.execute_get_sql(sql)

    def get_badge_grant_history(self):
        sql = 'select grantId, username, badgeName, img, date from badges_granted_timeline'
        return self.execute_get_sql(sql)

    def get_users_badges_timeline(self):
        sql = 'select * from badges_granted_timeline'
        return self.execute_get_sql(sql)

    def get_users_badges(self, userId=None):
        where = ' where user_badges.valid=1 '
        if userId is not None:
            where = ' where user_badges.valid=1 and user.id=%d ' % userId
        sql = 'select * from (select user.id userId, date, badgeId from user join user_badges on user.id=user_badges.userId %s ) a join badges on badges.id=a.badgeId' % (where)
        # TODO return as dict
        return self.execute_get_sql(sql)

    def insert_user_badges(self, badgeId, userId, date):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql='insert into user_badges (userId, badgeId, date, valid) values (\'%d\', \'%d\',\'%s\', 1)'  % (badgeId, userId, date)
        self.execute_sql(sql, commit=True)

    def remove_user_bagde(self, badgeGrantId):
        sql='update user_badges set valid=0 where id=%d' % badgeGrantId
        self.execute_sql(sql, commit=True)

    def get_products(self):
        return self.execute_get_sql('select * from product order by price, name')

    def get_product_details(self, productId):
        data = self.execute_get_sql('select * from product where id=%s'%str(productId))
        if len(data)>0:
            return data[0]
        else:
            raise ValueError('No Product with that ID ', id)

    def get_users(self, onlyNotValidated=False):
        sql = 'select * from user order by username'
        if onlyNotValidated:
            sql = 'select * from user where validated=0 order by username'
        return self.execute_get_sql(sql)

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
        sql = 'select userId, email, username, badgeId from user_badges join user on user_badges.userId=user.id where user_badges.badgeId=7 or user_badges.badgeId=8'
        toReturn = {'admin': {},
                    'badgeadmin': {}}
        for one in self.execute_get_sql(sql):
            if one[3] == 7:
                toReturn['admin'] = {one[1]: (one[0], one[2])}
            if one[3] == 8:
                toReturn['badgeadmin'] = {one[1]: (one[0], one[2])}

        return toReturn

    def get_username_and_email(self, id=None, email=None):
        if id is None and email is None:
            raise ValueError('Need at least one parameter!')
        if id is None:
            sql = 'select id,username,email from user where email=\'%s\'' % email
        if email is None:
            sql = 'select id,username,email from user where id=\'%s\'' % id
        return self.execute_get_sql(sql)

    def get_jobs_summary(self, today=False, buffer_seconds=3*3600):
        if today:
            now = datetime.now() - timedelta(seconds=buffer_seconds)
            sql = 'select * from all_list where date > \'%s\' order by date desc' % now.strftime("%Y-%m-%d %H:%M:%S")
        else:
            sql = 'select * from all_list order by date desc'
        return self.execute_get_sql(sql)

    def get_summary_per_user(self, user):
        return self.execute_get_sql('select * from all_list where buyer like \'\% %s \%\' '%user)

    def get_top_buyers(self):
        return self.execute_get_sql('select buyer, count(buyer) count, sum(price) total_spent, max(buyer_rating) from all_list group by buyer order by count desc limit 5')

    def get_top_candidates(self):
        return self.execute_get_sql('select id, username, rating from user order by rating limit 5')

    def close_db(self):
        self.con.close()
