# FairTaskAssigner

IT is a simple web server application that allows to track the activities (e.g. coffee servings) within the group of friends.

It works based on google authentication token (uses only login and identity picture!).

*0.3*
- The temporary rating is calculated within the preselected bucket only among the current waiting list users.
- For a logged user a predefined order button (adding to the current wish list) is available for the most often ordered product. No button is visible when never made an order.
- Moved the order history to the 'AddTask' tab accessible only for the logged users
- Disabled 'Register Job' and 'who is buying' for an empty Wish list.

*0.2*
- Preselected bucket is validated at later step

*v0.1*
- Not logged user can see actual servings, top three candidates and top three servants
- Logged user can add new users
- Logged user can add serving (as him)
- New user can login and add himself to the system

## Installation
Install all modules:
```bash
pip install -r requirements.txt
```

Use `db/db_scheme.sql` to create [SQLite]() DB.

Finally, create `run.sh` with the credentials created using [Google API Console](https://console.cloud.google.com/apis/credentials):
```bash
export FN_GOOGLE_CLIENT_ID='YOUR_CLIENT_ID'
export FN_GOOGLE_CLIENT_SECRET='YOUR_CLIENT_SECRET'
export FN_FLASK_SECRET_KEY='whatever_key'
export FN_REDIRECT_URI='REDIRECT_URL_YOU_SPECIFY_IN_GOOGLE'
export FN_DB_TO_USE='db/YOUR_SQLite_PATH'

export FN_DEBUG=True              # if not set default False
export FN_LISTEN_HOST_IP='any ip' # if not set default 127.0.0.1

python app.py
```
To start server `sh run.sh`, it will start server listening at `FN_LISTEN_HOST_IP:8040`.
