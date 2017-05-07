from __future__ import print_function, unicode_literals, division, absolute_import
from future import standard_library
standard_library.install_aliases()  # noqa
from builtins import *  # noqa

from datetime import timedelta
# import nltk
# from nltk import word_tokenize
# from nltk.corpus import stopwords

from . import db_utils

from twote.regexes import cre_room


def get_time_and_room(tweet, extracted_time):
    """Get room number from a tweet while ignoring the time that was extracted
    using SUTime. extracted_time should be equal to the object SUTime parsed
    """
    result = {}
    result["date"] = []
    result["room"] = []

    tweet_without_time = tweet

    for time_slot in extracted_time:
        tweet_without_time = tweet_without_time.replace(time_slot["text"], "")
        result["date"].append(time_slot.get("value"))

    # Orignal statement that was trimmed to only use word tokenize below
    #filter_known_words = [word.lower() for word in word_tokenize(tweet_without_time) if word.lower() not in (stopwords.words('english') + nltk.corpus.words.words())]

    # ****** this is the part that can't access word_tokenize when run with supervisor ******
    #filter_known_words = [word.lower() for word in word_tokenize(tweet_without_time)]

    filter_known_words = [word.lower() for word in tweet_without_time.split()]


    for word in filter_known_words:
        if cre_room.match(word):
            result["room"].append(cre_room.match(word).group())

    return result

def schedule_tweets(u_name, tweet, t_id, talk_time, num_tweets=2, interval=1):
    """Schedule reminder tweets at set intervals. num_tweets controls
    the number of remindertweets sent and interval controls the minutes
    before the event the tweets are sent. 

    Ex. 
    num_tweets = 2 & interval = 15 
    will send 2 tweets 30 & 15 mins before event
    """
    # check config table to see if autosend on
    approved = db_utils.check_for_auto_send()

    tweet_url = "https://twitter.com/{name}/status/{tweet_id}"
    embeded_tweet = tweet_url.format(name=u_name, tweet_id=t_id)

    for mins in range(interval,(num_tweets*interval+1), interval):
        remind_time = talk_time - timedelta(minutes=mins)
        message = "Coming up in {} minutes! {}".format(mins, embeded_tweet)

        tweet_obj = {
            "message": message,
            "approved": approved,
            "remind_time": remind_time
        }

        db_utils.save_outgoing_tweet(tweet_obj)
