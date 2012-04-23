# -*- coding: utf-8 -*-
#
#  multiedit.py - Multi Edit
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
from windowhelper import WindowHelper

class MultiEditPlugin(pluma.Plugin):
    def __init__(self):
        pluma.Plugin.__init__(self)
        self._instances = {}

    def activate(self, window):
        self._instances[window] = WindowHelper(self, window)

    def deactivate(self, window):
        if window in self._instances:
            self._instances[window].deactivate()
            del self._instances[window]

    def update_ui(self, window):
        if window in self._instances:
            self._instances[window].update_ui()

# ex:ts=4:et:
