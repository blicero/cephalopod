#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-15 19:19:41 krylon>
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
from enum import Enum, auto
from typing import Final

import krylib

from cephalopod import common

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
    url TEXT NOT NULL,
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

# Local Variables: #
# python-indent: 4 #
# End: #
