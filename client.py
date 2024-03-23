#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-23 16:17:25 krylon>
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

import calendar
import logging
import os
import time
from datetime import datetime, timedelta
from mimetypes import guess_extension
from queue import Empty, SimpleQueue
from threading import Lock, Thread, local
from typing import Final

import feedparser

from cephalopod import common
from cephalopod.cast import Episode, Feed
from cephalopod.database import Database

refresh_interval: Final[timedelta] = timedelta(minutes=60)


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
    fetch_queue: SimpleQueue[Feed]

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
                autorefresh=True,
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

    def refresh(self) -> None:
        """Refresh all the podcast feeds that need a refresh."""
        with self.lock:
            if self.active:
                self.log.error("Refresh is currently active.")
                return
            self.active = True

        self.log.info("Refreshing podcast feeds")

        self.log.debug("Starting worker threads.")
        for _i in range(self.worker_cnt):
            t = Thread(target=self._fetch_worker, daemon=True)
            t.start()
            self.workers.append(t)

        db = self.get_database()
        feeds = db.feed_get_autorefresh()
        self.log.debug("Ready to fetch %d feeds", len(feeds))
        for f in feeds:
            self.fetch_queue.put(f)

        while not self.fetch_queue.empty():
            time.sleep(1)

        self.log.debug("Shutting down worker threads")
        self.stop()
        for w in self.workers:
            w.join()
        self.workers.clear()
        self.log.debug("Refresh is done.")

    def _fetch_worker(self) -> None:
        while self.is_active():
            try:
                feed: Feed = self.fetch_queue.get(True, 2)
                d = feedparser.parse(feed.feed_url)
                self.process_feed(feed, d)
            except Empty:
                continue

    def process_feed(self, feed: Feed, d) -> list[Episode]:
        """Process the Feed data once it is fetched and parsed."""
        now = datetime.now()
        db = self.get_database()
        episodes_old: list[Episode] = db.episode_get_by_feed(feed)
        urls: set[str] = {x.url for x in episodes_old}
        episodes_new: list[Episode] = []

        for entry in d['entries']:
            for lnk in entry['links']:
                if lnk['rel'] == 'enclosure':
                    if not lnk['href'] in urls:
                        filename = entry['title'] + guess_extension(lnk['type'])
                        path = os.path.join(feed.folder, filename)
                        epoch = calendar.timegm(entry['published_parsed'])
                        stamp = datetime.fromtimestamp(epoch)
                        ep = Episode(
                            epid=0,
                            feed_id=feed.fid,
                            title=entry['title'],
                            url=lnk['href'],
                            published=stamp,
                            link='',
                            mime_type=lnk['type'],
                            cur_pos=0,
                            finished=False,
                            path=path,
                            keep=False,
                            description=entry['summary'],
                        )
                        with db:
                            if db.episode_add(ep):
                                episodes_new.append(ep)
                            else:
                                self.log.error("Failed to add episode %s", ep.title)
                    break

        with db:
            db.feed_set_timestamp(feed, now)
        return episodes_new


# Local Variables: #
# python-indent: 4 #
# End: #
