# -*- coding: utf-8 -*-
#  Join lines plugin
#  This file is part of pluma
#
#  Copyright (C) 2006-2007 Steve Frécinaux, André Homeyer
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

try:
    from gpdefs import *
    gettext.bindtextdomain(GETTEXT_PACKAGE, GP_LOCALEDIR)
    _ = lambda s: gettext.dgettext(GETTEXT_PACKAGE, s)
except:
    _ = lambda s: s


ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="EditMenu" action="Edit">
      <placeholder name="EditOps_5">
        <menuitem name="JoinLines" action="JoinLines"/>
        <menuitem name="SplitLines" action="SplitLines"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class JoinLinesPlugin(pluma.Plugin):
    def __init__(self):
        pluma.Plugin.__init__(self)

    def activate(self, window):
        manager = window.get_ui_manager()
        data = dict()

        data["action_group"] = gtk.ActionGroup("PlumaJoinLinesPluginActions")
        data["action_group"].add_actions(
            [("JoinLines", None, _("_Join Lines"), "<Ctrl>J",
              _("Join the selected lines"),
              lambda a, w: join_lines(w)),
             ("SplitLines", None, _('_Split Lines'), "<Shift><Ctrl>J",
              _("Split the selected lines"),
              lambda a, w: split_lines(w))],
            window)

        manager.insert_action_group(data["action_group"], -1)
        data["ui_id"] = manager.add_ui_from_string(ui_str)

        window.set_data("JoinLinesPluginInfo", data)
        update_sensitivity(window)

    def deactivate(self, window):
        data = window.get_data("JoinLinesPluginInfo")
        manager = window.get_ui_manager()
        manager.remove_ui(data["ui_id"])
        manager.remove_action_group(data["action_group"])
        manager.ensure_update()
        window.set_data("JoinLinesPluginInfo", None)

    def update_ui(self, window):
        update_sensitivity(window)

def update_sensitivity(window):
    data = window.get_data("JoinLinesPluginInfo")
    view = window.get_active_view()
    data["action_group"].set_sensitive(view is not None and \
                                       view.get_editable())

def join_lines(window):
    document = window.get_active_document()
    if document is None:
        return

    document.begin_user_action()

    # If there is a selection use it, otherwise join the
    # next line
    try:
        start, end = document.get_selection_bounds()
    except ValueError:
        start = document.get_iter_at_mark(document.get_insert())
        end = start.copy()
        end.forward_line()

    end_mark = document.create_mark(None, end)

    if not start.ends_line():
        start.forward_to_line_end()

    while document.get_iter_at_mark(end_mark).compare(start) == 1:
        end = start.copy()
        while end.get_char() in ('\r', '\n', ' ', '\t'):
            end.forward_char()
        document.delete(start, end)

        document.insert(start, ' ')
        start.forward_to_line_end()

    document.delete_mark(end_mark)
    document.end_user_action()

def split_lines(window):
    view = window.get_active_view()
    if view is None:
        return

    document = view.get_buffer()

    width = view.get_right_margin_position()
    tabwidth = view.get_tab_width()

    document.begin_user_action()

    try:
        # get selection bounds
        start, end = document.get_selection_bounds()

        # measure indent until selection start
        indent_iter = start.copy()
        indent_iter.set_line_offset(0)
        indent = ''
        while indent_iter.get_offset() != start.get_offset():
            if indent_iter.get_char() == '\t':
                indent = indent + '\t'
            else:
                indent = indent + ' '
            indent_iter.forward_char()
    except ValueError:
        # select from start to line end
        start = document.get_iter_at_mark(document.get_insert())
        start.set_line_offset(0)
        end = start.copy()
        if not end.ends_line():
            end.forward_to_line_end()

        # measure indent of line
        indent_iter = start.copy()
        indent = ''
        while indent_iter.get_char() in (' ', '\t'):
            indent = indent + indent_iter.get_char()
            indent_iter.forward_char()

    end_mark = document.create_mark(None, end)

    # ignore first word
    previous_word_end = start.copy()
    forward_to_word_start(previous_word_end)
    forward_to_word_end(previous_word_end)

    while 1:
        current_word_start = previous_word_end.copy()
        forward_to_word_start(current_word_start)

        current_word_end = current_word_start.copy()
        forward_to_word_end(current_word_end)

        if ord(current_word_end.get_char()) and \
           document.get_iter_at_mark(end_mark).compare(current_word_end) >= 0:

            word_length = current_word_end.get_offset() - \
                          current_word_start.get_offset()

            document.delete(previous_word_end, current_word_start)

            line_offset = get_line_offset(current_word_start, tabwidth) + word_length
            if line_offset > width - 1:
                document.insert(current_word_start, '\n' + indent)
            else:
                document.insert(current_word_start, ' ')

            previous_word_end = current_word_start.copy()
            previous_word_end.forward_chars(word_length)
        else:
            break

    document.delete_mark(end_mark)
    document.end_user_action()

def get_line_offset(text_iter, tabwidth):
    offset_iter = text_iter.copy()
    offset_iter.set_line_offset(0)

    line_offset = 0
    while offset_iter.get_offset() < text_iter.get_offset():
        char = offset_iter.get_char()
        if char == '\t':
            line_offset += tabwidth
        else:
            line_offset += 1
        offset_iter.forward_char()

    return line_offset

def forward_to_word_start(text_iter):
    char = text_iter.get_char()
    while ord(char) and (char in (' ', '\t', '\n', '\r')):
        text_iter.forward_char()
        char = text_iter.get_char()

def forward_to_word_end(text_iter):
    char = text_iter.get_char()
    while ord(char) and (not (char in (' ', '\t', '\n', '\r'))):
        text_iter.forward_char()
        char = text_iter.get_char()

# ex:ts=4:et:
