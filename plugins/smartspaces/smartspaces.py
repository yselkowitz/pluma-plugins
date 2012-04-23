# -*- coding: utf-8 -*-

#  smartspaces.py
#
#  Copyright (C) 2006 - Steve Frécinaux
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
import gtk

class SmartSpacesViewHelper(object):
    def __init__(self, view):
        self._view = view

        self._handlers = [
            None,
            view.connect('notify::editable', self.on_notify),
            view.connect('notify::insert-spaces-instead-of-tabs', self.on_notify)
        ]
        self.update_active()

    def deactivate(self):
        for handler in self._handlers:
            if handler is not None:
                self._view.disconnect(handler)

    def update_active(self):
        # Don't activate the feature if the buffer isn't editable or if
        # we're using tabs
        active = self._view.get_editable() and \
                 self._view.get_insert_spaces_instead_of_tabs()

        if active and self._handlers[0] is None:
            self._handlers[0] = self._view.connect('key-press-event',
                                                   self.on_key_press_event)
        elif not active and self._handlers[0] is not None:
            self._view.disconnect(self._handlers[0])
            self._handlers[0] = None

    def on_notify(self, view, pspec):
        self.update_active()

    def on_key_press_event(self, view, event):
        # Only take care of backspace and shift+backspace
        mods = gtk.accelerator_get_default_mod_mask()
        if event.keyval != gtk.keysyms.BackSpace or \
	       event.state & mods != 0 and event.state & mods != gtk.gdk.SHIFT_MASK:
            return False

        doc = view.get_buffer()
        if doc.get_has_selection():
            return False

        cur = doc.get_iter_at_mark(doc.get_insert())
        offset = cur.get_line_offset()

        if offset == 0:
            # We're at the begining of the line, so we can't obviously
            # unindent in this case
            return False

        start = cur.copy()
        prev = cur.copy()
        prev.backward_char()

        # If the previus chars are spaces, try to remove
        # them until the previus tab stop
        max_move = offset % view.get_tab_width()
        if max_move == 0:
            max_move = view.get_tab_width()

        moved = 0
        while moved < max_move and prev.get_char() == ' ':
            start.backward_char()
            moved += 1
            if not prev.backward_char():
                # we reached the start of the buffer
                break

        if moved == 0:
            # The iterator hasn't moved, it was not a space
            return False

        # Actually delete the spaces
        doc.begin_user_action()
        doc.delete(start, cur)
        doc.end_user_action()
        return True

class SmartSpacesPlugin(pluma.Plugin):
    WINDOW_DATA_KEY = "SmartSpacesPluginWindowData"
    VIEW_DATA_KEY = "SmartSpacesPluginViewData"

    def __init__(self):
        pluma.Plugin.__init__(self)

    def add_helper(self, view):
        helper = SmartSpacesViewHelper(view)
        view.set_data(self.VIEW_DATA_KEY, helper)

    def remove_helper(self, view):
        view.get_data(self.VIEW_DATA_KEY).deactivate()
        view.set_data(self.VIEW_DATA_KEY, None)

    def activate(self, window):
        for view in window.get_views():
            self.add_helper(view)

        handler_id = window.connect("tab-added",
                                    lambda w, t: self.add_helper(t.get_view()))
        window.set_data(self.WINDOW_DATA_KEY, handler_id)

    def deactivate(self, window):
        handler_id = window.get_data(self.WINDOW_DATA_KEY)
        window.disconnect(handler_id)
        window.set_data(self.WINDOW_DATA_KEY, None)

        for view in window.get_views():
            self.remove_helper(view)

    def update_ui(self, window):
        pass

# ex:ts=4:et:
