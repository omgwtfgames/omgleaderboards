import logging
import os
import datetime
import hashlib
import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
import json
from model import *

#jinja_environment = jinja2.Environment(
#    loader=jinja2.FileSystemLoader(os.path.join(
#                                   os.path.dirname(__file__)),
#                                   "templates"))

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

#logging.info('Template path: '+os.path.join(os.path.dirname(__file__), "templates"))

def json_date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

class MainPage(webapp2.RequestHandler):
  def get(self):
    template_values = {}

    q = Score.all()
    q.order("-score")
    scores = q.fetch(100)
    if scores:
      template_values = {'scores': scores}

    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

class AddScore(webapp2.RequestHandler):

  def post(self):
    """
    Creates a new highscore via POST.

    The provided hash must match the hash calculated for
    id,score,nickname and the secrect salt for that game_id.
    """
    game_id = str(self.request.get('id'))
    score = str(self.request.get('score'))
    nickname = str(self.request.get('nickname'))
    platform = str(self.request.get('platform'))
    extra = str(self.request.get('extra'))
    hash_recieved = str(self.request.get('hash'))
    if hash_okay(game_id, [score, nickname, platform, extra], hash_recieved):
      s = Score(game_id = game_id, score = int(score), nickname = nickname)
      s.platform = platform
      s.extra = extra
      s.timeframes = ['today','last7days','last30days']
      s.put()
      # success
      self.response.status = 200
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"result":"success"}')
      return
    else:
      # fail
      self.response.status = 403
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"result":"bad hash"}')
      return

  # we also implement GET although this isn't very RESTful
  # in spirit. This will probably disappear in the future
  def get(self):
    """
    Let's call this deprecated.
    """
    self.post()


class GetScores(webapp2.RequestHandler):
  def get(self, game_id):
    """
    Return scores for a particular game_id as JSON or
    tab-delimited values (TSV).
  
    Query parameters are:
        format -- return format specified as 'tsv' or 'json'
        timeframes -- a space delimited list of timeframe tags like 
                     'today last7days', or 'today+last7days' if 
                     spaces are URL encoded)
        limit -- an interger number of top scores to return.

    Default is to return the top 10 scores as JSON for all timeframes.
    """
    outformat = str(self.request.get('format'))

    # today, last7days, last30days, alltime (default)
    timeframes_req = str(self.request.get('timeframes'))
    if not timeframes_req:
      # by default we return every timeframe if none is specified
      timeframes_req = "alltime today last7days last30days"
    try:
      timeframes = timeframes_req.split(' ')
    except:
      # if we can't split, assume only one timeframe tag is specified
      timeframes = [timeframes_req]
    if self.request.get('limit'):
      limit = int(self.request.get('limit'))
    else:
       limit = 10

    tsvout = ""
    jdict = {'scores':{}}
    jdict['game_id'] = game_id
    for tf in timeframes:
      jdict['scores'][tf] = []
      q = Score.all()
      q.filter("game_id = ", game_id)
      q.order("-score")
      if tf == "" or tf == "alltime":
        pass
      else:
        q.filter("timeframes = ", tf)

      # NOTE: can't sort on score AND apply date inequality
      #       so while the filter below seems like a nice idea,
      #       we MUST use timeframe tags here instead
      #if timeframe == "today":
      # q.filter("date < ", hours_ago(24))

      # TODO: do some memcaching in here so we don't need to pull down
      #       every score every time (the top ones probably won't 
      #       change often.
      # TODO: make this async
      scores = q.fetch(limit)

      # create a list of dicts for each scoreboard (by timeframe)
      for s in scores:
        sdict = db.to_dict(s)
        if 'timeframes' in sdict:
          del sdict['timeframes'] # this is redundant now
        del sdict['game_id'] # this is included just once in the level above
        jdict['scores'][tf].append(sdict)

        tsvout += "%s\t%s\t%i\n" % (tf, s.nickname, s.score)
      
    #scores.sort(key=lambda i: i.score, reverse=True)

    #jdict = {'scores':[]}
    #for s in scores:
    #  jdict['scores'].append(db.to_dict(s))

    if outformat == "" or outformat == "json":
      logging.info(jdict)
      # JSON encode and send scores
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(json.dumps(jdict, default=json_date_handler))
    elif outformat == "tsv":
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(tsvout)

def hours_ago(hrs):
  return datetime.datetime.now() - datetime.timedelta(hours=hrs)

def mins_ago(mins):
  return datetime.datetime.now() - datetime.timedelta(minutes=mins)

def hash_okay(game_id, strings, hash_recieved):
  # pull the secret_salt from
  # the datastore (memcached)
  try:
    secret_salt = SecretSalt.all().filter("game_id = ", game_id).get().salt
  except AttributeError:
    logging.info("No salt found for: " + game_id)
    return False

  secret_salt = memcache.get("salt:"+game_id)
  if not secret_salt:
    secret_salt = SecretSalt.all().filter("game_id = ", game_id).get().salt
    memcache.add("salt:"+game_id, secret_salt)

  #secret_salt = "no_ch3ating_a$$wipe"
  str_to_hash = game_id+"".join(strings)+secret_salt
  expected = hashlib.md5(str_to_hash).hexdigest()
  logging.info("Expected hash: " + expected)

  #expected = base64.b64encode(sha.new(game_id+str(score)).digest()).strip("=")
  # this md5 should be compatible with the hexdigest generated by
  # http://wiki.unity3d.com/index.php?title=MD5
  
  if (hash_recieved == expected):
    return True;
  else:
    return False;

class AddSalt(webapp2.RequestHandler):
  def post(self):
    """
    Add secret salt for a particular game_id to the datastore.
    Query parameters are 'id' (the game_id) and 'salt' (the secret string).
    """
    game_id = str(self.request.get('id'))
    salt = str(self.request.get('salt'))
    if game_id and salt:
      # fail if we would overwrite an existing game_id
      if SecretSalt.get_by_key_name("salt:"+game_id):
        # on failure
        self.response.status = 409
        self.response.out.write('{"result":"fail"}')
        return

      ss = SecretSalt(game_id=game_id, salt=salt, key_name="salt:"+game_id)
      ss.put()
      self.response.status = 200
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"result":"success"}')
      return
    
    # on failure
    self.response.status = 400
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write('{"result":"fail"}')
    return

  def get(self):
    self.response.out.write("""
          <html>
            <body>
              <form action="/addsalt" method="post">
                <div>game_id <br/> <input type="text" name="id"></input></br><br/>
                     Secret salt <br/> <input type="text" name="salt"></input></br>
                </div>
                <div><input type="submit" value="Add salt"></div>
              </form>
            </body>
          </html>""")

class TaskUpdateTimeframeTags(webapp2.RequestHandler):
  """
  Checks the age of every highscore and updates the 'timeframes'
  property accordingly (eg adds last7days, last30days tags).

  Since every score begins with all timeframe tags added,
  we actually are typically removing stale tags here rather 
  than adding them.
  """
  def get(self):
    timeframes = {'today': hours_ago(24), 
                  'last7days': hours_ago(24*7),
                  'last30days': hours_ago(24*30)}
    puts = []
    outdict = {}
    # loop over today, last7days, last30days
    for ttag in timeframes:
      # remove stale tags
      q = Score.all()
      # is score older than timeframe ?
      q.filter("date < ", timeframes[ttag])
      q.filter("timeframes = ", ttag)
      # TODO: use cursors etc here
      #       fetch(1000) will currently cause the leaderboard to
      #       not properly update if the app recieves more than 
      #       1000 highscores in an hour
      #       however it should catch up in subsequent hours
      #       so it's not really a showstopper
      scores = q.fetch(1000)
      for s in scores:
        s.timeframes.remove(ttag)
        puts.append(db.put_async(s))
        outdict[str(s.key())+"_"+ttag] = "removed"

    # check that puts succeeded
    # if a put failed an exception will be thrown
    for p in puts:
      p.get_result()

    # on success
    outdict["result"] = "success"

    # just for testing ...
    #logging.debug(outdict)
    #self.response.status = 200
    #self.response.headers['Content-Type'] = 'application/json'
    #self.response.out.write(json.dumps(outdict, default=json_date_handler))
    
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/add', AddScore),
                               ('/get/(.*)', GetScores),
                               ('/addsalt', AddSalt),
                               ('/tasks/update_timeframe_tags', 
                                 TaskUpdateTimeframeTags),],
                              debug=True)
