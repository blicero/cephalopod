#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: <2024-03-26 14:36:11 krylon>
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
from cephalopod.cast import Episode, Feed
from cephalopod.database import Database

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GLib", "2.0")
# gi.require_version("Gio", "2.0")

# from gi.repository import \
#     Gdk as gdk  # noqa: E402 pylint: disable-msg=C0413,C0411 # type: ignore
from gi.repository import \
    GLib as glib  # noqa: E402 pylint: disable-msg=C0413,C0411 # type: ignore
from gi.repository import \
    Gtk as gtk  # noqa: E402 pylint: disable-msg=C0413,C0411 # type: ignore

ICON_NAME_DEFAULT: Final[str] = ''


class GUI:  # pylint: disable-msg=R0902,R0903
    """A graphical user interface, implemented using Gtk+ 3"""

    def __init__(self) -> None:  # pylint: disable-msg=R0915
        self.log = common.get_logger("GUI")
        self.lock: Final[Lock] = Lock()
        self.local = local()
        self.visible: bool = False
        self.active: bool = True

        # Create window and widgets

        self.win = gtk.Window()
        self.win.set_title(f"{common.APP_NAME} {common.APP_VERSION}")
        self.win.set_icon_name(ICON_NAME_DEFAULT)
        self.tray = gtk.StatusIcon.new_from_icon_name(ICON_NAME_DEFAULT)
        self.tray.set_has_tooltip(True)
        self.tray.set_title(f"{common.APP_NAME} {common.APP_VERSION}")
        self.tray.set_tooltip_text(f"{common.APP_NAME} {common.APP_VERSION}")

        self.mbox: gtk.Box = gtk.Box(orientation=gtk.Orientation.VERTICAL)

        self.notebook: gtk.Notebook = gtk.Notebook.new()
        self.nb_label_feed = gtk.Label.new("Feeds")
        self.nb_label_episode = gtk.Label.new("Episodes")

        self.sw_feeds = gtk.ScrolledWindow()
        self.sw_episodes = gtk.ScrolledWindow()

        for sw in (self.sw_feeds, self.sw_episodes):
            sw.set_vexpand(True)
            sw.set_hexpand(True)

        feed_columns: Final[list[tuple[int, str]]] = [
            (0, "ID"),
            (1, "Title"),
            (2, "Refresh"),
            (4, "New episodes"),
        ]

        self.feed_store = gtk.ListStore(
            int,  # Feed ID
            str,  # Title
            str,  # Refresh timestamp
            int,  # Number of new episodes
        )

        self.feed_view = gtk.TreeView(model=self.feed_store)

        for c in feed_columns:
            col = gtk.TreeViewColumn(
                c[1],
                gtk.CellRendererText(),
                text=c[0],
                size=12,
            )
            self.feed_view.append_column(col)

        episode_columns: Final[list[tuple[int, str]]] = [
            (0, "ID"),
            (1, "Feed"),
            (2, "Number"),
            (3, "Published"),
            (4, "Title"),
            (5, "Duration"),
            (6, "Position"),
        ]

        self.episode_store = gtk.ListStore(
            int,  # Episode ID
            str,  # Feed name
            int,  # Episode number
            str,  # Date published
            str,  # Episode Title
            str,  # Duration
            str,  # Playback position
        )

        self.episode_view = gtk.TreeView(model=self.episode_store)

        for c in episode_columns:
            col = gtk.TreeViewColumn(
                c[1],
                gtk.CellRendererText(),
                text=c[0],
                size=12,
            )
            self.episode_view.append_column(col)

        # Menu

        self.menubar = gtk.MenuBar()
        self.feed_menu_item: gtk.MenuItem = \
            gtk.MenuItem.new_with_mnemonic("_Feed")

        self.feed_menu = gtk.Menu()
        self.feed_menu_item.set_submenu(self.feed_menu)

        self.fm_add_item = gtk.MenuItem.new_with_mnemonic("_Add Feed")
        self.fm_quit_item = gtk.MenuItem.new_with_mnemonic("_Quit")

        self.feed_menu.add(self.fm_add_item)
        self.feed_menu.add(self.fm_quit_item)

        self.menubar.add(self.feed_menu_item)

        # Assemble UI

        self.sw_feeds.add(self.feed_view)
        self.sw_episodes.add(self.episode_view)

        self.notebook.append_page(self.sw_feeds, self.nb_label_feed)
        self.notebook.append_page(self.sw_episodes, self.nb_label_episode)

        self.mbox.pack_start(self.menubar, False, True, 0)
        self.mbox.pack_start(self.notebook, False, True, 0)

        self.win.add(self.mbox)

        self.win.show_all()

        # Register signal handlers

        self.win.connect("destroy", self.quit)
        self.fm_quit_item.connect("activate", self.quit)

        glib.timeout_add(2_500, self.periodic)
        glib.timeout_add(50, self.load_models)

    def quit(self, _whatever) -> None:
        self.log.info("Bye bye!")
        self.win.destroy()
        gtk.main_quit()

    def get_database(self) -> Database:
        """Get the Database instance for the calling thread."""
        try:
            return self.local.db
        except AttributeError:
            db = Database()
            self.local.db = db
            return db

    def load_models(self) -> None:
        """Fill the TreeModels with data from the database."""
        db: Database = self.get_database()

        feeds: Final[list[Feed]] = db.feed_get_all()
        ftitles: dict[int, str] = {}

        self.feed_store.clear()

        for f in feeds:
            ftitles[f.fid] = f.title
            fiter = self.feed_store.append()
            self.feed_store.set(
                fiter,
                (0, 1, 2, 3),
                (f.fid,
                 f.title,
                 f.last_refresh.strftime(common.TIME_FMT),
                 0),
            )

        episodes: Final[list[Episode]] = db.episode_get_all()
        self.episode_store.clear()
        self.log.debug("Add %d episodes to episode_store",
                       len(episodes))

        for e in episodes:
            e_iter = self.episode_store.append()
            self.episode_store.set(
                e_iter,
                (0, 1, 2, 3, 4, 5, 6),
                (
                    e.epid,
                    ftitles[e.feed_id],
                    e.number,
                    e.published.strftime(common.TIME_FMT),
                    e.title,
                    "??:??:??",
                    fmt_pos(e.cur_pos),
                ),
            )

    def periodic(self) -> bool:
        """Perform routine periodic things."""
        self.log.debug("Do periodic stuff.")
        return True


def fmt_pos(p: int) -> str:
    """Format the argument p as a playback position, i.e. minutes and seconds."""
    hours: int = 0
    minutes: int = 0
    seconds: int = p

    if seconds >= 3600:
        hours, seconds = divmod(seconds, 3600)

    if seconds >= 60:
        minutes, seconds = divmod(seconds, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main() -> None:
    """Display the GUI and run the gtk mainloop"""
    mw = GUI()
    mw.log.debug("Let's go")
    gtk.main()


if __name__ == "__main__":
    main()


# Local Variables: #
# python-indent: 4 #
# End: #
