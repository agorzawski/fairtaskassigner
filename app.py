'''
Flask App for serving three pages web server based on templates
and storage connector.
'''

from fairtask_db_tools import fairtaskDB
import fairtask_badges as badges
import fairtask_utils
from flask import Flask, render_template, request, json, redirect, url_for, session, flash, get_flashed_messages, make_response
from flask_oauth import OAuth
import os
import pytz
from pytz import timezone


DEBUG = os.environ.get("FN_DEBUG", default=False)
HOST_PORT = os.environ.get("FN_HOST_PORT", default='8040')
LISTEN_HOST_IP = os.environ.get("FN_LISTEN_HOST_IP", default='127.0.0.1')
ADMIN_EMAIL = os.environ.get("FN_ADMIN_EMAIL", default=False)
INSTANCE_NAME = os.environ.get("FN_INSTANCE_NAME", default='Coffee Tracker')
stream = os.popen('git describe --tags')
GIT_LAST_TAG = stream.read()
stream = os.popen('git rev-parse --abbrev-ref HEAD')
GIT_BRANCH = stream.read()
INSTANCE = {'name': INSTANCE_NAME,
            'ver': GIT_LAST_TAG+'/'+GIT_BRANCH,
            'ip': LISTEN_HOST_IP,
            'port': HOST_PORT,
            'admin': ADMIN_EMAIL,
            'db': os.environ.get("FN_DB_TO_USE", default=False),
            }

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
COOKIE_NAME_REDIRECT = 'targetbeforelogin'

HOUR_IN_SECONDS = 3600
NON_EXISTING_ID = -666
NON_SELECTED_VALUE = -1


def datetimefilter(value,
                   format="%Y-%m-%d %H:%M:%S",
                   tz=pytz.timezone('Europe/Paris')):
    from datetime import datetime
    value = datetime.strptime(value, format).astimezone(tz=pytz.timezone('UTC'))
    print(value)
    local_dt = value.astimezone(tz)
    print(local_dt)
    return local_dt.strftime(format)


app = Flask(__name__)
app.debug = DEBUG
app.secret_key = 'development key'
app.jinja_env.filters['datetimefilter'] = datetimefilter

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
    return redirect(url_for(request.cookies.get(COOKIE_NAME_REDIRECT, 'main')))


@google.tokengetter
def getAccessToken():
    return session.get('access_token')


def getUserInfo(access_token):
    import urllib3
    http = urllib3.PoolManager()
    try:
        res = http.request('GET', USER_INFO_URL+access_token)
        userData = json.loads(res.data.decode('utf-8'))
    except urllib3.exceptions.MaxRetryError:
        userData = {'email': 'test@local',
                    'picture': 'static/lock.png'
                    }
    return userData


def getLoggedUserDetails():
    access_token = getAccessToken()[0]
    userData = getUserInfo(access_token)
    email, picture = (userData['email'], userData['picture'])
    localUserData = storage.get_username_and_email(email=email)
    if len(localUserData.keys()):
        if localUserData['email'] == email:
            favProduct = storage.get_favorite_product(localUserData['id'])
            return {'id': localUserData['id'], 'email': localUserData['email'],
                    'username': localUserData['username'],
                    'picture': picture,
                    'idProduct': favProduct['id'],
                    'productName': favProduct['name'].upper(),
                    'scoring': localUserData['scoring']}
    else:
        return {'id': NON_EXISTING_ID, 'email': email,
                'username': '',
                'picture': picture,
                'idProduct': NON_SELECTED_VALUE,
                'productName': 'NONE',
                'scoring': 0}


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
    localId = getLoggedUserDetails()
    adminsList = storage.get_admins()
    if localId['email'] in adminsList['admin'].keys() \
        or localId['email'] in adminsList['badgeadmin'].keys():
        return True
    return False


def rememberTheInitialRequest(request, initialUrl):
    resp = make_response(request)
    resp.set_cookie(COOKIE_NAME_REDIRECT, initialUrl)
    return resp


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
        loggedUsernameEmail = getLoggedUserDetails()
        inBucket = storage.check_if_in_bucket(loggedUsernameEmail['id'])
        getLoggedUserBadges = storage.get_users_badges(userId=loggedUsernameEmail['id'])
    adminsList = storage.get_admins()
    generalStats = storage.get_main_statistics()
    topOrders = storage.get_top_orders()
    top3 = storage.get_top_buyers()
    candidates = storage.get_top_candidates()
    getAssignedBadges = storage.get_users_badges()
    summaryToday = storage.get_bucket()
    return render_template('index.html',
                           instance=INSTANCE,
                           top3=top3,
                           todaysJobs=summaryToday,
                           generalStats=generalStats,
                           topOrders=topOrders,
                           candidates=candidates,
                           adminsList=adminsList,
                           googleSession=googleSession,
                           loggedUsernameEmail=loggedUsernameEmail,
                           inBucket=inBucket,
                           assignedBadges=getAssignedBadges,
                           loggedUserBadges=getLoggedUserBadges)


@app.route('/addJobs')
def addJobs():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    loggedUsernameEmail = getLoggedUserDetails()
    if loggedUsernameEmail['id'] == NON_EXISTING_ID:
        return redirect(url_for('showSignUp'))
    inBucket = storage.check_if_in_bucket(loggedUsernameEmail['id'])
    users = storage.get_users(active=1)
    products = storage.get_products()
    adminsList = storage.get_admins()
    allJobs = storage.get_jobs_summary()
    badgesTimeline = storage.get_badge_grant_history()
    eventsTimeLine = fairtask_utils.combineEvents(allJobs, badgesTimeline)
    summaryToday = storage.get_bucket()
    getLoggedUserBadges = storage.get_users_badges(userId=loggedUsernameEmail['id'])
    return render_template('addjobs.html',
                           instance=INSTANCE,
                           todaysJobs=summaryToday,
                           eventsTimeLine=eventsTimeLine,
                           loggedUserBadges=getLoggedUserBadges,
                           users=users,
                           adminsList=adminsList,
                           products=products,
                           googleSession=True,
                           inBucket=inBucket,
                           loggedUsernameEmail=loggedUsernameEmail)


@app.route('/stats')
def stats():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    loggedUsernameEmail = getLoggedUserDetails()
    users = storage.get_users(onlyReal=False)
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
    evolution = storage.get_points_evolution()
    transferHistory = storage.get_debt_transfer_history()
    productsUse = storage.get_products_summary()
    dependencyWheelData = storage.get_dependecy_data()
    return render_template('stats.html',
                           instance=INSTANCE,
                           users=users,
                           notValidatedUsers=notValidatedUsers,
                           products=products,
                           allBadges=getAllBadges,
                           adminsList=adminsList,
                           googleSession=True,
                           usersStats=getUsersStats,
                           assignedBadges=getAssignedBadges,
                           loggedUserBadges=getLoggedUserBadges,
                           grantedBadges=grantedBadges,
                           loggedUsernameEmail=loggedUsernameEmail,
                           pointsEvolution=evolution,
                           productsUse=productsUse,
                           transferHistory=transferHistory,
                           dependencyWheelData=dependencyWheelData,
                           invalidId=NON_EXISTING_ID,
                           nonSelectedId=NON_SELECTED_VALUE)


@app.route('/showSignUp')
def showSignUp():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    loggedUsernameEmail = getLoggedUserDetails()
    users = storage.get_users(active=1)
    notValidatedUsers = storage.get_users(onlyNotValidated=True)
    getLoggedUserBadges = storage.get_users_badges(userId=loggedUsernameEmail['id'])
    getAllBadges = storage.get_all_badges(badgeUniqe=True)
    adminsList = storage.get_admins()
    adminBadges = False
    if loggedUsernameEmail['email'] in adminsList['admin'].keys():
        adminBadges = True
        getAllBadges = storage.get_all_badges()
    badgesToGrant = storage.get_all_badges(badgeUniqe=True,
                                           adminBadges=adminBadges)
    return render_template('signup.html',
                           instance=INSTANCE,
                           users=users,
                           googleSession=True,
                           notValidatedUsers=notValidatedUsers,
                           loggedUserBadges=getLoggedUserBadges,
                           loggedUsernameEmail=loggedUsernameEmail,
                           adminsList=adminsList,
                           badgesToGrant=badgesToGrant,
                           allBadges=getAllBadges,
                           invalidId=NON_EXISTING_ID,
                           nonSelectedId=NON_SELECTED_VALUE)


@app.route('/user',  methods=['GET'])
def user():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    loggedUsernameEmail = getLoggedUserDetails()

    try:
        userToDisplay = int(request.args.get('user', -1))
    except ValueError:
        return redirect(url_for('main'))

    if not isAnAdmin() and userToDisplay > 0:
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    if userToDisplay < 0:
        userIdToShow = loggedUsernameEmail['id']
        userNameToShow = loggedUsernameEmail['username']
    else:
        userIdToShow = userToDisplay
        userDb = storage.get_username_and_email(id=userToDisplay)
        if userDb.keys():
            userNameToShow = userDb['username']
        else:
            flash('No user with selected ID', 'error')
            return redirect(url_for('main'))

    adminsList = storage.get_admins()
    users = storage.get_users(onlyReal=False)
    getLoggedUserBadges = storage.get_users_badges(userId=userIdToShow)
    allJobs = storage.get_jobs_summary(withUser=userNameToShow)
    badgesTimeline = storage.get_badge_grant_history(withUser=userNameToShow)
    eventsTimeLine = fairtask_utils.combineEvents(allJobs, badgesTimeline)
    evolution = storage.get_points_evolution(specificUser=userIdToShow)
    products = storage.get_products()
    productsUse = storage.get_products_summary(userId=userIdToShow)
    return render_template('user.html',
                           instance=INSTANCE,
                           users = users,
                           userNameToShow=userNameToShow,
                           userIdToShow=userIdToShow,
                           loggedUsernameEmail=loggedUsernameEmail,
                           googleSession=True,
                           adminsList=adminsList,
                           pointsEvolution=evolution,
                           loggedUserBadges=getLoggedUserBadges,
                           products=products,
                           productsUse=productsUse,
                           eventsTimeLine=eventsTimeLine,)


@app.route('/jobedit', methods=['GET'])
def jobedit():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    loggedUsernameEmail = getLoggedUserDetails()
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))

    jobdate = request.args.get('date', -1)
    users = storage.get_users(active=1)
    products = storage.get_products()
    adminsList = storage.get_admins()
    getLoggedUserBadges = storage.get_users_badges(userId=loggedUsernameEmail['id'])
    jobToEdit = storage.get_job_summary(jobdate)
    return render_template('jobedit.html',
                           instance=INSTANCE,
                           loggedUsernameEmail=loggedUsernameEmail,
                           googleSession=True,
                           users=users,
                           products=products,
                           jobToEdit=jobToEdit,
                           adminsList=adminsList,
                           loggedUserBadges=getLoggedUserBadges,)


@app.route('/signUp', methods=['POST'])
def signUp():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    try:
        _assignedNameId = int(request.form['assignedNameId'])
    except KeyError:
        _assignedNameId = NON_SELECTED_VALUE

    validated = 0
    loggedUsernameEmail = getLoggedUserDetails()
    if _email and (_name or _assignedNameId != NON_SELECTED_VALUE):
        if loggedUsernameEmail['id'] == NON_EXISTING_ID:
            validated = 1
        if _assignedNameId == NON_SELECTED_VALUE:
            nameId = storage.add_user(_name, _email,
                                loggedUsernameEmail['id'],
                                validated=validated)

            storage.insert_user_badges(nameId,
                                       badges.BAGDE_ID_FOR_A_NEW_GUY,
                                       None,
                                       badges.SYSTEM_APP_ID,
                                       valid=1)
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
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    loggedUsernameEmail = getLoggedUserDetails()
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
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    loggedUsernameEmail = getLoggedUserDetails()
    if loggedUsernameEmail['id'] == NON_EXISTING_ID:
        return redirect(url_for('showSignUp'))
    storage.clean_bucket()
    flash('Wishlist cleared!')
    return redirect(url_for('addJobs'))


@app.route('/finalizeJob', methods=['POST'])
def finalizeJob():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    loggedUsernameEmail = getLoggedUserDetails()
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
        flash('This will be only saved for the analysis purpose. Scoring will not be countig this mini job.')

    for whomWhat in bucketContent:
        storage.add_transaction(_nameId, whomWhat[0], whomWhat[1],
                                loggedUsernameEmail['id'])
    storage.clean_bucket()

    checkStatusForBadges()
    flash('Order registered!')
    return redirect(url_for('main'))


def checkStatusForBadges():
    dates = storage.get_last_transaction()
    for date in dates:
        actualbadges = badges.get_current_badges(date[0],
                                                 app=app,
                                                 storage=storage)
        for oneBadge in actualbadges:
            storage.insert_user_badges(*oneBadge)
        if len(actualbadges):
            flash('New badges awarded!')
    storage.calculate_actal_scoring(commit=True)
    flash('Badges recalculated!')


@app.route('/grantBadge', methods=['POST'])
def grantBadge():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    try:
        _name = int(request.form['nameIdToGrant'])
        _badge = int(request.form['badgeId'])
    except ValueError:
        return redirect(url_for('showSignUp'))
    loggedUsernameEmail = getLoggedUserDetails()
    if _name > 0 and _badge > 0:
        storage.insert_user_badges(_name, _badge, None, loggedUsernameEmail['id'])
        storage.calculate_actal_scoring(commit=True)
    return redirect(url_for('showSignUp'))


@app.route('/removeBucketItem', methods=['GET'])
def removeBucketItem():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    try:
        what = int(request.args.get('what', -1))
        towhom = int(request.args.get('towhom', -1))
    except ValueError:
        return redirect(url_for('main'))
    if what > 0 and towhom > 0:
        storage.remove_item_in_bucket(towhom, what)
        flash('Removed one entry form the bucket')
    return redirect(url_for('addJobs'))


@app.route('/editUser', methods=['POST'])
def editUser():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    print("=======[DEV]========")
    print("------------------")
    print(request.form)
    print("------------------")
    return redirect(url_for('stats'))

@app.route('/editBadge', methods=['POST'])
def editBadge():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    print("=======[DEV]========")
    print("------------------")
    print(request.form)
    print("------------------")
    return redirect(url_for('stats'))


@app.route('/modifyUser', methods=['GET'])
def modifyUser():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    try:
        userId = int(request.args.get('userId', -1))
        active = int(request.args.get('active', 0))
    except ValueError:
        flash('Error in submited vaules for badge modification!')
        return redirect(url_for('stats'))
    if userId > 0 and (active == 1 or active == 0):
        storage.update_user_active(userId, active)
        flash('Modified user status!')
    else:
        flash('Error in submited vaules for badge modification!')
    return redirect(url_for('stats'))


@app.route('/transferDebt', methods=['GET'])
def transferDebt():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    try:
        fromUserId = int(request.args.get('fromUserId', -1))
        toUserId = int(request.args.get('toUserId', -1))
    except ValueError:
        flash('Error in submited vaules for badge modification!')
        return redirect(url_for('stats'))
    if fromUserId > 0 or fromUserId > 0:
        fromUser = storage.get_username_and_email(id=fromUserId)
        toUser = storage.get_username_and_email(id=toUserId)
        storage.add_debt_transfer(fromUser['scoring'], fromUserId, toUserId)
        addUserBadgesForDebtTransfer(fromUserId, toUserId)
        storage.calculate_actal_scoring(commit=True)
        flash('Transfered %s\'s debt of %d points to %s!' % (fromUser['username'],
                                                             fromUser['scoring'],
                                                             toUser['username']))
    else:
        flash('Error in submited vaules for debt transfer, aborting!!')
    return redirect(url_for('stats'))


@app.route('/modifyBadge', methods=['GET'])
def modifyBadge():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    loggedUsernameEmail = getLoggedUserDetails()
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
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    _name = request.form['productName']
    try:
        _price = float(request.form['productPrice'])
        _size = float(request.form['productSize'])
        _coffeine = float(request.form['productCoffeine'])
    except ValueError:
        flash('Cannot add product! One of the numeric values is not valid!')
        return redirect(url_for('showSignUp'))
    storage.add_product(_name, _price, _size, _coffeine)
    flash('Successfully added %s into product\'s database' % _name)
    return redirect(url_for('stats'))


@app.route('/calculateScoring')
def calculateScoring():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
    flash('Removing all System Awarded Badges!')
    storage.remove_users_bagde_by_system()
    debtTransfers = storage.get_debt_transfer_history().values()
    for oneDebtTransfer in debtTransfers:
        addUserBadgesForDebtTransfer(oneDebtTransfer['fromUserId'],
                                     oneDebtTransfer['toUserId'],
                                     date=oneDebtTransfer['date'])
    if len(debtTransfers):
        flash('Reverted %d debt transfer Badges' % len(debtTransfers))
    checkStatusForBadges()
    storage.calculate_actal_scoring(commit=True)
    flash('Bageds checked & Scoring recalculated!')
    return redirect(url_for('stats'))


@app.route('/applyInflation')
def applyInflation():
    if not isLoginValid():
        return rememberTheInitialRequest(redirect(url_for('login')),
                                         request.endpoint)
    if not isAnAdmin():
        flash('You Need to be AN ADMIN for this action!', 'error')
        return redirect(url_for('main'))
        
    date = storage.get_last_transaction(n=1)[0]
    badgesToAdd = badges.get_inflation_badges(date=date[0], storage=storage)
    for oneBadge in badgesToAdd:
        storage.insert_user_badges(*oneBadge)
    flash('Inflation badges applied!')
    return redirect(url_for('stats'))

def addUserBadgesForDebtTransfer(fromUserId, toUserId, date=None):
    storage.insert_user_badges(toUserId,
                               badges.BAGDE_ID_FOR_ACCEPTING_DEBT,
                               date, badges.SYSTEM_APP_ID, valid=1)
    storage.insert_user_badges(fromUserId,
                               badges.BAGDE_ID_FOR_SELLING_DEBT,
                               date, badges.SYSTEM_APP_ID, valid=1)

if __name__ == "__main__":
    import logging
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    app.run(host=LISTEN_HOST_IP, port=HOST_PORT)
