#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following line in the
entry_points section in setup.cfg:

    console_scripts =
     fibonacci = twote.skeleton:run

Then run `python setup.py install` which will install the command `fibonacci`
inside your current environment.
Besides console scripts, the header (i.e. until logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!

>>> cre_hashtag_at_end.match("There's a hashtag at the end #here. ")
<_sre.SRE_Match at ...>
>>> cre_hashtag_at_end.match("There's a #hashtag at the end #here  --?--  ")
<_sre.SRE_Match at ...>
>>> cre_hashtag_at_end.match("There's a #hashtag at the end #here  -- ? --  ")
<_sre.SRE_Match at ...>
>>> cre_hashtag_at_end.match("There's not a #hashtag at the end in this one  -- ? --  ")
>>> cre_hashtag_at_end.match("There's not a #hashtag at the end or this #1")
>>> cre_hashtag_at_end.match("There's is a smart #hashtag at at the end of tweets about #ai")
<_sre.SRE_Match at ...>
"""
from __future__ import division, print_function, absolute_import
# from builtins import int, round, str
from future import standard_library
standard_library.install_aliases()  # noqa
from builtins import object  # NOQA

import sys
import os
import re
import argparse
import logging

from tqdm import tqdm  # noqa

from pugnlp.regexes import cre_url  # noqa
from .django_queryset_iterator import queryset_iterator


from twote.models import Tweet
try:
    from twote import __version__
except ImportError:
    __version__ = "0.0.0"


if __name__ == "__main__" or not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openchat.settings")
    from django.conf import settings  # noqa


__author__ = "Total Good"
__copyright__ = "Total Good"
__license__ = "mit"

logger = logging.getLogger(__name__)
loggly = logging.getLogger('loggly')

re_hashtag = r'([-\s!?.;]|^)(#[A-Za-z]{2,32})\b'
cre_hashtag = re.compile(re_hashtag)
re_atuser = r'([-\s!?.;]|^)(@[A-Za-z_0-9]{2,32})\b'
cre_atuser = re.compile(re_atuser)
re_hashtag_at_end = r'.*\s([#][A-Za-z]{2,32})\s*[.?!-=\s]{0,8}\s*$'
cre_hashtag_at_end = re.compile(re_hashtag_at_end)


def score_tweets(hashtags, label_hashtag_scores):
    """Score a queryset or iterable of Tweet instances based on their hashtags

    Yields dictionaries of scores according to the dict of dicts in label_hashtag_scores
    """
    for tweet in tweets:
        tweet.
        yield scores

    return is_strict


def label_tweet(tweet):
    # tweet_id = int(tweet_id)
    tweet.is_strict = int(is_strict(tweet.text))
    return tweet


def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="Labels tweets for their 'strictness' (how valuable they are for ML training).")
    parser.add_argument(
        '--version',
        action='version',
        version='twote {ver}'.format(ver=__version__))
    parser.add_argument(
        '-l',
        '--limit',
        dest="limit",
        default=1000,
        help="Limit number of tweets processed.",
        type=int)
    parser.add_argument(
        '-s',
        '--start',
        dest="start",
        default=0,
        help="Which record to start processing on (enables skipping previously processed records).",
        type=int)
    parser.add_argument(
        '-b',
        '--batch',
        dest="batch",
        default=1000,
        help="Number of tweets per batch updated in the database.",
        type=int)
    parser.add_argument(
        '-v',
        '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        default=logging.WARN,
        const=logging.INFO)
    parser.add_argument(
        '-r',
        '--refresh',
        dest="refresh",
        help="Recompute/refresh existing strictness scores. Otherwise only empty (None) records will be processed",
        action='store_true',
        default=False)
    parser.add_argument(
        '-vv',
        '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        default=logging.WARN,
        const=logging.DEBUG)
    return parser.parse_args(args)


def setup_logging(loglevel=logging.WARN):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def no_tqdm(*args, **kwargs):
    return args[0] if len(args) else kwargs['qs']


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    global tqdm
    args = parse_args(args)
    setup_logging(args.loglevel)
    print(args)

    if args.loglevel < logging.WARN:
        pbar = no_tqdm  # noqa
    else:
        pbar = tqdm

    qs = Tweet.objects
    limit = min(args.limit, qs.count() - args.start)

    print("Labeling {} tweets starting at tweet #{}".format(limit))

    for i, tweet in pbar(enumerate(queryset_iterator(qs=qs, batchsize=args.batch)), total=limit):
        if i < args.start or not (args.refresh or tweet.is_strict is None):
            continue
        try:
            tweet.is_strict = is_strict(tweet.text)
        except TypeError:
            tweet.is_strict = None
        tweet.save(update_fields=['is_strict'])
        logger.debug(u"{:6.1f}% {}: {}".format(100. * i / float(limit), tweet.is_strict, tweet.text))
        # batch += [tweet]
        if i >= args.limit:
            break
        if i and not (i % args.batch):
            # Tweet.batch_update(tweet)
            # batch = []
            logger.info(u"{:6.1f}% {}: {}".format(100. * i / limit, tweet.is_strict, tweet.text))

    logger.info(u"Finished labeling {} tweets".format(i))


def run():
    """Entry point for console_scripts"""
    main(sys.argv[1:])


if __name__ == '__main__':
    run()