#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-23 21:13:31 krylon>
#
# /data/code/python/cephalopod/ui.py
# created on 23. 03. 2024
# (c) 2024 Benjamin Walkenhorst
#
# This file is part of the Wetterfrosch weather app. It is distributed
# under the terms of the GNU General Public License 3. See the file
# LICENSE for details or find a copy online at
# https://www.gnu.org/licenses/gpl-3.0

"""
cephalopod.ui

(c) 2024 Benjamin Walkenhorst
"""

from threading import Lock, local
from typing import Final

import gi  # type: ignore

from cephalopod import common

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GLib", "2.0")
gi.require_version("Gio", "2.0")

from gi.repository import \
    Gdk as gdk  # noqa: E402 pylint: disable-msg=C0413,C0411 # type: ignore
from gi.repository import \
    GLib as glib  # noqa: E402 pylint: disable-msg=C0413,C0411 # type: ignore
from gi.repository import \
    Gtk as gtk  # noqa: E402 pylint: disable-msg=C0413,C0411 # type: ignore


ICON_NAME_DEFAULT: Final[str] = ''


class GUI:
    """A graphical user interface, implemented using Gtk+ 3"""

    def __init__(self) -> None:
        self.log = common.get_logger("GUI")
        self.lock: Final[Lock] = Lock()
        self.local = local()
        self.visible: bool = False
        self.active: bool = True

        self.win = gtk.Window()
        self.win.set_title(f"{common.APP_NAME} {common.APP_VERSION}")
        self.win.set_icon_name(ICON_NAME_DEFAULT)
        self.tray = gtk.StatusIcon.new_from_icon_name(ICON_NAME_DEFAULT)
        self.tray.set_has_tooltip(True)
        self.tray.set_title(f"{common.APP_NAME} {common.APP_VERSION}")
        self.tray.set_tooltip_text(f"{common.APP_NAME} {common.APP_VERSION}")

        glib.timeout_add(2_500, self.periodic)

    def periodic(self) -> None:
        """Perform routine periodic things."""
        pass


# Local Variables: #
# python-indent: 4 #
# End: #
