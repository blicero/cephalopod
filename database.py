#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-20 22:34:23 krylon>
#
# /data/code/python/cephalopod/database.py
# created on 15. 03. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
cephalopod.database

(c) 2024 Benjamin Walkenhorst
"""

import logging
import sqlite3
import threading
from datetime import datetime
from enum import Enum, auto
from typing import Final, Union

import krylib

from cephalopod import common
from cephalopod.cast import Episode, Feed

OPEN_LOCK: Final[threading.Lock] = threading.Lock()

INIT_QUERIES: Final[list[str]] = [
    """
CREATE TABLE feed (
    id INTEGER PRIMARY KEY,
    feed_url TEXT UNIQUE NOT NULL,
    homepage TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    cover_url TEXT NOT NULL DEFAULT '',
    last_refresh INTEGER NOT NULL DEFAULT 0,
    autorefresh INTEGER NOT NULL DEFAULT 0,
    folder TEXT UNIQUE NOT NULL
) STRICT
    """,
    "CREATE INDEX feed_ref_idx ON feed (last_refresh)",
    "CREATE INDEX feed_auto_idx ON feed (autorefresh)",
    """
CREATE TABLE episode (
    id INTEGER PRIMARY KEY,
    feed_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published INTEGER NOT NULL DEFAULT 0,
    link TEXT NOT NULL DEFAULT '',
    mime TEXT NOT NULL DEFAULT 'application/octet-stream',
    cur_pos INTEGER NOT NULL DEFAULT 0,
    finished INTEGER NOT NULL DEFAULT 0,
    path TEXT UNIQUE NOT NULL,
    keep INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (feed_id) REFERENCES feed (id)
) STRICT
    """,
    "CREATE INDEX episode_feed_idx ON episode (feed_id)",
    "CREATE INDEX episode_published_idx ON episode (published)",
    "CREATE INDEX episode_finished_idx ON episode (finished)",
    "CREATE INDEX episode_keep_idx ON episode (keep)",
]


class Query(Enum):
    """Symbolic constants to identify database queries"""
    FeedAdd = auto()
    FeedGetAll = auto()
    FeedGetAutorefresh = auto()
    FeedGetByID = auto()
    FeedGetByTitle = auto()
    FeedSetAutorefresh = auto()
    FeedSetRefresh = auto()
    FeedDelete = auto()
    EpisodeAdd = auto()
    EpisodeGetByFeed = auto()
    EpisodeSetPos = auto()
    EpisodeSetKeep = auto()


db_queries: Final[dict[Query, str]] = {
    Query.FeedAdd: """
INSERT INTO feed (feed_url, homepage, title, description, cover_url, autorefresh, folder)
          VALUES (       ?,        ?,     ?,           ?,         ?,           ?,      ?)
RETURNING id
    """,
    Query.FeedGetAll: """
SELECT
    id,
    feed_url,
    homepage,
    title,
    description,
    cover_url,
    last_refresh,
    autorefresh,
    folder
FROM feed
    """,
    Query.FeedGetAutorefresh: """
SELECT
    id,
    feed_url,
    homepage,
    title,
    description,
    cover_url,
    last_refresh,
    folder
FROM feed
WHERE autorefresh <> 0
    """,
    Query.FeedSetRefresh: """
UPDATE feed SET last_refresh = ? WHERE id = ?
    """,
    Query.FeedSetAutorefresh: "UPDATE feed SET autorefresh = ? WHERE id = ?",
    Query.FeedDelete: "DELETE FROM feed WHERE id = ?",
    Query.EpisodeAdd: """
INSERT INTO episode (feed_id, title, url, published, link, mime, path, description)
             VALUES (      ?,          ?,         ?,    ?,    ?,    ?,           ?)
RETURNING id
    """,
    Query.EpisodeGetByFeed: """
SELECT
    id,
    title,
    url,
    published,
    link,
    mime,
    cur_pos,
    finished,
    path,
    keep,
    description,
FROM episode
WHERE feed_id = ?
ORDER BY published DESC
    """,
    Query.EpisodeSetKeep: "UPDATE episode SET keep = ? WHERE id = ?",
    Query.EpisodeSetPos: "UPDATE episode SET cur_pos = ? WHERE id = ?",
}


class Database:
    """Database provides a wrapper around the, uh, database connection
    and exposes the operations to be performed on it."""

    __slots__ = [
        "db",
        "log",
        "path",
    ]

    db: sqlite3.Connection
    log: logging.Logger
    path: Final[str]

    def __init__(self, path: str = "") -> None:
        if path == "":
            path = common.path.db()
        self.path = path
        self.log = common.get_logger("database")
        self.log.debug("Open database at %s", path)
        with OPEN_LOCK:
            exist: Final[bool] = krylib.fexist(path)
            self.db = sqlite3.connect(path)
            self.db.isolation_level = None

            cur: Final[sqlite3.Cursor] = self.db.cursor()
            cur.execute("PRAGMA foreign_keys = true")
            cur.execute("PRAGMA journal_mode = WAL")

            if not exist:
                self.__create_db()

    def __create_db(self) -> None:
        """Initialize a freshly created database"""
        self.log.debug("Initialize fresh database at %s", self.path)
        with self.db:
            for query in INIT_QUERIES:
                cur: sqlite3.Cursor = self.db.cursor()
                cur.execute(query)
        self.log.debug("Database initialized successfully.")

    def __enter__(self) -> None:
        self.db.__enter__()

    def __exit__(self, ex_type, ex_val, traceback):
        return self.db.__exit__(ex_type, ex_val, traceback)

    def feed_add(self, f: Feed) -> None:
        """Add a new feed to the database."""
        cur = self.db.cursor()
        cur.execute(
            db_queries[Query.FeedAdd],
            (f.feed_url,
             f.homepage,
             f.title,
             f.description,
             f.cover_url,
             f.autorefresh,
             f.folder))
        row = cur.fetchone()
        assert row is not None
        assert len(row) == 1
        assert isinstance(row[0], int)
        f.fid = row[0]

    def feed_get_all(self) -> list[Feed]:
        """Fetch all Feeds from the database."""
        cur = self.db.cursor()
        cur.execute(db_queries[Query.FeedGetAll])
        feeds: list[Feed] = []
        for row in cur:
            f = Feed(
                fid=row[0],
                feed_url=row[1],
                homepage=row[2],
                title=row[3],
                description=row[4],
                cover_url=row[5],
                last_refresh=datetime.fromtimestamp(row[6]),
                autorefresh=bool(row[7]),
                folder=row[8],
            )
            feeds.append(f)
        return feeds

    def feed_get_autorefresh(self) -> list[Feed]:
        """Fetch all feeds that have autorefresh set."""
        cur = self.db.cursor()
        cur.execute(db_queries[Query.FeedGetAutorefresh])
        feeds: list[Feed] = []
        for row in cur:
            f = Feed(
                fid=row[0],
                feed_url=row[1],
                homepage=row[2],
                title=row[3],
                description=row[4],
                cover_url=row[5],
                last_refresh=datetime.fromtimestamp(row[6]),
                autorefresh=True,
                folder=row[7],
            )
            feeds.append(f)
        return feeds

    def feed_set_autorefresh(self, f: Feed, refresh: bool) -> None:
        """Set a Feed's autorefresh flag to the given value."""
        cur = self.db.cursor()
        cur.execute(db_queries[Query.FeedSetAutorefresh],
                    (refresh, f.fid))
        f.autorefresh = refresh

    def feed_set_refresh(self, f: Feed, stamp: datetime) -> None:
        """Set a Feed's refresh timestamp to the given value"""
        cur = self.db.cursor()
        cur.execute(db_queries[Query.FeedSetRefresh],
                    (stamp.timestamp(), f.fid))
        f.last_refresh = stamp

    def episode_add(self, e: Episode) -> None:
        """Add a new Episode to the database."""
        cur: Final[sqlite3.Cursor] = self.db.cursor()
        cur.execute(db_queries[Query.EpisodeAdd],
                    (e.feed_id,
                     e.title,
                     e.url,
                     e.published.timestamp(),
                     e.mime_type,
                     e.path,
                     e.description))
        row = cur.fetchone()
        e.epid = row[0]

    def episode_get_by_feed(self, f: Union[Feed, int]) -> list[Episode]:
        """Get all episodes for the given Feed."""
        fid: int = 0
        if isinstance(f, Feed):
            fid = f.fid
        else:
            fid = f

        cur: Final[sqlite3.Cursor] = self.db.cursor()
        cur.execute(db_queries[Query.EpisodeGetByFeed], (fid, ))
        episodes: list[Episode] = []
        for row in cur:
            e = Episode(
                epid=row[0],
                feed_id=fid,
                title=row[1],
                url=row[2],
                published=datetime.fromtimestamp(row[3]),
                link=row[4],
                mime_type=row[5],
                cur_pos=row[6],
                finished=row[7],
                path=row[8],
                keep=row[9],
                description=row[10],
            )
            episodes.append(e)

        return episodes


# Local Variables: #
# python-indent: 4 #
# End: #
