# -*- coding: utf-8 -*-
# store.py
# This file is part of pluma Session Saver Plugin
#
# Copyright (C) 2006-2007 - Steve Frécinaux <code@istique.net>
#
# pluma Session Saver Plugin is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# pluma Session Saver Plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pluma Session Saver Plugin; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301  USA

import os.path
from xml.parsers import expat
import gobject

class Session(object):
    def __init__(self, name, files = None):
        super(Session, self).__init__()
        self.name = name
        if files is None:
            files = []
        self.files = files

    def __cmp__(self, session):
        return cmp(self.name.lower(), session.name.lower())

    def add_file(self, filename):
        self.files.append(filename)

class SessionStore(gobject.GObject):
    __gsignals__ = {
        "session-added":    (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
        "session-changed":  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)),
        "session-removed":  (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_PYOBJECT,))
    }

    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = gobject.GObject.__new__(cls)
        return cls._instance

    def __init__(self):
        super(SessionStore, self).__init__()
        self._sessions = []

    def __iter__(self):
        return iter(self._sessions)

    def __getitem__(self, index):
        return self._sessions[index]

    def __getslice__(self, i, j):
        return self._sessions[i:j]

    def __len__(self):
        return len(self._sessions)

    def do_session_added(self, session):
        self._sessions.append(session)
        self._sessions.sort()

    def do_session_changed(self, session):
        index = self._sessions.index(session)
        self._sessions[index] = session

    def add(self, session):
        assert isinstance(session, Session)

        if session in self:
            self.emit('session-changed', session)
        else:
            self.emit('session-added', session)

    def do_session_removed(self, session):
        self._sessions.remove(session)

    def remove(self, session):
        assert isinstance(session, Session)
        if session in self:
            self.emit('session-removed', session)

    def index(self, session):
        return self._sessions.index(session)

class XMLSessionStore(SessionStore):
    def __init__(self):
        super(XMLSessionStore, self).__init__()
        self.filename = os.path.expanduser('~/.config/pluma/saved-sessions.xml')
        self.load()

    def _escape(self, string):
        return string.replace('&', '&amp;') \
                     .replace('<', '&lt;')  \
                     .replace('>', '&gt;')  \
                     .replace('"', '&quot;')

    def _dump_session(self, session):
        files = ''.join(['  <file path="%s"/>\n' % self._escape(filename)
                            for filename in session.files])
        session_name = self._escape(session.name)
        return '<session name="%s">\n%s</session>\n' % (session_name, files)

    def dump(self):
        dump = [self._dump_session(session) for session in self]
        return '<saved-sessions>\n%s</saved-sessions>\n' % ''.join(dump)

    def save(self):
        dirname = os.path.dirname(self.filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        fp = file(self.filename, "wb")
        fp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fp.write(self.dump())
        fp.close()

    def load(self):
        if not os.path.isfile(self.filename):
            return

        parser = expat.ParserCreate('UTF-8')
        parser.buffer_text = True
        parser.StartElementHandler = self._expat_start_handler
        parser.EndElementHandler = self._expat_end_handler

        self._current_session = None
        parser.ParseFile(open(self.filename, 'rb'))
        del self._current_session

    def _expat_start_handler(self, tag, attr):
        if tag == 'file':
            assert self._current_session is not None
            self._current_session.add_file(str(attr['path']))
        elif tag == 'session':
            assert self._current_session is None
            self._current_session = Session(attr['name'])

    def _expat_end_handler(self, tag):
        if tag == 'session':
            self.add(self._current_session)
            self._current_session = None

# ex:ts=4:et:

