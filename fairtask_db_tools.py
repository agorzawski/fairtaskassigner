import sqlite3
import cgi, cgitb
from datetime import datetime, timedelta
from fairtask_scoring import fairtask_scoring
import os

# use db/dbScheme.sql to create an sqlite db
DATABASE_NAME = os.environ.get("FN_DB_TO_USE", default=False)

'''
utility class for SQLite connection
'''
class fairtaskDB:
    def __init__(self):
        self.load_db()

    def load_db(self):
        self.con = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
        self.c = self.con.cursor()

    def add_user(self, name, email, creator):
        try:
            self.c.execute('insert into user (email, username, rating, creator) values (\'%s\', \'%s\', 1.0, %s)' %(email, name, creator) )
            self.con.commit()
            return True
        except IntegrityError:
            return False

    def add_product(self, name, price):
        try:
            self.c.execute('insert into user vales (%s, %s) '%(name, price))
            self.con.commit()
            return True
        except IntegrityError:
            return False

    def add_transaction(self, who, whom, what,creator, commit=False):
        if who==-1 or whom==-1 or what==-1:
            raise ValueError('Cannot save transaction for an unspecified person or goods!')
        else:
            sql = 'insert into  contract (buyer, seller, product, date, creator) values (%s, %s, %s, CURRENT_TIMESTAMP, %s)'%(who, whom, what,creator)
            try:
                self.c.execute(sql)
                self.calculate_actal_scoring()
                if commit:
                    self.con.commit()
                return True
            except IntegrityError:
                return False

    def add_to_bucket(self, whom, what):
        if int(whom)>0 and int(what)>0:
            sql = 'insert into  contract_temp (to_whom, product) values (%s, %s)'%(whom, what)
            self.c.execute(sql)
            self.calculate_actal_scoring()
            self.con.commit()

    def finalize_bucket_list(self, loggedUser, who):
        self.c.execute('select * from contract_temp')
        for whomWhat in self.c.fetchall():
            if int(who) == int(whomWhat[0]):
                continue
            self.add_transaction(who, whomWhat[0], whomWhat[1], loggedUser)
        self.clean_bucket()

    def clean_bucket(self):
        self.c.execute('delete from contract_temp')
        self.con.commit()

    def calculate_actal_scoring(self, commit=False, presentContractors=[]):
        self.c.execute('select buyer, seller, product from contract')
        data = self.c.fetchall()
        scoring = fairtask_scoring()
        result = scoring.recalculate_scoring(data, presentContractors=presentContractors)
        for one in result.keys():
            self.c.execute('update user set rating=%f where id=%s'%(result[one], one))
        if commit:
            try:
                self.con.commit()
                return True
            except IntegrityError:
                return False

    def get_bucket(self):
        self.c.execute('select username, what, rating from (select to_whom whom, name what from contract_temp join product on product.id = product) join user on user.id=whom')
        data = self.c.fetchall()
        return data

    def get_username_and_email(self, id=None, email=None):
        if id is None and email is None:
            raise ValueError('Need at least one parameter!')
        if id is None:
            self.c.execute('select id,username,email from user where email=\'%s\''%email)
        if email is None:
            self.c.execute('select id,username,email from user where id=\'%s\''%id)
        data = self.c.fetchall()
        return data

    def get_products(self):
        self.c.execute('select * from product order by price, name')
        data = self.c.fetchall()
        return data

    def get_users(self):
        self.c.execute('select * from user order by username')
        data = self.c.fetchall()
        return data

    def get_jobs_summary(self, today=False, buffer_seconds=3*3600):
        if today:
            now = datetime.now() - timedelta(seconds=buffer_seconds)
            self.c.execute('select * from all_list where date > \'%s\' order by date desc'%now.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.c.execute('select * from all_list order by date desc')
        data = self.c.fetchall()
        return data

    def get_summary_per_user(self, user):
        self.c.execute('select * from all_list where buyer like \'\% %s \%\' '%user)
        data = self.c.fetchall()
        return data

    def get_top_buyers(self):
        self.c.execute('select buyer, count(buyer) count, sum(price) total_spent, max(buyer_rating) from all_list group by buyer order by count desc limit 3')
        data = self.c.fetchall()
        return data

    def get_top_candidates(self):
        self.c.execute('select username, rating from user order by rating limit 3')
        data = self.c.fetchall()
        return data

    def close_db(self):
        self.con.close()
