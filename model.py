from google.appengine.ext import db

class Score(db.Model):
  """A single score.
  """
  
  game_id = db.StringProperty() # the unique game+difficulty key
  date = db.DateTimeProperty(auto_now_add=True)
  # today, last7days, last30days
  timeframes = db.StringListProperty()
  score = db.IntegerProperty()
  nickname = db.StringProperty() # TODO: validator to limit length

  # 'extra' could be used to store a short JSON string with
  # info like the level the player got up to
  # however this won't be be indexed
  # extra = db.TextProperty()

  #def to_dict(self):
  #  return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

class SecretSalt(db.Model):
  """The salt for a particular game_id.
  """
  game_id = db.StringProperty()
  salt = db.StringProperty()
  

