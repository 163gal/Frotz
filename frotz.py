# Frotz activity, wrapper for the frotz interactive fiction interpreter
#
# Copyright (C) 2008  Joshua Minor
#
# Parts of Frotz activity are based on code from Terminal activity
# Copyright (C) 2007  Eduardo Silva <edsiper@gmail.com>.
# Copyright (C) 2008  One Laptop per Child
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import configparser
import logging
import os
import shutil
import platform
import sys
import time
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Vte', '2.91')

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Vte
from gi.repository import Gdk
from gi.repository import Pango

from sugar3.activity import activity
from sugar3 import env, profile
from sugar3.datastore import datastore
from sugar3.activity.activity import launch_bundle
from sugar3.graphics.toolbarbox import ToolbarBox, ToolbarButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.activity.widgets import EditToolbar, ActivityToolbarButton, StopButton
from sugar3.graphics import style
from sugar3.graphics.alert import ConfirmationAlert


class FrotzActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        logging.debug('Starting the Frotz activity')

        self.set_title(_('Frotz'))
        self.connect('key-press-event', self.__key_press_cb)

        self.toolbox = ToolbarBox()
        self.activity_toolbar_button = ActivityToolbarButton(self)
        self.toolbox.toolbar.insert(self.activity_toolbar_button, -1)
        self.activity_toolbar_button.show()

        self._edit_toolbar = EditToolbar()
        button = ToolbarButton()
        button.set_page(self._edit_toolbar)
        button.props.icon_name = 'toolbar-edit'
        button.props.label = _('Edit')
        self.toolbox.toolbar.insert(button, -1)
        button.show()
        self._edit_toolbar.show()
        self._edit_toolbar.undo.props.visible = False
        self._edit_toolbar.redo.props.visible = False
        self._edit_toolbar.separator.props.visible = False
        self._edit_toolbar.copy.connect('clicked', self._copy_cb)
        self._edit_toolbar.copy.props.accelerator = '<Ctrl><Shift>C'
        self._edit_toolbar.paste.connect('clicked', self._paste_cb)
        self._edit_toolbar.paste.props.accelerator = '<Ctrl><Shift>V'

        self.set_toolbar_box(self.toolbox)
        activity_toolbar = self.toolbox.get_toolbar()

        # Add a button that will send you to the ifarchive to get more games
        activity_toolbar.get_games = ToolButton('activity-get-games')
        activity_toolbar.get_games.set_tooltip(_('Get More Games'))
        activity_toolbar.get_games.connect('clicked', self._get_games_cb)
        activity_toolbar.insert(activity_toolbar.get_games, 2)
        activity_toolbar.get_games.show()
        self.toolbox.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self.toolbox.toolbar.insert(separator, -1)
        separator.show()

        stop = StopButton(self)
        self.toolbox.toolbar.insert(stop, -1)
        stop.show()

        box = Gtk.HBox(False, 4)

        self._vte = VTE()
        self._vte.set_encoding('utf-8')
        self._vte.show()
        self._vte.connect("child-exited", self._quit_cb)

        scrollbar = Gtk.VScrollbar(self._vte.get_vadjustment())
        scrollbar.show()

        box.pack_start(child=self._vte, expand=True, fill=True, padding=0)
        box.pack_start(child=scrollbar, expand=False, fill=False, padding=0)
        
        self.set_canvas(box)
        box.show()
        
        self._vte.grab_focus()
        
        self.game_started = False
        default_game_file = os.path.join(activity.get_bundle_path(), "Advent.z5")
        # when we return to the idle state, launch the default game
        # if read_file is called, that will override this
        GLib.idle_add(self.start_game, default_game_file)

    def _quit_cb(self, vte, foo=None):
        logging.debug("Quitting...")
        self.close()

    def _start_frotz(self, game_file):
        # cd to a persistent directory so that saved games
        # will have a place to live
        save_dir = os.path.join(
            os.environ["SUGAR_ACTIVITY_ROOT"], "data")
        # print a welcome banner and pause for a moment that
        # way the end user will have a chance to see which
        # version of frotz we are using and which file we are
        # loading
        cmd = "cd '%s'; " % save_dir
        cmd += "clear; "
        cmd += "frotz|head -3 ; "
        cmd += "echo '\nLoading %s...'; " % os.path.basename(game_file)
        cmd += "sleep 2; frotz '%s'; " % game_file
        cmd += "exit\n"
        self._vte.feed_child(cmd.encode('utf-8'))

    def start_game(self, game_file):
        if self.game_started:
            return False

        self.game_started = True

        if not shutil.which('frotz'):
            alert = ConfirmationAlert()
            alert.props.title = "Frotz is missing"
            alert.props.msg = "Install frotz by clicking OK"
            alert.connect('response', self._alert_response_cb)
            self.add_alert(alert)
            alert.show()
            alert = ConfirmationAlert()
            alert.props.title = "Start Game"
            alert.connect('response', self._game_start_cb)
            self.add_alert(alert)
            alert.show()
            return False

        logging.debug('Using frotz installed in the system')
        self._start_frotz(game_file)
        return False

    def _alert_response_cb(self, alert, response_id):

        self.remove_alert(alert)
        if response_id == Gtk.ResponseType.OK:
            logging.debug("Installing frotz")
            if platform.version().find("Ubuntu") > -1 or platform.version().find("Debian") > -1:
                self._vte.feed_child(b'sudo apt install frotz\n')
            else:
                self._vte.feed_child(b'sudo dnf install frotz\n')

    def _game_start_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id == Gtk.ResponseType.OK:
            logging.debug("Starting frotz")
            game_file = os.path.join(activity.get_bundle_path(), "Advent.z5")
            self._start_frotz(game_file)

    def read_file(self, file_path):
        self.start_game(file_path)

    def _get_games_cb(self, button):

        url = 'https://github.com/sugarlabs/Frotz/#downloading-games'
        path = os.path.join(self.get_activity_root(),
                            'instance', '%i' % time.time())
        fd = open(path, "w")
        fd.write(url)
        fd.close()
        journal_entry = datastore.create()
        journal_entry.metadata['title'] = 'Browse Activity'
        journal_entry.metadata['title_set_by_user'] = '1'
        journal_entry.metadata['keep'] = '0'
        journal_entry.metadata['mime_type'] = 'text/uri-list'
        journal_entry.metadata['icon-color'] = profile.get_color().to_string()
        journal_entry.metadata['description'] = \
            "Frotz activity, downloading games".format(url)
        journal_entry.file_path = path
        datastore.write(journal_entry)
        self._object_id = journal_entry.object_id
        launch_bundle(object_id=self._object_id)

    def _copy_cb(self, button):
        if self._vte.get_has_selection():
            self._vte.copy_clipboard()

    def _paste_cb(self, button):
        self._vte.paste_clipboard()

    def __key_press_cb(self, window, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.state & Gdk.ModifierType.SHIFT_MASK:
        
            if Gdk.keyval_name(event.keyval) == "C":
                if self._vte.get_has_selection():
                    self._vte.copy_clipboard()              
                return True
            elif Gdk.keyval_name(event.keyval) == "V":
                self._vte.paste_clipboard()
                return True

        return False


class VTE(Vte.Terminal):

    def __init__(self):
        Vte.Terminal.__init__(self)
        self.configure_terminal()

        # os.chdir(os.environ["HOME"])
        if hasattr(Vte.Terminal, "spawn_sync"):
            self.spawn_sync(
                Vte.PtyFlags.DEFAULT,
                os.environ["HOME"],
                ["/bin/bash"],
                [],
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None)
        else:
            self.fork_command_full(
                Vte.PtyFlags.DEFAULT,
                os.environ["HOME"],
                ["/bin/bash"],
                [],
                GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                None,
                None)

    def color_parse(self, color):
        rgba = Gdk.RGBA()
        rgba.parse(color)
        return rgba

    def configure_terminal(self):
        conf = configparser.ConfigParser()
        conf_file = os.path.join(env.get_profile_path(), 'terminalrc')

        if os.path.isfile(conf_file):
            with open(conf_file, 'r') as f:
                conf.read_file(f) 
        else:
            conf.add_section('terminal')

        if conf.has_option('terminal', 'font'):
            font = conf.get('terminal', 'font')
        else:
            font = 'Monospace'
            conf.set('terminal', 'font', font)
        font_desc = Pango.FontDescription(font)
        font_desc.set_size(style.FONT_SIZE * Pango.SCALE)
        self.set_font(font_desc)

        if conf.has_option('terminal', 'fg_color'):
            fg_color = conf.get('terminal', 'fg_color')
        else:
            fg_color = '#000000'
            conf.set('terminal', 'fg_color', fg_color)
        if conf.has_option('terminal', 'bg_color'):
            bg_color = conf.get('terminal', 'bg_color')
        else:
            bg_color = '#FFFFFF'
            conf.set('terminal', 'bg_color', bg_color)

        self.set_colors(self.color_parse(bg_color),
                        self.color_parse(fg_color), [])

        if conf.has_option('terminal', 'cursor_blink'):
            blink = conf.getboolean('terminal', 'cursor_blink')
        else:
            blink = 'False'
            conf.set('terminal', 'cursor_blink', blink)
        blink = Vte.CursorBlinkMode(0) if blink == 'False' else Vte.CursorBlinkMode(1)
        self.set_cursor_blink_mode(blink)

        if conf.has_option('terminal', 'bell'):
            bell = conf.getboolean('terminal', 'bell')
        else:
            bell = False
            conf.set('terminal', 'bell', str(bell))
        self.set_audible_bell(bell)

        if conf.has_option('terminal', 'scrollback_lines'):
            scrollback_lines = conf.getint('terminal', 'scrollback_lines')
        else:
            scrollback_lines = 1000
            conf.set('terminal', 'scrollback_lines', str(scrollback_lines))

        self.set_scrollback_lines(scrollback_lines)
        self.set_allow_bold(True)

        if conf.has_option('terminal', 'scroll_on_keystroke'):
            scroll_key = conf.getboolean('terminal', 'scroll_on_keystroke')
        else:
            scroll_key = False
            conf.set('terminal', 'scroll_on_keystroke', str(scroll_key))
        self.set_scroll_on_keystroke(scroll_key)

        if conf.has_option('terminal', 'scroll_on_output'):
            scroll_output = conf.getboolean('terminal', 'scroll_on_output')
        else:
            scroll_output = False
            conf.set('terminal', 'scroll_on_output', str(scroll_output))
        self.set_scroll_on_output(scroll_output)

        if hasattr(self, 'set_emulation'):
            if conf.has_option('terminal', 'emulation'):
                emulation = conf.get('terminal', 'emulation')
            else:
                emulation = 'xterm'
                conf.set('terminal', 'emulation', emulation)
            self.set_emulation(emulation)

        if hasattr(self, 'set_visible_bell'):
            if conf.has_option('terminal', 'visible_bell'):
                visible_bell = conf.getboolean('terminal', 'visible_bell')
            else:
                visible_bell = False
                conf.set('terminal', 'visible_bell', str(visible_bell))
            self.set_visible_bell(visible_bell)
        conf.write(open(conf_file, 'w'))

    def on_gconf_notification(self, client, cnxn_id, entry, what):
        self.reconfigure_vte()

    def on_vte_button_press(self, term, event):
        if event.button == 3:
            self.do_popup(event)
            return True

    def on_vte_popup_menu(self, term):
        pass
