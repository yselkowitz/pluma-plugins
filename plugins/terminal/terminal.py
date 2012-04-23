# -*- coding: utf8 -*-

# terminal.py - Embeded VTE terminal for pluma
# This file is part of pluma
#
# Copyright (C) 2005-2006 - Paolo Borelli
#
# pluma is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# pluma is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pluma; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA

import pluma
import pluma.utils
import pango
import gtk
import gobject
import vte
import mateconf
import gettext
import os
import gio
from gpdefs import *

try:
    gettext.bindtextdomain(GETTEXT_PACKAGE, GP_LOCALEDIR)
    _ = lambda s: gettext.dgettext(GETTEXT_PACKAGE, s);
except:
    _ = lambda s: s

class PlumaTerminal(gtk.HBox):
    """VTE terminal which follows mate-terminal default profile options"""

    __gsignals__ = {
        "populate-popup": (
            gobject.SIGNAL_RUN_LAST,
            None,
            (gobject.TYPE_OBJECT,)
        )
    }

    MATECONF_PROFILE_DIR = "/apps/mate-terminal/profiles/Default"

    defaults = {
        'allow_bold'            : True,
        'audible_bell'          : False,
        'background'            : None,
        'backspace_binding'     : 'ascii-del',
        'cursor_blink_mode'     : vte.CURSOR_BLINK_SYSTEM,
        'cursor_shape'          : vte.CURSOR_SHAPE_BLOCK,
        'emulation'             : 'xterm',
        'font_name'             : 'Monospace 10',
        'scroll_on_keystroke'   : False,
        'scroll_on_output'      : False,
        'scrollback_lines'      : 100,
        'visible_bell'          : False,
        'word_chars'            : '-A-Za-z0-9,./?%&#:_'
    }

    def __init__(self):
        gtk.HBox.__init__(self, False, 4)

        mateconf_client.add_dir(self.MATECONF_PROFILE_DIR,
                             mateconf.CLIENT_PRELOAD_RECURSIVE)

        self._vte = vte.Terminal()
        self.reconfigure_vte()
        self._vte.set_size(self._vte.get_column_count(), 5)
        self._vte.set_size_request(200, 50)
        self._vte.show()
        self.pack_start(self._vte)

        self._scrollbar = gtk.VScrollbar(self._vte.get_adjustment())
        self._scrollbar.show()
        self.pack_start(self._scrollbar, False, False, 0)

        mateconf_client.notify_add(self.MATECONF_PROFILE_DIR,
                                self.on_mateconf_notification)

        # we need to reconf colors if the style changes
        self._vte.connect("style-set", lambda term, oldstyle: self.reconfigure_vte())
        self._vte.connect("key-press-event", self.on_vte_key_press)
        self._vte.connect("button-press-event", self.on_vte_button_press)
        self._vte.connect("popup-menu", self.on_vte_popup_menu)
        self._vte.connect("child-exited", lambda term: term.fork_command())

        self._accel_base = '<pluma>/plugins/terminal'
        self._accels = {
            'copy-clipboard': [gtk.keysyms.C, gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK, self.copy_clipboard],
            'paste-clipboard': [gtk.keysyms.V, gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK, self.paste_clipboard]
        }

        for name in self._accels:
            path = self._accel_base + '/' + name
            accel = gtk.accel_map_lookup_entry(path)

            if accel == None:
                 gtk.accel_map_add_entry(path, self._accels[name][0], self._accels[name][1])

        self._vte.fork_command()

    def do_grab_focus(self):
        self._vte.grab_focus()

    def reconfigure_vte(self):
        # Fonts
        if mateconf_get_bool(self.MATECONF_PROFILE_DIR + "/use_system_font"):
            font_name = mateconf_get_str("/desktop/mate/interface/monospace_font_name",
                                      self.defaults['font_name'])
        else:
            font_name = mateconf_get_str(self.MATECONF_PROFILE_DIR + "/font",
                                      self.defaults['font_name'])

        try:
            self._vte.set_font(pango.FontDescription(font_name))
        except:
            pass

        # colors
        self._vte.ensure_style()
        style = self._vte.get_style()
        fg = style.text[gtk.STATE_NORMAL]
        bg = style.base[gtk.STATE_NORMAL]
        palette = []

        if not mateconf_get_bool(self.MATECONF_PROFILE_DIR + "/use_theme_colors"):
            fg_color = mateconf_get_str(self.MATECONF_PROFILE_DIR + "/foreground_color", None)
            if (fg_color):
                fg = gtk.gdk.color_parse (fg_color)
            bg_color = mateconf_get_str(self.MATECONF_PROFILE_DIR + "/background_color", None)
            if (bg_color):
                bg = gtk.gdk.color_parse (bg_color)
        str_colors = mateconf_get_str(self.MATECONF_PROFILE_DIR + "/palette", None)
        if (str_colors):
            for str_color in str_colors.split(':'):
                try:
                    palette.append(gtk.gdk.color_parse(str_color))
                except:
                    palette = []
                    break
            if (len(palette) not in (0, 8, 16, 24)):
                palette = []
        self._vte.set_colors(fg, bg, palette)

        # cursor blink
        blink_mode = mateconf_get_str(self.MATECONF_PROFILE_DIR + "/cursor_blink_mode")
        if blink_mode.lower() == "system":
            blink = vte.CURSOR_BLINK_SYSTEM
        elif blink_mode.lower() == "on":
            blink = vte.CURSOR_BLINK_ON
        elif blink_mode.lower() == "off":
            blink = vte.CURSOR_BLINK_OFF
        else:
            blink = self.defaults['cursor_blink_mode']
        self._vte.set_cursor_blink_mode(blink)

        # cursor shape
        cursor_shape = mateconf_get_str(self.MATECONF_PROFILE_DIR + "/cursor_shape")
        if cursor_shape.lower() == "block":
            shape = vte.CURSOR_SHAPE_BLOCK
        elif cursor_shape.lower() == "ibeam":
            shape = vte.CURSOR_SHAPE_IBEAM
        elif cursor_shape.lower() == "underline":
            shape = vte.CURSOR_SHAPE_UNDERLINE
        else:
            shape = self.defaults['cursor_shape']
        self._vte.set_cursor_shape(shape)

        self._vte.set_audible_bell(not mateconf_get_bool(self.MATECONF_PROFILE_DIR + "/silent_bell",
                                                      not self.defaults['audible_bell']))

        self._vte.set_scrollback_lines(mateconf_get_int(self.MATECONF_PROFILE_DIR + "/scrollback_lines",
                                                     self.defaults['scrollback_lines']))

        self._vte.set_allow_bold(mateconf_get_bool(self.MATECONF_PROFILE_DIR + "/allow_bold",
                                                self.defaults['allow_bold']))

        self._vte.set_scroll_on_keystroke(mateconf_get_bool(self.MATECONF_PROFILE_DIR + "/scroll_on_keystroke",
                                                         self.defaults['scroll_on_keystroke']))

        self._vte.set_scroll_on_output(mateconf_get_bool(self.MATECONF_PROFILE_DIR + "/scroll_on_output",
                                                      self.defaults['scroll_on_output']))

        self._vte.set_word_chars(mateconf_get_str(self.MATECONF_PROFILE_DIR + "/word_chars",
                                               self.defaults['word_chars']))

        self._vte.set_emulation(self.defaults['emulation'])
        self._vte.set_visible_bell(self.defaults['visible_bell'])

    def on_mateconf_notification(self, client, cnxn_id, entry, what):
        self.reconfigure_vte()

    def on_vte_key_press(self, term, event):
        modifiers = event.state & gtk.accelerator_get_default_mod_mask()
        if event.keyval in (gtk.keysyms.Tab, gtk.keysyms.KP_Tab, gtk.keysyms.ISO_Left_Tab):
            if modifiers == gtk.gdk.CONTROL_MASK:
                self.get_toplevel().child_focus(gtk.DIR_TAB_FORWARD)
                return True
            elif modifiers == gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK:
                self.get_toplevel().child_focus(gtk.DIR_TAB_BACKWARD)
                return True

        for name in self._accels:
            path = self._accel_base + '/' + name
            entry = gtk.accel_map_lookup_entry(path)

            if entry and entry[0] == event.keyval and entry[1] == modifiers:
                self._accels[name][2]()
                return True

        return False

    def on_vte_button_press(self, term, event):
        if event.button == 3:
            self._vte.grab_focus()
            self.do_popup(event)
            return True

    def on_vte_popup_menu(self, term):
        self.do_popup()

    def create_popup_menu(self):
        menu = gtk.Menu()

        item = gtk.ImageMenuItem(gtk.STOCK_COPY)
        item.connect("activate", lambda menu_item: self.copy_clipboard())
        item.set_accel_path(self._accel_base + '/copy-clipboard')
        item.set_sensitive(self._vte.get_has_selection())
        menu.append(item)

        item = gtk.ImageMenuItem(gtk.STOCK_PASTE)
        item.connect("activate", lambda menu_item: self.paste_clipboard())
        item.set_accel_path(self._accel_base + '/paste-clipboard')
        menu.append(item)

        self.emit("populate-popup", menu)
        menu.show_all()
        return menu

    def do_popup(self, event = None):
        menu = self.create_popup_menu()

        if event is not None:
            menu.popup(None, None, None, event.button, event.time)
        else:
            menu.popup(None, None,
                       lambda m: pluma.utils.menu_position_under_widget(m, self),
                       0, gtk.get_current_event_time())
            menu.select_first(False)

    def copy_clipboard(self):
        self._vte.copy_clipboard()
        self._vte.grab_focus()

    def paste_clipboard(self):
        self._vte.paste_clipboard()
        self._vte.grab_focus()

    def change_directory(self, path):
        path = path.replace('\\', '\\\\').replace('"', '\\"')
        self._vte.feed_child('cd "%s"\n' % path)
        self._vte.grab_focus()

class TerminalWindowHelper(object):
    def __init__(self, window):
        self._window = window

        self._panel = PlumaTerminal()
        self._panel.connect("populate-popup", self.on_panel_populate_popup)
        self._panel.show()

        image = gtk.Image()
        image.set_from_icon_name("utilities-terminal", gtk.ICON_SIZE_MENU)

        bottom = window.get_bottom_panel()
        bottom.add_item(self._panel, _("Terminal"), image)

    def deactivate(self):
        bottom = self._window.get_bottom_panel()
        bottom.remove_item(self._panel)

    def update_ui(self):
        pass

    def get_active_document_directory(self):
        doc = self._window.get_active_document()
        if doc is None:
            return None
        location = doc.get_location()
        if location is not None and pluma.utils.uri_has_file_scheme(location.get_uri()):
            directory = location.get_parent()
            return directory.get_path()
        return None

    def on_panel_populate_popup(self, panel, menu):
        menu.prepend(gtk.SeparatorMenuItem())
        path = self.get_active_document_directory()
        item = gtk.MenuItem(_("C_hange Directory"))
        item.connect("activate", lambda menu_item: panel.change_directory(path))
        item.set_sensitive(path is not None)
        menu.prepend(item)

class TerminalPlugin(pluma.Plugin):
    WINDOW_DATA_KEY = "TerminalPluginWindowData"

    def __init__(self):
        pluma.Plugin.__init__(self)

    def activate(self, window):
        helper = TerminalWindowHelper(window)
        window.set_data(self.WINDOW_DATA_KEY, helper)

    def deactivate(self, window):
        window.get_data(self.WINDOW_DATA_KEY).deactivate()
        window.set_data(self.WINDOW_DATA_KEY, None)

    def update_ui(self, window):
        window.get_data(self.WINDOW_DATA_KEY).update_ui()

mateconf_client = mateconf.client_get_default()
def mateconf_get_bool(key, default = False):
    val = mateconf_client.get(key)

    if val is not None and val.type == mateconf.VALUE_BOOL:
        return val.get_bool()
    else:
        return default

def mateconf_get_str(key, default = ""):
    val = mateconf_client.get(key)

    if val is not None and val.type == mateconf.VALUE_STRING:
        return val.get_string()
    else:
        return default

def mateconf_get_int(key, default = 0):
    val = mateconf_client.get(key)

    if val is not None and val.type == mateconf.VALUE_INT:
        return val.get_int()
    else:
        return default

# Let's conform to PEP8
# ex:ts=4:et:
