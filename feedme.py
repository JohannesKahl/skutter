#!/usr/bin/env python3

import feedparser
import logging
import sys
import os
import textwrap
import re

FEED_ONE = 'http://www.abc.net.au/news/feed/51120/rss.xml'
FEED_TWO = 'http://www.phoronix.com/rss.php'
FEED_THREE = 'https://planetkde.org/rss20.xml'
FEED_THREE = 'http://www.linux.com/feeds/all-content'
FEED_ONE_LINES = 4
FEED_TWO_LINES = 4
FEED_THREE_LINES = 4
rss_one_feed_length = 0
rss_two_feed_length = 0
rss_three_feed_length = 0
line_width = 50

outstring='<table align="left" cellspacing="0" cellpadding="0">'

logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt="%H:%M:%S")


print("Feed One Connecting...")
rss_one = feedparser.parse(FEED_ONE)

if not 'title' in rss_one.feed:
    logging.debug("Feed One didn't load. Check URL.")
    rss_one_feed_length = -1

print("Feed Two Connecting...")
rss_two = feedparser.parse(FEED_TWO)

if not 'title' in rss_two.feed:
    logging.debug("Feed Two didn't load. Check URL.")
    rss_two_feed_length = -1

print("Feed Three Connecting...")
rss_three = feedparser.parse(FEED_THREE)

if not 'title' in rss_three.feed:
    logging.debug("Feed Three didn't load. Check URL.")
    rss_three_feed_length = -1

if not rss_one_feed_length == -1:
    rss_one_feed_length = min(FEED_ONE_LINES, len(rss_one['entries']))
    logging.debug(rss_one_feed_length)
    outstring += '<tr><td><span style="color:red;font-size:16pt;text-decoration:none;">' + rss_one.feed['title'] + '</span></td></tr>'
    for i in range(rss_one_feed_length):
        logging.debug(rss_one.entries[i].link)
        tmp_title = textwrap.wrap(rss_one.entries[i].title, line_width)
        tmp = re.sub('<[^<]+?>', '', rss_one.entries[i].summary)
        tmp_summary = textwrap.wrap(tmp, line_width)
        outstring += '<tr><td><a href="' + rss_one.entries[i].link + '"><span style="color:red;">'
        for i in tmp_title:
            outstring += i + '<br>'
        outstring = outstring[:-4] + '</a></span><br>'
        for i in tmp_summary:
            outstring += i + '<br>'
        outstring = outstring[:-4] + '</td></tr>'
    

if not rss_two_feed_length == -1:
    rss_two_feed_length = min(FEED_ONE_LINES, len(rss_two['entries']))
    logging.debug(rss_two_feed_length)
    outstring += '<tr><td><span style="color:red;font-size:16pt;text-decoration:none;">' + rss_two.feed['title'] + '</span></td></tr>'
    for i in range(rss_two_feed_length):
        logging.debug(rss_two.entries[i].link)
        tmp_title = textwrap.wrap(rss_two.entries[i].title, line_width)
        tmp = re.sub('<[^<]+?>', '', rss_two.entries[i].summary)
        tmp_summary = textwrap.wrap(tmp, line_width)
        outstring += '<tr><td><a href="' + rss_two.entries[i].link + '"><span style="color:red;">'
        for i in tmp_title:
            outstring += i + '<br>'
        outstring = outstring[:-4] + '</a></span><br>'
        for i in tmp_summary:
            outstring += i + '<br>'
        outstring = outstring[:-4] + '</td></tr>'

if not rss_three_feed_length == -1:
    rss_three_feed_length = min(FEED_ONE_LINES, len(rss_three['entries']))
    logging.debug(rss_three_feed_length)
    outstring += '<tr><td><span style="color:red;font-size:16pt;text-decoration:none;">' + rss_three.feed['title'] + '</span></td></tr>'
    for i in range(rss_three_feed_length):
        logging.debug(rss_three.entries[i].link)
        tmp_title = textwrap.wrap(rss_three.entries[i].title, line_width)
        tmp = re.sub('<[^<]+?>', '', rss_three.entries[i].summary)
        tmp_summary = textwrap.wrap(tmp, line_width)
        outstring += '<tr><td><a href="' + rss_three.entries[i].link + '"><span style="color:red;">'
        for i in tmp_title:
            outstring += i + '<br>'
        outstring = outstring[:-4] + '</a></span><br>'
        for i in tmp_summary:
            outstring += i + '<br>'
        outstring = outstring[:-4] + '</td></tr>'



outstring += '</table>'
logging.info(outstring)
with open(os.path.expanduser('~/.local/share/skutter/rss'), 'w') as g:
        g.write(outstring)
sys.exit(0)
