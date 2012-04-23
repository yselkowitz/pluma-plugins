# -*- coding: utf-8 -*-   

#  synctex.py - Synctex support with Pluma and Atril.
#  
#  Copyright (C) 2010 - José Aliste <jose.aliste@gmail.com>
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

import gtk, pluma, gio , gtk.gdk as gdk
from gettext import gettext as _
from atril_dbus import AtrilWindowProxy
import dbus.mainloop.glib
import logging

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <separator/>
        <menuitem name="Synctex" action="SynctexForwardSearch"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

VIEW_DATA_KEY = "SynctexPluginViewData"
WINDOW_DATA_KEY = "SynctexPluginWindowData"

_logger = logging.getLogger("SynctexPlugin")

def apply_style (style, tag):
    import pango
    def apply_style_prop(tag, style, prop):
        if style.get_property(prop + "-set"):
            tag.set_property(prop, style.get_property(prop))
        else:
            tag.set_property(prop, None)
    def apply_style_prop_bool(tag, style, prop, whentrue, whenfalse):
        if style.get_property(prop + "-set"):
            prop_value = whentrue if style.get_property(prop) else whenfalse
            tag.set_property(prop, prop_value)

    apply_style_prop(tag, style, "foreground")
    apply_style_prop(tag, style, "background")

    apply_style_prop_bool(tag, style, "bold", pango.WEIGHT_BOLD, pango.WEIGHT_NORMAL)
    apply_style_prop_bool(tag, style, "italic", pango.STYLE_ITALIC, pango.STYLE_NORMAL)
    apply_style_prop_bool(tag, style, "underline", pango.UNDERLINE_SINGLE,
                                pango.UNDERLINE_NONE)
    apply_style_prop(tag, style, "strikethrough")

def parse_modeline(line):
    index = line.find("mainfile:")
    if line.startswith("%") and index > 0:
        # Parse the modeline.
        return line[index + len("mainfile:"):].strip()
    return None

class SynctexViewHelper:
    def __init__(self, view, window, tab, plugin):
        self._view = view
        self._window = window
        self._tab = tab
        self._plugin = plugin
        self._doc = view.get_buffer()
        self.window_proxy = None
        self._handlers = [
            self._doc.connect('saved', self.on_saved_or_loaded),
            self._doc.connect('loaded', self.on_saved_or_loaded)
        ]

        self._highlight_tag = self._doc.create_tag()
        self.active = False
        self.last_iters = None
        self.gfile = None
        self.update_location()

    def on_notify_style_scheme(self, doc, param_object):
        apply_style (doc.get_style_scheme().get_style('search-match'), self._highlight_tag)

    def on_button_release(self, view, event):
        if event.button == 1 and event.state & gdk.CONTROL_MASK:
            self.sync_view()

    def on_saved_or_loaded(self, doc, data):
        self.update_location()

    def get_output_file(self):
        file_output = None
        line_count = self._doc.get_line_count()
        for i in range(min(3,line_count)) + range(max(0,line_count - 3), line_count):
            start = self._doc.get_iter_at_line(i)
            end = start.copy()
            end.forward_to_line_end()
            file_output = parse_modeline(self._doc.get_text(start, end, False))
            if file_output is not None:
                break
        return file_output

    def on_key_press(self, a, b):
        self._unhighlight()
    def on_cursor_moved(self, cur):
        self._unhighlight()

    def deactivate(self):
        self._unhighlight()
        for h in self._handlers:
            self._doc.disconnect(h)
        del self._highlight_tag

    def update_location(self):
        import os

        gfile = self._doc.get_location()
        if gfile is None:
            return
        if self.gfile is None or gfile.get_uri() != self.gfile.get_uri():
            self._plugin.view_dict[gfile.get_uri()] = self
            self.gfile = gfile

        modeline_output_file = self.get_output_file()

        if modeline_output_file is not None:
            filename = modeline_output_file
        else:
            filename = self.gfile.get_basename()

        out_path = self.gfile.get_parent().get_child(filename).get_path()
        out_path = os.path.splitext(out_path)
        out_gfile = gio.File(out_path[0] + ".pdf")
        if out_gfile.query_exists():
            self.out_gfile = out_gfile
        else:
            self.out_gfile = None

        self.update_active()

    def _highlight(self):
        iter = self._doc.get_iter_at_mark(self._doc.get_insert())
        end_iter = iter.copy()
        end_iter.forward_to_line_end()
        self._doc.apply_tag(self._highlight_tag, iter, end_iter)
        self.last_iters = [iter, end_iter];

    def _unhighlight(self):
        if self.last_iters is not None:
            self._doc.remove_tag(self._highlight_tag,
                                 self.last_iters[0], self.last_iters[1])
        self.last_iters = None

    def goto_line (self, line):
        self._doc.goto_line(line) 
        self._view.scroll_to_cursor()
        self._window.set_active_tab(self._tab)
        self._highlight()
        self._window.present()

    def goto_line_after_load(self, a, line):
        self.goto_line(line)
        self._doc.disconnect(self._goto_handler)

    def sync_view(self):
        if self.active:
            cursor_iter =  self._doc.get_iter_at_mark(self._doc.get_insert())
            line = cursor_iter.get_line() + 1
            col = cursor_iter.get_line_offset()
            self.window_proxy.SyncView(self.gfile.get_path(), (line, col))

    def update_active(self):
        # Activate the plugin only if the doc is a LaTeX file.
        lang = self._doc.get_language() 
        self.active = (lang is not None and lang.get_id() == 'latex' and
                        self.out_gfile is not None)

        if self.active and self.window_proxy is None:
            self._doc_active_handlers = [
                        self._doc.connect('cursor-moved', self.on_cursor_moved),
                        self._doc.connect('notify::style-scheme', self.on_notify_style_scheme)]
            self._view_active_handlers = [
                        self._view.connect('key-press-event', self.on_key_press),
                        self._view.connect('button-release-event', self.on_button_release)]


            style = self._doc.get_style_scheme().get_style('search-match')
            apply_style(style, self._highlight_tag)
            self._window.get_data(WINDOW_DATA_KEY)._action_group.set_sensitive(True)
            self.window_proxy = self._plugin.ref_atril_proxy(self.out_gfile, self._window)

        elif not self.active and self.window_proxy is not None:
            #destroy the atril window proxy.
            for handler in self._doc_active_handlers:
                self._doc.disconnect(handler)
            for handler in self._view_active_handlers:
                self._view.disconnect(handler)

            self._window.get_data(WINDOW_DATA_KEY)._action_group.get_sensitive(False)
            self._plugin.unref_atril_proxy(self.out_gfile)
            self.window_proxy = None


class SynctexWindowHelper:
    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin

        self._insert_menu()

        for view in window.get_views():
            self.add_helper(view, window, view.get_parent().get_parent())

        self.handlers = [
            window.connect("tab-added", lambda w, t: self.add_helper(t.get_view(),w, t)),
            window.connect("tab-removed", lambda w, t: self.remove_helper(t.get_view())),
            window.connect("active-tab-changed", self.on_active_tab_changed)
        ]
    def on_active_tab_changed(self, window,  tab):
        view_helper = tab.get_view().get_data(VIEW_DATA_KEY)
        if view_helper is None:
            active = False
        else:
            active = view_helper.active 
        self._action_group.set_sensitive(active)


    def add_helper(self, view, window, tab):
        helper = SynctexViewHelper(view, window, tab, self._plugin)
        uri = view.get_buffer().get_uri()
        if uri is not None:
            self._plugin.view_dict[uri] = helper
        view.set_data (VIEW_DATA_KEY, helper)

    def remove_helper(self, view):
        helper = view.get_data(VIEW_DATA_KEY)
        if helper.gfile is not None:
            del self._plugin.view_dict[helper.gfile.get_uri()]
        helper.deactivate()
        view.set_data(VIEW_DATA_KEY, None)

    def __del__(self):
        self._window = None
        self._plugin = None

    def deactivate(self):
        for h in self.handlers:
            self._window.disconnect(h)
        for view in self._window.get_views():
            self.remove_helper(view)
        self._remove_menu()

    def _remove_menu(self):
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()

    def _insert_menu(self):
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()

        # Create a new action group
        self._action_group = gtk.ActionGroup("SynctexPluginActions")
        self._action_group.add_actions([("SynctexForwardSearch", None,
                                        _("Forward Search"), "<Ctrl><Alt>F",
                                        _("Forward Search"), self.forward_search_cb)])

        # Insert the action group
        manager.insert_action_group(self._action_group, -1)

        # Merge the UI
        self._ui_id = manager.add_ui_from_string(ui_str)

    def forward_search_cb(self, action):
        self._window.get_active_view().get_data(VIEW_DATA_KEY).sync_view()

class SynctexPlugin(pluma.Plugin):

    def __init__(self):
        pluma.Plugin.__init__(self)
        self.view_dict = {}
        self._proxy_dict = {}

    def activate(self, window):
        helper = SynctexWindowHelper(self, window)
        window.set_data(WINDOW_DATA_KEY, helper)

    def deactivate(self, window):
        window.get_data(WINDOW_DATA_KEY).deactivate()
        window.set_data(WINDOW_DATA_KEY, None)

    def source_view_handler(self, out_gfile, input_file, source_link):
        uri_input = out_gfile.get_parent().get_child(input_file).get_uri()
        
        if uri_input not in self.view_dict:
            window = self._proxy_dict[out_gfile.get_uri()][2]
            tab = window.create_tab_from_uri(uri_input,
                                                 None, source_link[0] - 1, False, True)
            helper =  tab.get_view().get_data(VIEW_DATA_KEY)
            helper._goto_handler = tab.get_document().connect_object("loaded", 
                                                SynctexViewHelper.goto_line_after_load, 
                                                helper, source_link[0] - 1) 
        else:
            self.view_dict[uri_input].goto_line(source_link[0] - 1)

    def ref_atril_proxy(self, gfile, window):
        uri = gfile.get_uri()
        proxy = None
        if uri not in self._proxy_dict:
            proxy = AtrilWindowProxy (uri, True, _logger)
            self._proxy_dict[uri] = [1, proxy, window]
            proxy.set_source_handler (lambda i, s: self.source_view_handler(gio.File(uri), i, s))
        else:
            self._proxy_dict[uri][0]+=1
            proxy = self._proxy_dict[uri][1]
        return proxy

    def unref_atril_proxy(self, gfile):
        uri = gfile.get_uri()
        if uri in self._proxy_dict:
            self._proxy_dict[uri][0]-=1
            if self._proxy_dict[uri][0] == 0:
                del self._proxy_dict[uri]
     
    def update_ui(self, window):
        pass
# ex:ts=4:et:
