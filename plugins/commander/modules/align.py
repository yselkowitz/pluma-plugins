import commander.commands as commands
import commander.commands.completion
import commander.commands.result
import commander.commands.exceptions

import re

__commander_module__ = True

class Line:
	def __init__(self, line, reg, tabwidth):
		self.tabwidth = tabwidth
		self.line = line
		self.matches = list(reg.finditer(line))

		if not self.matches:
			self.newline = str(line)
		else:
			self.newline = line[0:self.matches[0].start(0)]

	def matches_len(self):
		return len(self.matches)

	def new_len(self, extra=''):
		return len((self.newline + extra).expandtabs(self.tabwidth))

	def match(self, idx):
		if idx >= self.matches_len():
			return None

		return self.matches[idx]

	def append(self, idx, num, group, add_ws_group):
		m = self.match(idx)

		if m == None:
			return

		if len(m.groups()) <= group - 1:
			gidx = 0
		else:
			gidx = group

		if len(m.groups()) <= add_ws_group - 1:
			wsidx = 0
		else:
			wsidx = add_ws_group

		if wsidx > gidx:
			wsidx = gidx

		# First append leading match
		wsg = m.group(wsidx)
		numln = len(wsg) - len(wsg.lstrip())

		self.newline += self.line[m.start(0):m.start(wsidx)]

		# Then do the indent until gidx is aligned with num
		bridge = self.line[m.start(wsidx) + numln:m.start(gidx)]

		if not '\t' in bridge:
			bridge = (' ' * (num - self.new_len(bridge))) + bridge
		else:
			while self.new_len(bridge) < num:
				bridge = ' ' + bridge

		self.newline += bridge

		# Then append the rest of the match
		mnext = self.match(idx + 1)

		if mnext == None:
			endidx = None
		else:
			endidx = mnext.start(0)

		self.newline += self.line[m.start(gidx):endidx]

	def __str__(self):
		return self.newline

def __default__(view):
	"""Align selected text in columns: align

Align the selected text in columns separated by white space (spaces and tabs)"""
	yield regex(view, '\s+')

def _find_max_align(lines, idx, group, add_ws_group):
	num = 0
	spaces = re.compile('^\s*')

	# We will align on 'group', by adding spaces to 'add_ws_group'
	for line in lines:
		m = line.match(idx)

		if m != None:
			if len(m.groups()) <= group - 1:
				gidx = 0
			else:
				gidx = group

			if len(m.groups()) <= add_ws_group - 1:
				wsidx = 0
			else:
				wsidx = add_ws_group

			if wsidx > gidx:
				wsidx = gidx

			wsg = m.group(wsidx)

			numln = len(wsg) - len(wsg.lstrip())

			# until the start
			extra = line.line[m.start(0):m.start(wsidx)]
			extra += line.line[m.start(wsidx) + numln:m.start(gidx)]

			# Measure where to align it
			l = line.new_len(extra)
		else:
			l = line.new_len()

		if l > num:
			num = l

	return num

def _regex(view, reg, group, additional_ws, add_ws_group, flags=0):
	buf = view.get_buffer()

	bounds = buf.get_selection_bounds()

	if not bounds or (bounds[1].get_line() - bounds[0].get_line() == 0):
		raise commander.commands.exceptions.Execute('You need to select a number of lines to align')

	if reg == None:
		reg, words, modifier = (yield commander.commands.result.Prompt('Regex:'))

	try:
		reg = re.compile(reg, flags)
	except Exception, e:
		raise commander.commands.exceptions.Execute('Failed to compile regular expression: %s' % (e,))

	if group == None:
		group, words, modifier = (yield commander.commands.result.Prompt('Group (1):'))

	try:
		group = int(group)
	except:
		group = 1

	if additional_ws == None:
		additional_ws, words, modifier = (yield commander.commands.result.Prompt('Additional Whitespace (0):'))

	try:
		additional_ws = int(additional_ws)
	except:
		additional_ws = 0

	if add_ws_group == None:
		add_ws_group, words, modifier = (yield commander.commands.result.Prompt('Group (1):'))

	try:
		add_ws_group = int(add_ws_group)
	except:
		add_ws_group = -1

	if add_ws_group < 0:
		add_ws_group = group

	start, end = bounds

	if not start.starts_line():
		start.set_line_offset(0)

	if not end.ends_line():
		end.forward_to_line_end()

	lines = start.get_text(end).splitlines()
	newlines = []
	num = 0
	tabwidth = view.get_tab_width()

	for line in lines:
		ln = Line(line, reg, tabwidth)
		newlines.append(ln)

		if len(ln.matches) > num:
			num = len(ln.matches)

	for i in range(num):
		al = _find_max_align(newlines, i, group, add_ws_group)

		for line in newlines:
			line.append(i, al + additional_ws, group, add_ws_group)

	# Replace lines
	aligned = '\n'.join([str(x) for x in newlines])

	buf.begin_user_action()
	buf.delete(bounds[0], bounds[1])
	buf.insert(bounds[1], aligned)
	buf.end_user_action()

	yield commander.commands.result.DONE

def regex(view, reg=None, group=1, additional_ws=1, add_ws_group=-1):
	"""Align selected in columns using a regular expression: align.regex [&lt;regex&gt;] [&lt;group&gt;] [&lt;ws&gt;]

Align the selected text in columns separated by the specified regular expression.
The optional group argument specifies on which group in the regular expression
the text should be aligned. Additional whitespace will be added in front of
the matched group to align each column. The optional &lt;ws&gt; argument can
be used to add additional whitespace to the column separation.

The regular expression will be matched in case-sensitive mode"""

	yield _regex(view, reg, group, additional_ws, add_ws_group)

def regex_i(view, reg=None, group=1, additional_ws=1, add_ws_group=-1):
	"""Align selected in columns using a regular expression: align.regex [&lt;regex&gt;] [&lt;group&gt;] [&lt;ws&gt;]

Align the selected text in columns separated by the specified regular expression.
The optional group argument specifies on which group in the regular expression
the text should be aligned. Additional whitespace will be added in front of
the matched group to align each column. The optional &lt;ws&gt; argument can
be used to add additional whitespace to the column separation.

The regular expression will be matched in case-insensitive mode"""

	yield _regex(view, reg, group, additional_ws, add_ws_group, re.IGNORECASE)
