#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-20 22:35:20 krylon>
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
from queue import Empty, SimpleQueue
from threading import Lock, Thread, local

import feedparser

from cephalopod import common
from cephalopod.cast import Feed
from cephalopod.database import Database


class Client:  # pylint: disable-msg=R0903
    """Client handles the fetching and parsing of RSS feeds."""

    __slots__ = [
        "worker_cnt",
        "workers",
        "lock",
        "active",
        "log",
        "pool",
        "fetch_queue",
    ]

    worker_cnt: int
    workers: list[Thread]
    lock: Lock
    active: bool
    log: logging.Logger
    pool: local
    fetch_queue: SimpleQueue

    def __init__(self, worker_cnt: int = 0):
        if worker_cnt == 0:
            worker_cnt = os.cpu_count() or 1

        self.worker_cnt = worker_cnt
        self.workers = []
        self.lock = Lock()
        self.active = False
        self.log = common.get_logger("Client")
        self.pool = local()
        self.fetch_queue = SimpleQueue()

    def get_database(self) -> Database:
        """Get the Database instance for the calling thread."""
        try:
            return self.pool.db
        except AttributeError:
            db = Database()  # pylint: disable-msg=C0103
            self.pool.db = db
            return db

    def is_active(self) -> bool:
        """Return the Client's Active flag"""
        with self.lock:
            return self.active

    def stop(self) -> None:
        """Clear the Client's active flag"""
        with self.lock:
            self.active = False

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

            db = self.get_database()

            with db:
                db.feed_add(feed)
                assert feed.fid != 0

            return feed
        except Exception as e:
            self.log.error("Error trying to load podcast from URL %s: %s",
                           url,
                           e)
            raise

    def _fetch_worker(self) -> None:
        # db = self.get_database()
        while self.is_active():
            try:
                # feed: Feed = self.fetch_queue.get(True, 2)
                # d = feedparser.parse(feed.feed_url)
                pass
            except Empty:
                continue

# Local Variables: #
# python-indent: 4 #
# End: #
