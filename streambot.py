import tweepy
from tweepy.api import API 
import re
import os
import datetime
import django

# need to point Django at the right settings to access pieces of app
os.environ["DJANGO_SETTINGS_MODULE"] = "hackor.settings"
django.setup()

import twote.secrets as s
from twote import models
from hackor.settings import BASE_DIR
from twote.tweepy_connect import tweepy_send_tweet
from retweetbot import RetweetBot


class StreamListener(tweepy.StreamListener):
    """
    Object that defines the callback actions passed to tweepy.Stream 
    """
    def __init__(self, streambot, api=None):
        self.api = api or API()
        # needed ref to streambot so method can be called there
        self.streambot = streambot
        self.tw_bot_id = 841013993602863104
        self.ignored_users = [self.tw_bot_id, ]
        
    def update_ignore_users(self):
        """
        Check app config table to get list of ignored twitter ids, ignore bot
        """
        config_obj = models.OutgoingConfig.objects.latest("id")
        ignore_list = [tw_id for tw_id in config_obj.ignore_users]
        ignore_list.append(self.tw_bot_id)
        self.ignored_users = ignore_list

    def on_status(self, status):
        # call to check for ignored users from OutgoingConfig
        self.update_ignore_users()

        if status.user.id in self.ignored_users:
            print("tweet from account on ignore list")
            return

        # save user record to User model
        user, created = models.User.objects.get_or_create(id_str=str(status.user.id))
        user.verified = status.user.verified  # v4
        user.time_zone = status.user.time_zone  # v4
        user.utc_offset = status.user.utc_offset  # -28800 (v4)
        user.protected = status.user.protected  # v4
        user.location = status.user.location  # Houston, TX  (v4)
        user.lang = status.user.lang  # en  (v4)
        user.screen_name = status.user.screen_name
        user.followers_count = status.user.followers_count
        user.statuses_count = status.user.statuses_count
        user.friends_count = status.user.friends_count
        user.favourites_count = status.user.favourites_count
        user.save()

        # save tweet record to StreamedTweet model
        tweet_record, created = models.StreamedTweet.objects.get_or_create(id_str=status.id_str)
        tweet_record.id_str = status.id_str
        tweet_record.user = user
        tweet_record.favorite_count = status.favorite_count
        tweet_record.text = status.text
        tweet_record.source = status.source
        tweet_record.save()    

        # trigger time parsing with SUTime inside streambot
        self.streambot.retweet_logic(status.text, status.id_str, user.screen_name)  
        
    def on_error(self, status_code):
        if status_code == 420:
            return False


class Streambot:
    """
    Stream Twitter and look for tweets that contain targeted words, 
    when tweets found look for datetime and room, if present save tweet to
    OutgoingTweet model.  

    Ex.
    bot = Streambot()
    # to run a stream looking for tweets about PyCon
    bot.run_stream(["PyCon"]) 
    """
    def __init__(self):
        self.api = self.setup_auth()
        self.stream_listener = StreamListener(self)
        self.retweet_bot = RetweetBot()

    def setup_auth(self):
        """
        Set up auth stuff for api and return tweepy api object
        """
        auth = tweepy.OAuthHandler(s.listener["CONSUMER_KEY"], s.listener["CONSUMER_SECRET"])
        auth.set_access_token(s.listener["ACCESS_TOKEN"], s.listener["ACCESS_TOKEN_SECRET"])
        api = tweepy.API(auth)

        return api

    def run_stream(self, search_list=[]):
        """
        Start stream, when matching tweet found on_status in StreamListener called. 
        search_list arg is a list of terms that will be looked for in tweets
        """
        if search_list == []:
            raise ValueError("Need a list of search terms as arg to run_stream")

        stream = tweepy.Stream(auth=self.api.auth, listener=self.stream_listener)
        stream.filter(track=search_list)

    def retweet_logic(self, tweet, tweet_id, screen_name):
        """
        Use SUTime to try to parse a datetime out of a tweet, if successful
        save tweet to OutgoingTweet to be retweeted
        """
        print(tweet, tweet_id)
        time_room = self.retweet_bot.get_time_and_room(tweet)

        # check to make sure both time and room extracted and only one val for each
        val_check = [val for val in time_room.values() if val != [] and len(val) == 1]

        if len(val_check) == 2:
            # way to mention a user after a tweet is recieved
            tweepy_send_tweet(
                "@{} We saw your openspaces tweet!".format(screen_name)
                )

            #check config table to see if autosend on
            config_obj = models.AppConfig.objects.latest("id")
            approved = 1 if config_obj.auto_send else 0

            # saving the tweet to the OutgoingTweet table triggers celery stuff
            tweet_obj = models.Tweets(tweet=tweet, approved=approved)
            tweet_obj.save()


if __name__ == '__main__':
    bot = Streambot()
    keyword = "adlsjlflkjdhsfla"
    print(keyword)
    bot.run_stream([keyword])