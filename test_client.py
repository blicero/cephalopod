#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-22 21:00:48 krylon>
#
# /data/code/python/cephalopod/test_client.py
# created on 22. 03. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
cephalopod.test_client

(c) 2024 Benjamin Walkenhorst
"""

import os
import unittest
from datetime import datetime
from typing import Final

import feedparser
from krylib import isdir

from cephalopod import common
from cephalopod.cast import Episode, Feed
from cephalopod.client import Client
from cephalopod.test_example_feed import EXAMPLE_FEED

TEST_FEED_URL: Final[str] = "http://feeds.feedburner.com/sternengeschichten"


TEST_ROOT: str = "/tmp/"

# On my main development machines, I have a RAM disk mounted at /data/ram.
# If it's available, I'd rather use that than /tmp which might live on disk.
if isdir("/data/ram"):
    TEST_ROOT = "/data/ram"


class ClientTest(unittest.TestCase):
    """Test the Database class. Duh."""

    client: Client
    folder: str

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

    def __get_client(self) -> Client:
        return self.__class__.client

    def test_01_client_create(self) -> None:
        """Test creating a Client instance."""
        try:
            self.__class__.client = Client()
        except Exception as e:  # pylint: disable-msg=W0718
            self.fail(f"Exception raised while creating Client: {e}")
        finally:
            self.assertIsNotNone(self.__class__.client)

    def test_02_feed_add(self) -> None:
        """Try adding a feed to the database."""
        client = self.__get_client()
        try:
            f: Feed = client.feed_add(TEST_FEED_URL)
        except Exception as e:  # pylint: disable-msg=W0718
            self.fail(f"Exception while trying to add Feed: {e}")
        else:
            self.assertIsNotNone(f)
            self.assertGreater(f.fid, 0)

    def test_03_process_feed(self) -> None:
        """Try processing a parsed feed."""
        raw = feedparser.parse(EXAMPLE_FEED)
        client = self.__get_client()
        feed = client.get_database().feed_get_all()[0]
        try:
            episodes: list[Episode] = client.process_feed(feed, raw)
        except Exception as e:  # pylint: disable-msg=W0718
            self.fail(f"Exception while processing Feed: {e}")
        else:
            self.assertIsNotNone(episodes)
            self.assertEqual(len(episodes), 5)


# Local Variables: #
# python-indent: 4 #
# End: #
