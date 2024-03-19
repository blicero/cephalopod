#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-19 14:55:34 krylon>
#
# /home/krylon/code/python/cephalopod/test_database.py
# created on 19. 03. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
cephalopod.test_database

(c) 2024 Benjamin Walkenhorst
"""

import os
import unittest
from datetime import datetime

from cephalopod import common, database
from cephalopod.cast import Feed
from krylib import isdir

TEST_ROOT: str = "/tmp/"

# On my main development machines, I have a RAM disk mounted at /data/ram.
# If it's available, I'd rather use that than /tmp which might live on disk.
if isdir("/data/ram"):
    TEST_ROOT = "/data/ram"


class DatabaseTest(unittest.TestCase):
    """Test the Database class. Duh."""

    folder: str
    db: database.Database

    @classmethod
    def setUpClass(cls) -> None:
        stamp = datetime.now()
        folder_name = \
            stamp.strftime("wetterfrosch_test_database_%Y%m%d_%H%M%S")
        cls.folder = os.path.join(TEST_ROOT,
                                  folder_name)
        common.set_basedir(cls.folder)

    @classmethod
    def tearDownClass(cls) -> None:
        os.system(f"/bin/rm -rf {cls.folder}")

    def __get_db(self) -> database.Database:
        """Get the shared database instance."""
        return self.__class__.db

    def test_01_db_open(self) -> None:
        """Test opening the database."""
        try:
            self.__class__.db = database.Database(common.path.db())
        except Exception as e:  # pylint: disable-msg=W0718
            self.fail(f"Failed to open database: {e}")
        finally:
            self.assertIsNotNone(self.__class__.db)

    def test_02_db_feed_add(self) -> None:
        """Try adding a feed."""
        test_cases: list[tuple[Feed, bool]] = [
            (Feed(
                fid=0,
                feed_url="https://www.example.com/podcast.feed?audio=opus",
                homepage="https://www.example.com/",
                title="The Example Podcast",
                description="Exciting new examples, fresh in your feed, every Monday",
                cover_url="https://static.example.com/podcast.jpg",
                last_refresh=datetime.fromtimestamp(0),
                autorefresh=True,
                folder="/tmp/podcast",
            ), False),
        ]

        db = self.__get_db()

        for c in test_cases:
            try:
                with db:
                    db.feed_add(c[0])
            except Exception as e:
                if not c[1]:
                    self.fail("Unexpected exception adding feed %s: %s" %
                              (c[0].title, e))
            else:
                if c[1]:
                    self.fail("Adding podcast %s to database should not have worked!" %
                              c[0].title)

# Local Variables: #
# python-indent: 4 #
# End: #
