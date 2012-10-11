from google.appengine.ext import db

class Score(db.Model):
  """A single score.
  """
  
  game_id = db.StringProperty() # the unique game+difficulty key
  date = db.DateTimeProperty(auto_now_add=True)
  # NOTE: should different platforms just be a different game_id ?
  platform = db.StringProperty() # eg, android,windows,osx,nacl
  # today, last7days, last30days
  timeframes = db.StringListProperty()
  score = db.IntegerProperty()
  nickname = db.StringProperty() # TODO: validator to limit length


  # 'extra' can be used to store a arbitrary text data, eg
  # a short JSON string with info like the level the player 
  # got up to. Note that this won't be be indexed so you can't
  # query on info in extra
  extra = db.TextProperty()

  #def to_dict(self):
  #  return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

class SecretSalt(db.Model):
  """The salt for a particular game_id.
  """
  game_id = db.StringProperty()
  salt = db.StringProperty()
  

