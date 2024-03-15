#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-15 09:43:35 krylon>
#
# /data/code/python/cephalopod/cast.py
# created on 14. 03. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
cephalopod.cast

(c) 2024 Benjamin Walkenhorst
"""

from datetime import datetime, timedelta
from dataclass import dataclass
from typing import Optional


@dataclass(slots=True, kw_only=True)
class Feed:
    """A podcast feed"""

    pid: int
    feed_url: str
    homepage: Optional[str]
    title: str
    description: str
    cover_url: str
    last_refresh: datetime
    autorefresh: bool
    folder: str

    def age(self) -> timedelta:
        """Return the time that has passed since the last refresh of this podcast"""
        return datetime.now() - self.last_refresh


@dataclass(slots=True, kw_only=True)
class Episode:
    """A podcast episode"""

    epid: int
    feed_id: int
    title: str
    url: str
    published: datetime
    link: str
    mime_type: str
    cur_pos: int
    finished: bool
    path: str
    keep: bool
    description: str


# Local Variables: #
# python-indent: 4 #
# End: #
