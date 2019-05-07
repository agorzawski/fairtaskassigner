'''
Flask App for serving three pages server based on templates and storage connector.
'''

from fairtask_db_tools import fairtaskDB
from flask import Flask, render_template, request, json, redirect, url_for, session
#from flask_oauth import OAuth
#from flask_googlelogin import GoogleLogin

app = Flask(__name__)
storage = fairtaskDB()
loggedUser = 4;

def getLoggedUsernameEmail(loggedUser = loggedUser):
    if loggedUser == -1:
        #TODO get the email from the
        #return storage.getUsernameAndEmail(email=emailFromCookies)[0]
        return (None,None)
    else:
        return storage.getUsernameAndEmail(id=4)[0]

@app.route("/")
@app.route('/main')
def main():
    loggedUsernameEmail = getLoggedUsernameEmail(loggedUser = loggedUser)
    top3 = storage.get_top_buyers()
    allJobs = storage.get_jobs_summary()
    candidates = storage.get_top_candidates()
    return render_template('index.html', top3=top3,
                           summaryJobs=allJobs,
                           candidates=candidates,
                           loggedUsernameEmail=loggedUsernameEmail)

#### ADDDING JOBS
@app.route('/registerJob', methods=['POST'])
def registerJobs():
    _name = request.form['inputName']
    _product = request.form['inputProduct']
    if _name and _product:
        storage.add_transaction(loggedUser, _name, _product)
        return redirect(url_for('addJobs'))
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})

@app.route('/addJobs')
def addJobs():
    loggedUsernameEmail = getLoggedUsernameEmail(loggedUser = loggedUser)
    top3 = storage.get_top_buyers()
    users = storage.get_users()
    products = storage.get_products()
    buffer = 3*3600
    summaryToday = storage.get_jobs_summary(today=True, buffer_seconds=buffer)
    return render_template('addjobs.html',
                           todaysJobs=summaryToday,
                           users=users,
                           products=products, hours=int(buffer/3600),
                           loggedUsernameEmail=loggedUsernameEmail)

#### ADDDING BUDDYS
@app.route('/showSignUp')
def showSignUp():
    users = storage.get_users()
    products = storage.get_products()
    summaryToday = storage.get_jobs_summary(today=True)
    loggedUsernameEmail = getLoggedUsernameEmail(loggedUser = loggedUser)
    return render_template('signup.html', users=users, products=products,
                           loggedUsernameEmail=loggedUsernameEmail)

@app.route('/signUp', methods=['POST'])
def signUp():
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    if _name and _email:
        storage.add_user(_name, _email)
        return redirect(url_for('showSignUp'))
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})

if __name__ == "__main__":
    app.run()
