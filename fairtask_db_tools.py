import sqlite3
import cgi, cgitb
from datetime import datetime, timedelta
from fairtask_scoring import fairtask_scoring

database_name = "db/CoffeTaskDB.db"

'''
utility class for SQLite connection
'''

class fairtaskDB:
    def __init__(self):
        self.load_db()

    def load_db(self):
        self.con = sqlite3.connect(database_name)
        self.c = self.con.cursor()

    def add_user(self, name, email):
        err = self.c.execute('insert into user (email, username, rating) values (\'%s\', \'%s\', 1.0)' %(email, name) )
        self.con.commit()
        if err:
            print(err)

    def add_product(self, name, price):
        err = self.c.execute('insert into user vales (%s, %s) '%(name, price))
        self.con.commit()
        if err:
            print(err)

    def add_transaction(self, who, whom, what):
        if who==-1 or whom==-1 or what==-1:
            raise ValueError('Cannot save transaction for an unspecified person or goods!')
        else:
            sql = 'insert into  contract (buyer, seller, product, date) values (%s, %s, %s, CURRENT_TIMESTAMP)'%(who, whom, what)
            self.c.execute(sql)
            self.calculate_actal_scoring()
            self.con.commit()

    def calculate_actal_scoring(self, commit=False):
        self.c.execute('select buyer, seller, product from contract')
        data = self.c.fetchall()
        scoring = fairtask_scoring()
        result = scoring.recalculate_scoring(data)
        for one in result.keys():
            self.c.execute('update user set rating=%f where id=%s'%(result[one], one))
        if commit:
            self.con.commit()

    def getUsernameAndEmail(self, id=None, email=None):
        if id is None and email is None:
            raise ValueError('Need at least one parameter!')
        if id is None:
            self.c.execute('select username,email from user where email=\'%s\''%email)
        if email is None:
            self.c.execute('select username,email from user where id=\'%s\''%id)
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
