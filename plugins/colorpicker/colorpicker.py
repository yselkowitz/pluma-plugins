# -*- coding: utf-8 -*-
#  Color picker plugin
#  This file is part of pluma-plugins
#
#  Copyright (C) 2006 Jesse van den Kieboom
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

import pluma, gtk
import gettext
import re
from gpdefs import *

try:
    gettext.bindtextdomain(GETTEXT_PACKAGE, GP_LOCALEDIR)
    _ = lambda s: gettext.dgettext(GETTEXT_PACKAGE, s);
except:
    _ = lambda s: s

ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="ColorPicker" action="ColorPicker"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class ColorPickerPluginInstance:
    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin
        self._activate_id = 0

        self.insert_menu()
        self.update()

        self._activate_id = self._window.connect('focus-in-event', \
                self.on_window_activate)

    def stop(self):
        self.remove_menu()

        if self._activate_id:
            self._window.handler_disconnect(self._activate_id)

        self._window = None
        self._plugin = None
        self._action_group = None
        self._activate_id = 0

    def insert_menu(self):
        manager = self._window.get_ui_manager()

        self._action_group = gtk.ActionGroup("PlumaColorPickerPluginActions")
        self._action_group.add_actions( \
                [("ColorPicker", None, _("Pick _Color..."), None, \
                _("Pick a color from a dialog"), \
                lambda a: self._plugin.on_color_picker_activate(self._window))])

        manager.insert_action_group(self._action_group, -1)
        self._ui_id = manager.add_ui_from_string(ui_str)

    def remove_menu(self):
        manager = self._window.get_ui_manager()

        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()

    def update(self):
        tab = self._window.get_active_tab()
        self._action_group.set_sensitive(tab != None)

        if not tab and self._plugin._dialog and \
                self._plugin._dialog.get_transient_for() == self._window:
            self._plugin._dialog.response(gtk.RESPONSE_CLOSE)

    def on_window_activate(self, window, event):
        self._plugin.dialog_transient_for(window)

class ColorPickerPlugin(pluma.Plugin):
    DATA_TAG = "ColorPickerPluginInstance"

    def __init__(self):
        pluma.Plugin.__init__(self)
        self._dialog = None

    def get_instance(self, window):
        return window.get_data(self.DATA_TAG)

    def set_instance(self, window, instance):
        window.set_data(self.DATA_TAG, instance)

    def activate(self, window):
        self.set_instance(window, ColorPickerPluginInstance(self, window))

    def deactivate(self, window):
        self.get_instance(window).stop()
        self.set_instance(window, None)

    def update_ui(self, window):
        self.get_instance(window).update()

    def skip_hex(self, buf, iter, next_char):
        while True:
            char = iter.get_char()

            if not char:
                return

            if char.lower() not in \
                    ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                    'a', 'b', 'c', 'd', 'e', 'f'):
                return

            if not next_char(iter):
                return

    def get_color_position(self, buf):
        bounds = buf.get_selection_bounds()

        if not bounds or bounds[0].equal(bounds[1]):
            # No selection, find color in the current cursor position
            start = buf.get_iter_at_mark(buf.get_insert())

            end = start.copy()
            start.backward_char()

            self.skip_hex(buf, start, lambda iter: iter.backward_char())
            self.skip_hex(buf, end, lambda iter: iter.forward_char())
        else:
            start, end = bounds

        text = buf.get_text(start, end)

        if not re.match('#?[0-9a-zA-Z]+', text):
            return None

        if text[0] != '#':
            start.backward_char()

            if start.get_char() != '#':
                return None

        return start, end

    def insert_color(self, text):
        window = pluma.app_get_default().get_active_window()
        view = window.get_active_view()

        if not view or not view.get_editable():
            return

        doc = view.get_buffer()

        if not doc:
            return

        doc.begin_user_action()

        # Get the color
        bounds = self.get_color_position(doc)

        if not bounds:
            doc.delete_selection(False, True)
        else:
            doc.delete(bounds[0], bounds[1])

        doc.insert_at_cursor('#' + text)

        doc.end_user_action()

    def scale_color_component(self, component):
        return min(max(int(round(component * 255. / 65535.)), 0), 255)

    def scale_color(self, color):
        color.red = self.scale_color_component(color.red)
        color.green = self.scale_color_component(color.green)
        color.blue = self.scale_color_component(color.blue)

    def get_current_color(self):
        window = pluma.app_get_default().get_active_window()
        doc = window.get_active_document()

        if not doc:
            return None

        bounds = self.get_color_position(doc)

        if bounds:
            return doc.get_text(bounds[0], bounds[1])
        else:
            return None

    def dialog_transient_for(self, window):
        if self._dialog:
            self._dialog.set_transient_for(window)

    # Signal handlers

    def on_color_picker_activate(self, window):
        if not self._dialog:
            self._dialog = gtk.ColorSelectionDialog(_('Pick Color'))
            self._dialog.colorsel.set_has_palette(True)

            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_SELECT_COLOR, gtk.ICON_SIZE_BUTTON)

            self._dialog.ok_button.set_label(_('_Insert'))
            self._dialog.ok_button.set_image(image)

            self._dialog.cancel_button.set_use_stock(True)
            self._dialog.cancel_button.set_label(gtk.STOCK_CLOSE)

            self._dialog.connect('response', self.on_dialog_response)

        color = self.get_current_color()

        if color:
            try:
                color = gtk.gdk.color_parse(color)
            except ValueError:
                color = None

            if color:
                self._dialog.colorsel.set_current_color(color)

        self._dialog.set_transient_for(window)
        self._dialog.present()

    def on_dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_OK:
            color = dialog.colorsel.get_current_color()

            self.scale_color(color)

            self.insert_color("%02x%02x%02x" % (color.red, \
                    color.green, color.blue))
        else:
            self._dialog.destroy()
            self._dialog = None

# ex:ts=4:et:
