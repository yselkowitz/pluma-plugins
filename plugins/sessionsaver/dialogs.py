# -*- coding: utf-8 -*-
# Copyright (c) 2007 - Steve Frécinaux <code@istique.net>
# Licence: GPL2 or later

import gobject
import pluma
import gtk
import os.path
import gettext
from store import Session

try:
    from gpdefs import *
    gettext.bindtextdomain(GETTEXT_PACKAGE, GP_LOCALEDIR)
    gtk.glade.bindtextdomain(GETTEXT_PACKAGE, GP_LOCALEDIR)
    _ = lambda s: gettext.dgettext(GETTEXT_PACKAGE, s);
except:
    _ = lambda s: s

class SessionModel(gtk.GenericTreeModel):
    OBJECT_COLUMN = 0
    NAME_COLUMN = 1
    N_COLUMNS = 2
    column_types = (gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)

    def __init__(self, store):
        super(SessionModel, self).__init__()
        self.store = store
        self.store.connect_after('session-added', self.on_session_added)
        self.store.connect('session-changed', self.on_session_changed)
        self.store.connect('session-removed', self.on_session_removed)

    def on_session_added(self, store, session):
        piter = store.index(session)
        self.row_inserted(self.on_get_path(piter), piter)

    def on_session_changed(self, store, session):
        piter = store.index(session)
        self.row_changed(self.on_get_path(piter), piter)

    def on_session_removed(self, store, session):
        piter = store.index(session)
        self.row_deleted(self.on_get_path(piter))

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY

    def on_get_n_columns(self):
        return self.N_COLUMNS

    def on_get_column_type(self, index):
        assert index < self.N_COLUMNS
        return self.column_types[index]

    def on_get_iter(self, path):
        return path[0]

    def on_get_path(self, piter):
        return (piter, )

    def on_get_value(self, piter, column):
        obj = self.store[piter]
        if column == self.OBJECT_COLUMN:
            return obj
        elif column == self.NAME_COLUMN:
            return obj.name

    def on_iter_next(self, piter):
        if piter + 1 < len(self.store):
            return piter + 1
        return None

    def on_iter_children(self, piter):
        if piter is None and len(self.store) > 0: return 0
        return None

    def on_iter_has_child(self, piter):
        return False

    def on_iter_n_children(self, piter):
        if piter is None:
            return len(self.store)
        return 0

    def on_iter_nth_child(self, piter, n):
        if piter is None and n >= 0 and n < len(self.store):
            return n
        return None

    def on_iter_parent(self, piter):
        return None

class Dialog(object):
    UI_FILE = "sessionsaver.ui"

    def __new__(cls, *args):
        if not cls.__dict__.has_key('_instance') or cls._instance is None:
            cls._instance = object.__new__(cls, *args)
        return cls._instance

    def __init__(self, main_widget, datadir, parent_window = None):
        super(Dialog, self).__init__()

        if parent_window is None:
            parent_window = pluma.app_get_default().get_active_window()
        self.parent = parent_window

        self.ui = gtk.Builder()
        self.ui.add_from_file(os.path.join(datadir, self.UI_FILE))
        self.ui.set_translation_domain(domain=GETTEXT_PACKAGE)
        self.dialog = self.ui.get_object(main_widget)
        self.dialog.connect('delete-event', self.on_delete_event)

    def __getitem__(self, item):
        return self.ui.get_object(item)

    def on_delete_event(self, dialog, event):
        dialog.hide()
        return True

    def __del__(self):
        self.__class__._instance = None

    def run(self):
        self.dialog.set_transient_for(self.parent)
        self.dialog.show()

    def destroy(self):
        self.dialog.destroy()
        self.__del__()

class SaveSessionDialog(Dialog):
    def __init__(self, window, plugin):
        super(SaveSessionDialog, self).__init__('save-session-dialog', plugin.get_data_dir(), window)
        self.plugin = plugin

        model = SessionModel(plugin.sessions)

        combobox = self['session-name']
        combobox.set_model(model)
        combobox.set_text_column(1)

        self.dialog.connect('response', self.on_response)

    def on_response(self, dialog, response_id):
        if response_id == gtk.RESPONSE_OK:
            files = [doc.get_uri()
                        for doc in self.parent.get_documents()
                        if doc.get_uri() is not None]
            name = self['session-name'].child.get_text()
            self.plugin.sessions.add(Session(name, files))
            self.plugin.sessions.save()
        self.plugin.update_session_menu()
        self.destroy()

class SessionManagerDialog(Dialog):
    def __init__(self, plugin):
        super(SessionManagerDialog, self).__init__('session-manager-dialog', plugin.get_data_dir())
        self.plugin = plugin

        model = SessionModel(plugin.sessions)

        self.view = self['session-view']
        self.view.set_model(model)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("Session Name"), renderer, text = model.NAME_COLUMN)
        self.view.append_column(column)

        handlers = {
            'on_close_button_clicked': self.on_close_button_clicked,
            'on_open_button_clicked': self.on_open_button_clicked,
            'on_delete_button_clicked': self.on_delete_button_clicked
        }
        self.ui.connect_signals(handlers)

    def on_delete_event(self, dialog, event):
        dialog.hide()
        self.plugin.sessions.save()
        return True

    def get_current_session(self):
        selected = self.view.get_selection().get_selected()
        if selected is None:
            return None
        model, selected = selected
        return model.get_value(selected, SessionModel.OBJECT_COLUMN)

    def on_open_button_clicked(self, button):
        session = self.get_current_session()
        if session is not None:
            self.plugin.load_session(session, self.parent)

    def on_delete_button_clicked(self, button):
        session = self.get_current_session()
        self.plugin.sessions.remove(session)
        self.plugin.update_session_menu()

    def on_close_button_clicked(self, button):
        self.plugin.sessions.save()
        self.destroy()

# ex:ts=4:et:

