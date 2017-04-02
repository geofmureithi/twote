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
standard_library.install_aliases()
from builtins import object  # NOQA

import sys  # noqa
import gc  # noqa
import os  # noqa
import re  # noqa
import argparse  # noqa
import logging  # noqa

from tqdm import tqdm  # noqa

from pugnlp.regexes import cre_url  # noqa

# from twote import __version__  # noqa
from twote.models import Tweet  # noqa


if __name__ == "__main__" or not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openchat.settings")
    from django.conf import settings  # noqa

try:
    from twote import __version__
except:
    __version__ = "0.0.0"

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


def is_strict(text):
    """Fibonacci example function

    Args:
      text (str): Tweet text

    Returns:
      int: a class of strictness, 0 meaning contains a URL or more than 1 hashtag, or hashtag isn't at end

    >>> is_strict(u"This has a url.example.com so it's not fully #strict")
    3
    >>> is_strict(u"This has a #hasher in middle but no url and has hash at #end.")
    4
    >>> is_strict(u"This has an ending #hasher.")
    7
    >>> is_strict(u"This has two ending #hasher #hashers.")
    4
    >>> is_strict(u"I still don't understand why people don't f'n follow back. I promise you won't lose your ego! #sarcasm")
    7

    """
    if not isinstance(text, (str, basestring, unicode)) or not len(text) > 2:
        return 0
    is_strict = 0

    num_hashtags = len(cre_hashtag.findall(text))
    num_atmentions = len(cre_atuser.findall(text))

    is_strict += 8 * int(len(cre_url.findall(text)) == 0)
    is_strict += 4 * int(num_hashtags in (0, 1))
    is_strict += 2 * int(((num_hashtags == 1 and bool(cre_hashtag_at_end.match(text))) or (num_hashtags == 0)) and
                     num_hashtags in (0, 1))
    is_strict += int(num_atmentions in (0, 1))

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


def queryset_iterator(qs, batchsize=500, gc_collect=True):
    iterator = qs.values_list('pk', flat=True).order_by('pk').distinct().iterator()
    eof = False
    while not eof:
        primary_key_buffer = []
        try:
            while len(primary_key_buffer) < batchsize:
                primary_key_buffer.append(iterator.next())
        except StopIteration:
            eof = True
        for obj in qs.filter(pk__in=primary_key_buffer).order_by('pk').iterator():
            yield obj
        if gc_collect:
            gc.collect()


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
    limit = min(args.limit, qs.count())

    print("Labeling {} tweets".format(limit))

    for i, tweet in pbar(enumerate(queryset_iterator(qs=qs, batchsize=args.batch)), total=limit):
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