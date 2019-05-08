# FairTaskAssigner

IT is a simple web server application that allows to track the activities (e.g. coffee servings) within the group of friends.

It works based on google authentication token (uses only login and identity picture!).

*v0.1*
- not logged user can see actual servings, top three candidates and top three servants
- logged user can add new users
- logged user can add serving (as him)

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

## TO DO
- New user can add himself
- Add different scoring methods
- Add proposal based on preselected users
