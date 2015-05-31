# -*- coding: utf-8 -*-
# This tool exports the contents of the omgleaderboards datastore as JSON Lines
# (one JSON object per line).
#
# You may want to use this to analyse scores offline (eg in R), or if you
# decide to migrate to different leaderboard solution and wish to transfer the
# existing scores over.
#
# Note that the free quotas Google App Engine for datastore reads are
# quite limited and the charges beyond the free quota are quite high.
# It may end up costing you a few dollars to export more than ~20,000
# scores in a day.

import getpass
import sys
import os
from os.path import expanduser

APP_DOMAIN = 'omgleaderboards.appspot.com'
REMOTE_API_PATH = '/remoteapi'
APPENGINE_SDK_PATH = expanduser('~/python_devel/appengine/google_appengine/')

# we need to do this to discover the appengine modules which
# don't exist in the regular python path
sys.path.insert(0, APPENGINE_SDK_PATH)
import dev_appserver
dev_appserver.fix_sys_path()
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db

sys.path.append("..")
from model import Score, SecretSalt

def auth_func():
    username = os.environ.get('APPENGINE_USERNAME')
    pw = os.environ.get('APPENGINE_PASSWORD_IN_ENV_IS_BAD_IDEA_BUT_CONVENIENT')
    if username and pw:
        return (username, pw)
    else:
        return (raw_input('Username:'), getpass.getpass('Password:'))

from time import sleep
from datetime import datetime, date, time
import json

# https://stackoverflow.com/questions/13311363/appengine-making-ndb-models-json-serializable
class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        # If this is a key, you might want to grab the actual model.
        if isinstance(o, db.Key):
            o = db.get(o)

        if isinstance(o, Score):
            d = db.to_dict(o)
            # some json strings in the 'extra' field use the wrong
            # quote type (a bug on the client side). we fix that.
            d["extra"] = d['extra'].replace("'", '"')
            # then convert json encoded string field into a dict, if possible
            if d["extra"]:
                try:
                    d["extra"] = json.loads(d["extra"])
                except ValueError, e:
                    pass
            k = o.key()
            d["__key__"] = str(k)
            d["__id__"] = k.id()
            d["__name__"] = k.name()
            return d
        elif isinstance(o, db.Model):
            d = db.to_dict(o)
            k = o.key()
            d["__key__"] = str(k)
            d["__id__"] = k.id()
            d["__name__"] = k.name()
            return d
        elif isinstance(o, (datetime, date, time)):
            # ISO 8601 time, UTC timezone
            return (o).isoformat('T')+'Z'

remote_api_stub.ConfigureRemoteApi(None, REMOTE_API_PATH, auth_func, APP_DOMAIN)

scores_query = Score.all().order("-date")
#scores_query = SecretSalt.all()

cursor = None
batch_has_result = True

# TODO: This isn't terminating when finished
while batch_has_result:
    if cursor:
        scores_query = Score.all().order("-date").with_cursor(cursor)
        #scores_query = SecretSalt.all().with_cursor(cursor)

    batch_has_result = False
    for score in scores_query.run(limit=1000, batch_size=1000):
        batch_has_result = True
        # print db.to_dict(score)
        try:
            jstr = JSONEncoder().encode(score)
        except ValueError, e:
            sys.stderr.write("%s : %s\n" % (e, db.to_dict(score)))
            sys.exit()
        print jstr

    # we track the cursor - if it's the same as last loop, we've retrieved all
    # entities and finish up
    prev_cursor = cursor
    cursor = scores_query.cursor()
    if cursor == prev_cursor:
        break

    sys.stderr.write("Cursor: %s\n" % cursor)
    sleep(3)



