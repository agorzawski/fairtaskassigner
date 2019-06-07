'''
Flask App for serving three pages web server based on templates
and storage connector.
'''

from fairtask_db_tools import fairtaskDB
import fairtask_badges as badges
import fairtask_utils
from flask import Flask, render_template, request, json, redirect, url_for, session, flash, get_flashed_messages
from flask_oauth import OAuth
import os

DEBUG = os.environ.get("FN_DEBUG", default=False)
HOST_PORT = os.environ.get("FN_HOST_PORT", default='8040')
LISTEN_HOST_IP = os.environ.get("FN_LISTEN_HOST_IP", default='127.0.0.1')
ADMIN_EMAIL = os.environ.get("FN_ADMIN_EMAIL", default=False)

# You must configure these 3 first values from Google APIs console
# https://code.google.com/apis/console
# here they are read from the ENV that is setup on server startup
GOOGLE_CLIENT_ID = os.environ.get("FN_GOOGLE_CLIENT_ID", default=False)
GOOGLE_CLIENT_SECRET = os.environ.get("FN_GOOGLE_CLIENT_SECRET", default=False)
# one of the Redirect URIs from Google APIs console
REDIRECT_URI = os.environ.get("FN_REDIRECT_URI", default=False)
BASE_URL = 'https://www.google.com/accounts/'
AUTHORIZE_URL = 'https://accounts.google.com/o/oauth2/auth'
SCOPE_URL = 'https://www.googleapis.com/auth/userinfo.email'
ACCESS_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
USER_INFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token='

HOUR_IN_SECONDS = 3600
NON_EXISTING_ID = -666
NON_SELECTED_VALUE = -1

app = Flask(__name__)
app.debug = DEBUG
app.secret_key = 'development key'
storage = fairtaskDB(allowCommit=True)
oauth = OAuth()
google = oauth.remote_app('google',
                          base_url=BASE_URL,
                          authorize_url=AUTHORIZE_URL,
                          request_token_url=None,
                          request_token_params={'scope': SCOPE_URL,
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
def getAccessToken():
    return session.get('access_token')


def getUserInfo(access_token):
    import urllib3
    import json
    http = urllib3.PoolManager()
    res = http.request('GET', USER_INFO_URL+access_token)
    userData = json.loads(res.data.decode('utf-8'))
    return userData


def getLoggedUsernameEmailPicture():
    access_token = getAccessToken()[0]
    userData = getUserInfo(access_token)
    email, picture = (userData['email'], userData['picture'])
    localUserData = storage.get_username_and_email(email=email)
    if len(localUserData):
        id, username, emailLocal = localUserData[0]
        if emailLocal == email:
            favProduct = storage.get_favorite_product(id)

            return {'id': id, 'email': email,
                    'username': username,
                    'picture': picture,
                    'idProduct':favProduct[0],
                    'productName': favProduct[1].upper()}
    else:
        return {'id': NON_EXISTING_ID, 'email': email,
                'username': '', 'picture': picture,
                    'idProduct':NON_SELECTED_VALUE,
                    'productName': 'NONE'}


def isLoginValid():
    access_token = getAccessToken()
    if access_token is not None:
        userDetails = getUserInfo(access_token[0])
        try:
            userDetails['error']  # 99% cases when some cookie/session problem
            return False
        except KeyError:
            # TODO Handle some error cases here
            return True
    return False


def isAnAdmin():
    localId = getLoggedUsernameEmailPicture()
    adminsList = storage.get_admins()
    if localId['email'] in adminsList['admin'].keys() \
        or localId['email'] in adminsList['badgeadmin'].keys():
        return True
    return False


@app.route('/login')
def login():
    if not isLoginValid():
        callback = url_for('authorized', _external=True)
        return google.authorize(callback=callback)
    else:
        return redirect(url_for('main'))


@app.route('/logout')
def logout():
    session['access_token'] = 'LOGOUT', ''
    return redirect(url_for('main'))


@app.route("/")
@app.route('/main')
def main():
    googleSession = False
    loggedUsernameEmail = ()
    getLoggedUserBadges = ()
    inBucket = False
    if isLoginValid():
        googleSession = True
        loggedUsernameEmail = getLoggedUsernameEmailPicture()
        inBucket = storage.check_if_in_bucket(loggedUsernameEmail['id'])
        getLoggedUserBadges = storage.get_users_badges(userId=loggedUsernameEmail['id'])
    lastDate = storage.get_last_transaction(n=1)[0]
    top3 = storage.get_top_buyers()
    candidates = storage.get_top_candidates()
    getAssignedBadges = storage.get_users_badges()
    return render_template('index.html',
                           top3=top3,
                           lastDate=lastDate,
                           candidates=candidates,
                           googleSession=googleSession,
                           loggedUsernameEmail=loggedUsernameEmail,
                           inBucket=inBucket,
                           assignedBadges=getAssignedBadges,
                           loggedUserBadges=getLoggedUserBadges)


@app.route('/addJobs')
def addJobs():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    if loggedUsernameEmail['id'] == NON_EXISTING_ID:
        return redirect(url_for('showSignUp'))
    inBucket = storage.check_if_in_bucket(loggedUsernameEmail['id'])
    googleSession = True
    users = storage.get_users()
    products = storage.get_products()
    allJobs = storage.get_jobs_summary()
    badgesTimeline = storage.get_badge_grant_history()
    eventsTimeLine = fairtask_utils.combineEvents(allJobs, badgesTimeline)
    summaryToday = storage.get_bucket()
    getLoggedUserBadges = storage.get_users_badges(userId=loggedUsernameEmail['id'])
    return render_template('addjobs.html',
                           todaysJobs=summaryToday,
                           eventsTimeLine=eventsTimeLine,
                           loggedUserBadges=getLoggedUserBadges,
                           users=users,
                           products=products,
                           googleSession=googleSession,
                           inBucket=inBucket,
                           loggedUsernameEmail=loggedUsernameEmail)


@app.route('/stats')
def stats():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    users = storage.get_users()
    products = storage.get_products()
    notValidatedUsers = storage.get_users(onlyNotValidated=True)
    adminsList = storage.get_admins()
    getUsersStats = storage.get_users_stats()
    getAllBadges = storage.get_all_badges()
    getAssignedBadges = storage.get_users_badges()
    allValidities = False
    if isAnAdmin():
        allValidities = True
    grantedBadges = storage.get_badge_grant_history(allValidities=allValidities)
    getLoggedUserBadges = storage.get_users_badges(userId=loggedUsernameEmail['id'])
    return render_template('stats.html',
                           users=users,
                           notValidatedUsers=notValidatedUsers,
                           products=products,
                           allBadges=getAllBadges,
                           adminsList=adminsList,
                           usersStats=getUsersStats,
                           assignedBadges=getAssignedBadges,
                           loggedUserBadges=getLoggedUserBadges,
                           grantedBadges=grantedBadges,
                           loggedUsernameEmail=loggedUsernameEmail,
                           invalidId=NON_EXISTING_ID,
                           nonSelectedId=NON_SELECTED_VALUE)


@app.route('/showSignUp')
def showSignUp():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    users = storage.get_users()
    notValidatedUsers = storage.get_users(onlyNotValidated=True)
    getLoggedUserBadges = storage.get_users_badges(userId=loggedUsernameEmail['id'])
    adminsList = storage.get_admins()
    adminBadges = False
    if loggedUsernameEmail['email'] in adminsList['admin'].keys():
        adminBadges = True
    badgesToGrant = storage.get_all_badges(badgeUniqe=True,
                                           adminBadges=adminBadges)
    return render_template('signup.html',
                           users=users,
                           notValidatedUsers=notValidatedUsers,
                           loggedUserBadges=getLoggedUserBadges,
                           loggedUsernameEmail=loggedUsernameEmail,
                           adminsList=adminsList,
                           badgesToGrant=badgesToGrant,
                           invalidId=NON_EXISTING_ID,
                           nonSelectedId=NON_SELECTED_VALUE)


@app.route('/signUp', methods=['POST'])
def signUp():
    if not isLoginValid():
        return redirect(url_for('login'))
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    try:
        _assignedNameId = int(request.form['assignedNameId'])
    except KeyError:
        _assignedNameId = NON_SELECTED_VALUE

    validated = 0
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    if _email and (_name or _assignedNameId != NON_SELECTED_VALUE):
        if loggedUsernameEmail['id'] == NON_EXISTING_ID:
            validated = 1
        if _assignedNameId == NON_SELECTED_VALUE:
            storage.add_user(_name, _email,
                             loggedUsernameEmail['id'],
                             validated=validated)
        else:
            storage.update_user(_assignedNameId, _email,
                                loggedUsernameEmail['id'],
                                validated=validated)
        flash('User %s/%s successfuly added!' % (_name, _email))
        return redirect(url_for('showSignUp'))
    else:
        flash("Cannot add user!")
    return redirect(url_for('showSignUp'))


@app.route('/registerJob', methods=['POST','GET'])
def registerJob():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    if loggedUsernameEmail['id'] == NON_EXISTING_ID:
        return redirect(url_for('showSignUp'))
    try:
        if request.form:
            _name = int(request.form['inputName'])
            _product = int(request.form['inputProduct'])
    except ValueError:
        flash('Cannot register this order, select correct pair TO WHOM & WHAT')
        return redirect(url_for('addJobs'))
    try:
        if request.args:
            _name = int(request.args.get('inputName', -1))
            _product = int(request.args.get('inputProduct', -1))
    except ValueError:
        flash('Cannot register this order, select correct pair TO WHOM & WHAT')
        return redirect(url_for('addJobs'))

    if _name > 0 and _product > 0:
        storage.add_to_bucket(_name, _product)
        flash('Registered in the whish list...')
    else:
        flash('Cannot register this order, select correct pair TO WHOM & WHAT')
    return redirect(url_for('addJobs'))


@app.route('/emptyBucket', methods=['POST'])
def emptyBucket():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    if loggedUsernameEmail['id'] == NON_EXISTING_ID:
        return redirect(url_for('showSignUp'))
    storage.clean_bucket()
    flash('Wishlist cleared!')
    return redirect(url_for('addJobs'))


@app.route('/finalizeJob', methods=['POST'])
def finalizeJob():
    if not isLoginValid():
        return redirect(url_for('login'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    if loggedUsernameEmail['id'] == NON_EXISTING_ID:
        return redirect(url_for('showSignUp'))
    try:
        _nameId = int(request.form['finalzeName'])
    except ValueError:
        flash('Wrong name: %s' % request.form['finalzeName'])
        return redirect(url_for('addJobs'))
    if _nameId < 0:
        return redirect(url_for('addJobs'))
    bucketContent = storage.get_bucket_raw()
    if len(bucketContent) < 2:
        flash('Cannot proceed with less then three orders!')
        return redirect(url_for('addJobs'))

    for whomWhat in bucketContent:
        storage.add_transaction(_nameId, whomWhat[0], whomWhat[1],
                                loggedUsernameEmail['id'])
    storage.clean_bucket()
    dates = storage.get_last_transaction(n=1)
    for date in dates:
        actualbadges = badges.get_current_badges(date[0], storage=storage)
        for oneBadge in actualbadges:
            storage.insert_user_badges(*oneBadge)
        if len(actualbadges):
            flash('New badges awarded!')
    storage.calculate_actal_scoring(commit=True)
    flash('Order registered!')
    return redirect(url_for('main'))


@app.route('/grantBadge', methods=['POST'])
def grantBadge():
    if not isLoginValid():
        return redirect(url_for('login'))
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    try:
        _name = int(request.form['nameIdToGrant'])
        _badge = int(request.form['badgeId'])
    except ValueError:
        return redirect(url_for('showSignUp'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    if _name > 0 and _badge > 0:
        storage.insert_user_badges(_name, _badge, None, loggedUsernameEmail['id'])
        storage.calculate_actal_scoring(commit=True)
    return redirect(url_for('showSignUp'))


@app.route('/removeBucketItem', methods=['GET'])
def removeBucketItem():
    if not isLoginValid():
        return redirect(url_for('login'))
    try:
        what = int(request.args.get('what', -1))
        towhom = int(request.args.get('towhom', -1))
    except ValueError:
        return redirect(url_for('main'))
    if what > 0 and towhom > 0:
        storage.remove_item_in_bucket(towhom, what)
        flash('Removed one entry form the bucket')
    return redirect(url_for('addJobs'))


@app.route('/modifyBadge', methods=['GET'])
def modifyBadge():
    if not isLoginValid():
        return redirect(url_for('login'))
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    loggedUsernameEmail = getLoggedUsernameEmailPicture()
    try:
        badgeId = int(request.args.get('grantId', -1))
        valid = int(request.args.get('valid', 0))
    except ValueError:
        flash('Error in submited vaules for badge modification!')
        return redirect(url_for('stats'))
    if badgeId > 0 and (valid == 1 or valid == 0):
        storage.remove_user_bagde(badgeId, valid, loggedUsernameEmail['id'])
        flash('Modified Badge!')
    else:
        flash('Error in submited vaules for badge modification!')
    return redirect(url_for('stats'))


@app.route('/addProduct', methods=['POST'])
def addProduct():
    if not isLoginValid():
        return redirect(url_for('login'))
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    _name = request.form['productName']
    try:
        _price = float(request.form['productPrice'])
    except ValueError:
        return redirect(url_for('showSignUp'))
    storage.add_product(_name, _price)
    return redirect(url_for('stats'))


@app.route('/calculateScoring', methods=['POST'])
def calculateScoring():
    if not isLoginValid():
        return redirect(url_for('login'))
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))

    storage.calculate_actal_scoring(commit=True)
    flash('Scoring recalculated!')
    return redirect(url_for('stats'))


if __name__ == "__main__":
    import logging
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    app.run(host=LISTEN_HOST_IP, port=HOST_PORT)
