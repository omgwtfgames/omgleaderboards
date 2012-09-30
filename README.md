# OMG Leaderboards !1!!

*OMG Leaderboards* is a simple backend for storing highscores for games and
serving up leaderboards for specified timeframes (today, last 7 days, etc).

It was built with Unity3d games in mind, but is generic enough to work with
any game capable of making an HTTP connection.

Cheaters are prevented from posting fake scores by a use of a shared secret 
(the salt) which is used to hash the game_id, score and player nickname 
sent to the server.
Since this 'salt' is stored on the client side, you should obfusicate your
game code somehow to try and prevent it's disclosure.

## Add secret salt for a particular game_id via POST like:

In a web browser, go to http://omgleaderboards.appspot.com/addsalt and enter a game_id and secret salt value.

Or, on the commandline use curl like:

    curl --data "id=somegame&salt=mySecretKey" https://omgleaderboards.appspot.com/addsalt

## Add a score for a particular game_id via POST, using the hash for verification:

    curl --data "id=somegame&nickname=AwesomePlayer&score=1110&hash=6b959d6bf1f873a1c3c3f63f2d8a00ca" https://omgleaderboards.appspot.com/add

Obviously in your game you would make this POST request programatically however you want.

### The hash is generated from the game_id, score, nickname and the salt, like:

```python
import hashlib
str_to_hash = game_id + str(score) + nickname + secret_salt
hash = hashlib.md5(str_to_hash).hexdigest()
```

(to do this in Unity, see http://wiki.unity3d.com/index.php?title=MD5 )

## Get scores for a particular game_id:

''(specifying some timeframes and to return the top ten scores)''

    http://omgleaderboards.appspot.com/get/somegame?timeframes=today+last7days&limit=10

## Internal: cron job to update timeframe tags each hour (admin & cron only)

    http://omgleaderboards.appspot.com/tasks/update_timeframe_tags

You will probably never need to use this, but it's useful to know that
it will run in the background each hour.
