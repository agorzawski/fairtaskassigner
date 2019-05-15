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
    def __init__(self):
        self.load_db()

    def load_db(self):
        self.con = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
        self.c = self.con.cursor()

    def execute_sql(self, sql, commit=False):
        try:
            errors = []  # TODO add SQL injection check
            if len(errors) > 0:
                return False
            self.c.execute(sql)
            if commit:
                self.con.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def execute_get_sql(self, sql):
        self.c.execute(sql)
        data = self.c.fetchall()
        return data

    def add_user(self, name, email, creator, validated=0):
        sql = 'insert into user (email, username, rating, creator, validated) values (\'%s\', \'%s\', 1.0, %s, %s)' % (email, name, creator, validated)
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
            sql = 'insert into contract (buyer, seller, product, date, creator) values (%s, %s, %s, CURRENT_TIMESTAMP, %s)' % (who, whom, what,creator)
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
        sql = 'SELECT product, COUNT(product) AS vo FROM contract where seller=%d GROUP BY product ORDER BY vo DESC LIMIT 1'%userId
        result =  self.execute_get_sql(sql)
        if len(result)>0:
            return self.get_product_details(result[0][0])
        else:
            return (NON_SELECTED_VALUE,'NOT FOUND')

    def finalize_bucket_list(self, loggedUser, who):
        for whomWhat in self.execute_get_sql('select * from contract_temp'):
            if int(who) == int(whomWhat[0]):
                continue
            self.add_transaction(who, whomWhat[0], whomWhat[1], loggedUser)
        self.clean_bucket()

    def clean_bucket(self):
        self.execute_sql('delete from contract_temp', commit=True)

    def calculate_actal_scoring(self, commit=False, presentContractors=[]):
        data = self.execute_get_sql('select buyer, seller, product from contract')
        scoring = fairtask_scoring()
        result = scoring.recalculate_scoring(data, presentContractors=presentContractors)
        for one in result.keys():
            self.c.execute('update user set rating=%f where id=%s' % (result[one], one))
        if commit:
            try:
                self.con.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_bucket(self):
        dataBucket = self.execute_get_sql('select username, what, rating, user.id from (select to_whom whom, name what from contract_temp join product on product.id = product) join user on user.id=whom')
        # (whom, what, rating) with origanl scorings
        if len(dataBucket):
            dataBucketSimple = self.execute_get_sql('select to_whom from contract_temp')
            data = self.execute_get_sql('select buyer, seller, product from contract')
            scoring = fairtask_scoring()
            presentContractors = []
            for one in dataBucketSimple:
                presentContractors.append(one[0])
            resultForOrdering = scoring.recalculate_scoring(data,
                                                 presentContractors=presentContractors)
            toReturn = []
            for data in dataBucket:
                toReturn.append((data[0],
                                 data[1],
                                 resultForOrdering.get(data[3], 0),))
            return toReturn
        return dataBucket

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
        return self.execute_get_sql('select username, rating from user order by rating limit 5')

    def close_db(self):
        self.con.close()
