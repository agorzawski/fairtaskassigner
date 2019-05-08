'''
Flask App for serving three pages web server based on templates and storage connector.
'''

from fairtask_db_tools import fairtaskDB
from flask import Flask, render_template, request, json, redirect, url_for, session
from flask_oauth import OAuth
import os

DEBUG = os.environ.get("FN_DEBUG", default=False)
LISTEN_HOST_IP = os.environ.get("FN_LISTEN_HOST_IP", default='127.0.0.1')

# You must configure these 3 first values from Google APIs console
# https://code.google.com/apis/console
# here they are read from the ENV that is setup on server startup
GOOGLE_CLIENT_ID = os.environ.get("FN_GOOGLE_CLIENT_ID", default=False)
GOOGLE_CLIENT_SECRET = os.environ.get("FN_GOOGLE_CLIENT_SECRET", default=False)
REDIRECT_URI = os.environ.get("FN_REDIRECT_URI", default=False)  # one of the Redirect URIs from Google APIs console
BASE_URL='https://www.google.com/accounts/'
AUTHORIZE_URL='https://accounts.google.com/o/oauth2/auth'
SCOPE_URL='https://www.googleapis.com/auth/userinfo.email'
ACCESS_TOKEN_URL='https://accounts.google.com/o/oauth2/token'
USER_INFO_URL='https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token='

HOUR_IN_SECONDS = 3600

app = Flask(__name__)
app.debug = DEBUG
app.secret_key = 'development key'
storage = fairtaskDB()
oauth = OAuth()
google = oauth.remote_app('google',
                          base_url=BASE_URL,
                          authorize_url=AUTHORIZE_URL,
                          request_token_url=None,
                          request_token_params={'scope':SCOPE_URL ,
                                                'response_type': 'code'},
                          access_token_url=ACCESS_TOKEN_URL,
                          access_token_method='POST',
                          access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)


@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token, ''
    return redirect(url_for('main'))

@google.tokengetter
def get_access_token():
    return session.get('access_token')

def getUserInfo(access_token):
    import urllib3, json
    http = urllib3.PoolManager()
    res = http.request('GET',USER_INFO_URL+access_token)
    userData=json.loads(res.data.decode('utf-8'))
    return userData

def getLoggedUsernameEmailPicture():
    access_token = get_access_token()[0]
    userData = getUserInfo(access_token)
    email, picture  =  (userData['email'], userData['picture'])
    id, username, emailLocal= storage.getUsernameAndEmail(email=email)[0]
    if emailLocal == email:
        return {'id':id, 'email':email, 'username':username, 'picture':picture}

def isLoginValid():
    access_token = get_access_token()
    if access_token is not None:
        userDetails = getUserInfo(access_token[0])
        try:
            userDetails['error'] ## 99% cases when some cookie/session problem
            return False
        except KeyError:
            #TODO Handle some error cases here
            return True
    return False

###############
#######   MAIN PAGES and actions
##############
@app.route('/login')
def login():
    if not isLoginValid():
        callback=url_for('authorized', _external=True)
        return google.authorize(callback=callback)
    else:
        return redirect(url_for('main'))

@app.route("/")
@app.route('/main')
def main():
    googleSession=False
    loggedUsernameEmail=()
    if isLoginValid():
        googleSession=True
        loggedUsernameEmail=getLoggedUsernameEmailPicture()
    top3 = storage.get_top_buyers()
    allJobs = storage.get_jobs_summary()
    candidates = storage.get_top_candidates()
    return render_template('index.html',
                           top3=top3,
                           summaryJobs=allJobs,
                           candidates=candidates,
                           googleSession=googleSession,
                           loggedUsernameEmail=loggedUsernameEmail)

@app.route('/addJobs')
def addJobs():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    users = storage.get_users()
    products = storage.get_products()
    buffer = 5*HOUR_IN_SECONDS
    summaryToday = storage.get_jobs_summary(today=True, buffer_seconds=buffer)
    return render_template('addjobs.html',
                           todaysJobs=summaryToday,
                           users=users,
                           products=products,
                           hours=int(buffer/HOUR_IN_SECONDS),
                           loggedUsernameEmail=loggedUsernameEmail)

@app.route('/showSignUp')
def showSignUp():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    users = storage.get_users()
    products = storage.get_products()
    summaryToday = storage.get_jobs_summary(today=True)
    return render_template('signup.html',
                           users=users,
                           products=products,
                           loggedUsernameEmail=loggedUsernameEmail)

@app.route('/signUp', methods=['POST'])
def signUp():
    if not isLoginValid():
        return redirect(url_for('login'))

    _name = request.form['inputName']
    _email = request.form['inputEmail']
    if _name and _email:
        storage.add_user(_name, _email)
        return redirect(url_for('showSignUp'))
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})

@app.route('/registerJob', methods=['POST'])
def registerJobs():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    _name = request.form['inputName']
    _product = request.form['inputProduct']
    if _name and _product:
        storage.add_transaction(loggedUsernameEmail['id'], _name, _product)
        return redirect(url_for('addJobs'))
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})

if __name__ == "__main__":
    import logging
    logging.basicConfig(filename='error.log',level=logging.DEBUG)
    app.run(host=LISTEN_HOST_IP, port=8040)
