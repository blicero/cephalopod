#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-14 19:03:54 krylon>
#
# /data/code/python/cephalopod/common.py
# created on 14. 03. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
cephalopod.common

(c) 2024 Benjamin Walkenhorst
"""

import logging
import logging.handlers
import os
from typing import Final
from threading import Lock

APP_NAME: Final[str] = "Cephalopod"
APP_VERSION: Final[str] = "0.0.1"
DEBUG: Final[bool] = True
TIME_FMT: Final[str] = "%Y-%m-%d %H:%M:%S"


class Path:
    """Holds the paths of folders and files used by the application"""

    __base: str

    def __init__(self, root: str = os.path.expanduser(f"~/.{APP_NAME.lower()}.d")) -> None:  # noqa
        self.__base = root

    def base(self, folder: str = "") -> str:
        """Return the base directory for application specific files.
        If path is a non-empty string, set the base directory to its value."""
        if folder != "":
            self.__base = folder
        return self.__base

    def window(self) -> str:
        """Return the path of the window state file"""
        return os.path.join(self.__base, f"{APP_NAME.lower()}.win")

    def db(self) -> str:  # pylint: disable-msg=C0103
        """Return the path to the database"""
        return os.path.join(self.__base, f"{APP_NAME.lower()}.db")

    def log(self) -> str:
        """Return the path to the log file"""
        return os.path.join(self.__base, f"{APP_NAME.lower()}.log")

    def config(self) -> str:
        """Return the path of the configuration file"""
        return os.path.join(self.__base, "settings.toml")

    def download(self) -> str:
        """Return the path of the download folder"""
        return os.path.join(self.__base, "downloads")


path: Path = Path(os.path.expanduser(f"~/.{APP_NAME.lower()}.d"))

_lock: Final[Lock] = Lock()  # pylint: disable-msg=C0103
_cache: Final[dict[str, logging.Logger]] = {}  # pylint: disable-msg=C0103


def set_basedir(folder: str) -> None:
    """Set the base dir to the speficied path."""
    path.base(folder)
    init_app()


def init_app() -> None:
    """Initialize the application environment"""
    if not os.path.isdir(path.base()):
        print(f"Create base directory {path.base()}")
        os.mkdir(path.base())
    if not os.path.isdir(path.download()):
        print(f"Create download folder {path.download()}")
        os.mkdir(path.download())


def get_logger(name: str, terminal: bool = True) -> logging.Logger:
    """Create and return a logger with the given name"""
    with _lock:
        init_app()

        if name in _cache:
            return _cache[name]

        log_format = "%(asctime)s (%(name)-16s / line %(lineno)-4d) " + \
            "- %(levelname)-8s %(message)s"
        max_log_size = 256 * 2**20
        max_log_count = 4

        log_obj = logging.getLogger(name)
        log_obj.setLevel(logging.DEBUG)
        log_file_handler = logging.handlers.RotatingFileHandler(path.log(),
                                                                'a',
                                                                max_log_size,
                                                                max_log_count)

        log_fmt = logging.Formatter(log_format)
        log_file_handler.setFormatter(log_fmt)
        log_obj.addHandler(log_file_handler)

        if terminal:
            log_console_handler = logging.StreamHandler()
            log_console_handler.setFormatter(log_fmt)
            log_console_handler.setLevel(logging.DEBUG)
            log_obj.addHandler(log_console_handler)

        _cache[name] = log_obj
        return log_obj


# Local Variables: #
# python-indent: 4 #
# End: #