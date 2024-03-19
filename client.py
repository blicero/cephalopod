#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-18 14:48:38 krylon>
#
# /data/code/python/cephalopod/client.py
# created on 16. 03. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
cephalopod.client

(c) 2024 Benjamin Walkenhorst
"""

import logging
import os
from datetime import datetime

import feedparser

from cephalopod import common
from cephalopod.cast import Feed
from cephalopod.database import Database


class Client:  # pylint: disable-msg=R0903
    """Client handles the fetching and parsing of RSS feeds."""

    log: logging.Logger
    db: Database

    def __init__(self):
        self.log = common.get_logger("Client")
        self.db = Database()

    def feed_add(self, url: str) -> Feed:
        """Add a new feed."""
        try:
            self.log.info("Add feed %s", url)
            d = feedparser.parse(url)
            f = d['feed']
            folder = os.path.join(
                common.path.download(),
                f['title']
            )

            self.log.debug("Episodes for %s will be saved in %s",
                           f['title'],
                           folder)

            feed = Feed(
                fid=0,
                feed_url=url,
                homepage=f['link'],
                title=f['title'],
                description=f['description'],
                cover_url=f['image']['href'],
                last_refresh=datetime.fromtimestamp(0),
                autorefresh=False,
                folder=folder,
            )

            with self.db:
                self.db.feed_add(feed)
                assert feed.fid != 0

            return feed
        except Exception as e:
            self.log.error("Error trying to load podcast from URL %s: %s",
                           url,
                           e)
            raise

# Local Variables: #
# python-indent: 4 #
# End: #
