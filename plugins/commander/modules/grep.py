# -*- coding: utf-8 -*-
#
#  grep.py - grep commander module
#
#  Copyright (C) 2010 - Jesse van den Kieboom
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

import commander.commands as commands
import commander.commands.completion
import commander.commands.result
import commander.commands.exceptions

import re

__commander_module__ = True
HideTagName = 'CommanderModuleGrepHideTag'
ZoomOutTagName = 'CommanderModuleGrepZoomOutTag'
HighlightTagName = 'CommanderModuleGrepHighlightTag'

def _get_tag(buf, name, callback=None, **args):
    table = buf.get_tag_table()
    tag = table.lookup(name)

    if tag is None:
        if not callback is None:
            args.update(callback(buf))

        tag = buf.create_tag(name, **args)

    return tag

def _get_invisible_tag(buf):
    return _get_tag(buf, HideTagName, invisible=True, invisible_set=True)

def _get_zoomout_tag(buf):
    return _get_tag(buf, ZoomOutTagName, size_points=4)

def _create_highlight_tag(buf):
    scheme = buf.get_style_scheme()
    style = scheme.get_style('search-match')

    if style is None:
        return {'background': '#FFFF78', 'background_set': True, 'foreground_set': False}

    ret = {}

    if style.props.foreground_set:
        ret.update({'foreground_set': True, 'foreground': style.props.foreground})

    if style.props.background_set:
        ret.update({'background_set': True, 'background': style.props.background})

    return ret

def _get_highlight_tag(buf):
    return _get_tag(buf, HighlightTagName, _create_highlight_tag)

def _grep_action_hide(view, start, end):
    # Apply tag that makes line invisible
    buf = view.get_buffer()
    tag = _get_invisible_tag(buf)

    buf.apply_tag(tag, start, end)

def _grep_action_show(view, start, end):
    buf = view.get_buffer()
    tag = _get_invisible_tag(buf)

    buf.remove_tag(tag, start, end)

def _grep_action_zoomin(view, start, end):
    buf = view.get_buffer()
    tag = _get_zoomout_tag(buf)

    buf.remove_tag(tag, start, end)

def _grep_action_zoomout(view, start, end):
    buf = view.get_buffer()
    tag = _get_zoomout_tag(buf)

    buf.apply_tag(tag, start, end)

def _highlight(view, start, end, matches):
    buf = view.get_buffer()
    tag = _get_highlight_tag(buf)

    for match in matches:
        st = start.copy()
        ed = start.copy()

        st.forward_chars(match.start(0))
        ed.forward_chars(match.end(0))

        buf.apply_tag(tag, st, ed)

def _unhighlight(view, start, end, matches):
    buf = view.get_buffer()
    tag = _get_highlight_tag(buf)

    for match in matches:
        st = start.copy()
        ed = start.copy()

        st.forward_chars(match.start(0))
        ed.forward_chars(match.end(0))

        buf.remove_tag(tag, st, ed)

def _grep(view, regex, match_action, non_match_action):
    buf = view.get_buffer()
    start = buf.get_start_iter()

    try:
        reg = re.compile(regex)
    except Exception, e:
        raise commands.exceptions.Execute('Invalid regular expression: ' + str(e))

    while True:
        end = start.copy()

        if not end.forward_line():
            end.forward_to_line_end()

        text = start.get_text(end)
        piter = list(reg.finditer(text))

        if not piter:
            _unhighlight(view, start, end, piter)
            non_match_action(view, start, end)
        else:
            _highlight(view, start, end, piter)
            match_action(view, start, end)

        if not start.forward_line():
            break

def __default__(view, argstr):
    """Hide non-matching lines in document: grep &lt;regex&gt;

Matches a regular expression on each line and hides all text that does not
match. For the revere (hiding matches) use grep.hide"""
    yield _grep(view, argstr, _grep_action_show, _grep_action_hide)

def hide(view, argstr):
    """Hide matching lines in document: grep.hide &lt;regex&gt;

Matches a regular expression on each line and hides all matches. For
the reverse (hiding lines that do not match) use grep.show"""
    yield _grep(view, argstr, _grep_action_hide, _grep_action_show)

def zoomin(view, argstr):
    """Zoom in on matching lines in document: grep.zoomin &lt;regex&gt;

Matches a regular expression on each line and magnifies all matching lines
with respect to the non-matching lines. For the reverse, use grep.zoomout"""
    yield _grep(view, argstr, _grep_action_zoomin, _grep_action_zoomout)

def zoomout(view, argstr):
    """Zoom out on matching lines in document: grep.zoomout &lt;regex&gt;

Matches a regular expression on each line and minifies all matching lines
with respect to the non-matching lines. For the reverse, use grep.zoomin"""
    yield _grep(view, argstr, _grep_action_zoomout, _grep_action_zoomin)

def clear(view):
    """Clear all grep commands: grep.clear

Clear the actions done by all grep commands."""
    buf = view.get_buffer()

    buf.remove_tag(_get_highlight_tag(buf), buf.get_start_iter(), buf.get_end_iter())
    buf.remove_tag(_get_invisible_tag(buf), buf.get_start_iter(), buf.get_end_iter())
    buf.remove_tag(_get_zoomout_tag(buf), buf.get_start_iter(), buf.get_end_iter())

locals()['show'] = __default__
locals()['zoom'] = zoomin

# vi:ts=4:et
