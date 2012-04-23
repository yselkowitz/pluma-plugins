# -*- coding: utf-8 -*-
#
#  windowhelper.py - Multi Edit
#
#  Copyright (C) 2009 - Jesse van den Kieboom
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

import pluma
from documenthelper import DocumentHelper
from signals import Signals
import constants
import gtk

from gpdefs import *

try:
    gettext.bindtextdomain(GETTEXT_PACKAGE, GP_LOCALEDIR)
    _ = lambda s: gettext.dgettext(GETTEXT_PACKAGE, s);
except:
    _ = lambda s: s

ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="EditMenu" action="Edit">
      <placeholder name="EditOps_5">
        <menuitem name="MultiEditMode" action="MultiEditModeAction"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class WindowHelper(Signals):
    def __init__(self, plugin, window):
        Signals.__init__(self)

        self._window = window
        self._plugin = plugin

        # Insert document helpers
        for view in window.get_views():
            self.add_document_helper(view)

        self.connect_signal(window, 'tab-added', self.on_tab_added)
        self.connect_signal(window, 'tab-removed', self.on_tab_removed)
        self.connect_signal(window, 'active-tab-changed', self.on_active_tab_changed)

        self.install_ui()

    def install_ui(self):
        manager = self._window.get_ui_manager()

        self._action_group = gtk.ActionGroup("PlumaMultiEditPluginActions")
        self._action_group.add_toggle_actions(
            [('MultiEditModeAction', None, _('Multi Edit Mode'), '<Ctrl><Shift>C', _('Start multi edit mode'), self.on_multi_edit_mode)])

        manager.insert_action_group(self._action_group, -1)
        self._merge_id = manager.add_ui_from_string(ui_str)

    def uninstall_ui(self):
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._merge_id)
        manager.remove_action_group(self._action_group)

        manager.ensure_update()

    def deactivate(self):
        # Remove document helpers
        for view in self._window.get_views():
            self.remove_document_helper(view)

        self.disconnect_signals(self._window)
        self.uninstall_ui()

        self._window = None
        self._plugin = None

    def update_ui(self):
        pass

    def add_document_helper(self, view):
        if view.get_data(constants.DOCUMENT_HELPER_KEY) != None:
            return

        helper = DocumentHelper(view)
        helper.set_toggle_callback(self.on_multi_edit_toggled, helper)

    def remove_document_helper(self, view):
        helper = view.get_data(constants.DOCUMENT_HELPER_KEY)

        if helper != None:
            helper.stop()

    def get_action(self):
        return self._action_group.get_action('MultiEditModeAction')

    def on_multi_edit_toggled(self, helper):
        if helper.get_view() == self._window.get_active_view():
            self.get_action().set_active(helper.enabled())

    def on_tab_added(self, window, tab):
        self.add_document_helper(tab.get_view())

    def on_tab_removed(self, window, tab):
        self.remove_document_helper(tab.get_view())

    def on_active_tab_changed(self, window, tab):
        view = tab.get_view()
        helper = view.get_data(constants.DOCUMENT_HELPER_KEY)

        self.get_action().set_active(helper != None and helper.enabled())

    def on_multi_edit_mode(self, action):
        view = self._window.get_active_view()
        helper = view.get_data(constants.DOCUMENT_HELPER_KEY)

        if helper != None:
            helper.toggle_multi_edit(self.get_action().get_active())

# ex:ts=4:et:
