import gtk
import cairo
import glib
import os
import re
import inspect

import commander.commands as commands
import commands.completion
import commands.module
import commands.method
import commands.exceptions
import commands.accel_group

import commander.utils as utils

from history import History
from info import Info
from xml.sax import saxutils
import traceback

class Entry(gtk.EventBox):
	def __init__(self, view):
		gtk.EventBox.__init__(self)
		self._view = view

		hbox = gtk.HBox(False, 3)
		hbox.show()
		hbox.set_border_width(3)

		self._entry = gtk.Entry()
		self._entry.modify_font(self._view.style.font_desc)
		self._entry.set_has_frame(False)
		self._entry.set_name('command-bar')
		self._entry.modify_text(gtk.STATE_NORMAL, self._view.style.text[gtk.STATE_NORMAL])
		self._entry.set_app_paintable(True)

		self._entry.connect('realize', self.on_realize)
		self._entry.connect('expose-event', self.on_entry_expose)

		self._entry.show()

		self._prompt_label = gtk.Label('<b>&gt;&gt;&gt;</b>')
		self._prompt_label.set_use_markup(True)
		self._prompt_label.modify_font(self._view.style.font_desc)
		self._prompt_label.show()
		self._prompt_label.modify_fg(gtk.STATE_NORMAL, self._view.style.text[gtk.STATE_NORMAL])

		self.modify_bg(gtk.STATE_NORMAL, self.background_gdk())
		self._entry.modify_base(gtk.STATE_NORMAL, self.background_gdk())

		self._entry.connect('focus-out-event', self.on_entry_focus_out)
		self._entry.connect('key-press-event', self.on_entry_key_press)

		self.connect_after('size-allocate', self.on_size_allocate)
		self.connect_after('expose-event', self.on_expose)
		self.connect_after('realize', self.on_realize)

		self._history = History(os.path.expanduser('~/.config/pluma/commander/history'))
		self._prompt = None

		self._accel_group = None

		hbox.pack_start(self._prompt_label, False, False, 0)
		hbox.pack_start(self._entry, True, True, 0)

		self.add(hbox)
		self.attach()

		self._entry.grab_focus()
		self._wait_timeout = 0
		self._info_window = None

		self.connect('destroy', self.on_destroy)

		self._history_prefix = None
		self._suspended = None
		self._handlers = [
			[0, gtk.keysyms.Up, self.on_history_move, -1],
			[0, gtk.keysyms.Down, self.on_history_move, 1],
			[None, gtk.keysyms.Return, self.on_execute, None],
			[None, gtk.keysyms.KP_Enter, self.on_execute, None],
			[0, gtk.keysyms.Tab, self.on_complete, None],
			[0, gtk.keysyms.ISO_Left_Tab, self.on_complete, None]
		]

		self._re_complete = re.compile('("((?:\\\\"|[^"])*)"?|\'((?:\\\\\'|[^\'])*)\'?|[^\s]+)')
		self._command_state = commands.Commands.State()

	def view(self):
		return self._view

	def on_realize(self, widget):
		widget.window.set_back_pixmap(None, False)

	def on_entry_expose(self, widget, evnt):
		ct = evnt.window.cairo_create()
		ct.rectangle(evnt.area.x, evnt.area.y, evnt.area.width, evnt.area.height)

		bg = self.background_color()
		ct.set_source_rgb(bg[0], bg[1], bg[2])
		ct.fill()

		return False

	def on_expose(self, widget, evnt):
		ct = evnt.window.cairo_create()
		color = self.background_color()

		ct.rectangle(evnt.area.x, evnt.area.y, evnt.area.width, evnt.area.height)
		ct.clip()

		# Draw separator line
		ct.move_to(0, 0)
		ct.set_line_width(1)
		ct.line_to(self.allocation.width, 0)

		ct.set_source_rgb(1 - color[0], 1 - color[1], 1 - color[2])
		ct.stroke()
		return False

	def on_size_allocate(self, widget, alloc):
		vwwnd = self._view.get_window(gtk.TEXT_WINDOW_BOTTOM).get_parent()
		size = vwwnd.get_size()
		position = vwwnd.get_position()

		self._view.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM, alloc.height)

	def attach(self):
		# Attach ourselves in the text view, and position just above the
		# text window
		self._view.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM, 1)
		alloc = self._view.allocation

		self.show()
		self._view.add_child_in_window(self, gtk.TEXT_WINDOW_BOTTOM, 0, 0)
		self.set_size_request(alloc.width, -1)

	def background_gdk(self):
		bg = self.background_color()

		bg = map(lambda x: int(x * 65535), bg)
		return gtk.gdk.Color(bg[0], bg[1], bg[2])

	def background_color(self):
		bg = self._view.get_style().base[self._view.state]

		vals = [bg.red, bg.green, bg.blue, 1]

		for i in range(3):
			val = vals[i] / 65535.0

			if val < 0.0001:
				vals[i] = 0.1
			elif val > 0.9999:
				vals[i] = 0.9
			elif val < 0.1:
				vals[i] = val * 1.2
			else:
				vals[i] = val * 0.8

		return vals

	def on_entry_focus_out(self, widget, evnt):
		if self._entry.flags() & gtk.SENSITIVE:
			self.destroy()

	def on_entry_key_press(self, widget, evnt):
		state = evnt.state & gtk.accelerator_get_default_mod_mask()
		text = self._entry.get_text()

		if evnt.keyval == gtk.keysyms.Escape:
			if self._info_window:
				if self._suspended:
					self._suspended.resume()

				if self._info_window:
					self._info_window.destroy()

				self._entry.set_sensitive(True)
			elif self._accel_group:
				self._accel_group = self._accel_group.parent

				if not self._accel_group or not self._accel_group.parent:
					self._entry.set_editable(True)
					self._accel_group = None

				self.prompt()
			elif text:
				self._entry.set_text('')
			elif self._command_state:
				self._command_state.clear()
				self.prompt()
			else:
				self._view.grab_focus()
				self.destroy()

			return True

		if state or self._accel_group:
			# Check if it should be handled by the accel group
			group = self._accel_group

			if not self._accel_group:
				group = commands.Commands().accelerator_group()

			accel = group.activate(evnt.keyval, state)

			if isinstance(accel, commands.accel_group.AccelGroup):
				self._accel_group = accel
				self._entry.set_text('')
				self._entry.set_editable(False)
				self.prompt()

				return True
			elif isinstance(accel, commands.accel_group.AccelCallback):
				self._entry.set_editable(True)
				self.run_command(lambda: accel.activate(self._command_state, self))
				return True

		if not self._entry.get_editable():
			return True

		for handler in self._handlers:
			if (handler[0] == None or handler[0] == state) and evnt.keyval == handler[1] and handler[2](handler[3], state):
				return True

		if self._info_window and self._info_window.empty():
			self._info_window.destroy()

		self._history_prefix = None
		return False

	def on_history_move(self, direction, modifier):
		pos = self._entry.get_position()

		self._history.update(self._entry.get_text())

		if self._history_prefix == None:
			if len(self._entry.get_text()) == pos:
				self._history_prefix = self._entry.get_chars(0, pos)
			else:
				self._history_prefix = ''

		if self._history_prefix == None:
			hist = ''
		else:
			hist = self._history_prefix

		next = self._history.move(direction, hist)

		if next != None:
			self._entry.set_text(next)
			self._entry.set_position(-1)

		return True

	def prompt(self, pr=''):
		self._prompt = pr

		if self._accel_group != None:
			pr = '<i>%s</i>' % (saxutils.escape(self._accel_group.full_name()),)

		if not pr:
			pr = ''
		else:
			pr = ' ' + pr

		self._prompt_label.set_markup('<b>&gt;&gt;&gt;</b>%s' % pr)

	def make_info(self):
		if self._info_window == None:
			self._info_window = Info(self)
			self._info_window.show()

			self._info_window.connect('destroy', self.on_info_window_destroy)

	def on_info_window_destroy(self, widget):
		self._info_window = None

	def info_show(self, text='', use_markup=False):
		self.make_info()
		self._info_window.add_lines(text, use_markup)

	def info_status(self, text):
		self.make_info()
		self._info_window.status(text)

	def info_add_action(self, stock, callback, data=None):
		self.make_info()
		return self._info_window.add_action(stock, callback, data)

	def command_history_done(self):
		self._history.add(self._entry.get_text())
		self._history_prefix = None
		self._entry.set_text('')

	def on_wait_cancel(self):
		if self._suspended:
			self._suspended.resume()

		if self._cancel_button:
			self._cancel_button.destroy()

		if self._info_window and self._info_window.empty():
			self._info_window.destroy()
			self._entry.grab_focus()
			self._entry.set_sensitive(True)

	def _show_wait_cancel(self):
		self._cancel_button = self.info_add_action(gtk.STOCK_STOP, self.on_wait_cancel)
		self.info_status('<i>Waiting to finish...</i>')

		self._wait_timeout = 0
		return False

	def _complete_word_match(self, match):
		for i in (3, 2, 0):
			if match.group(i) != None:
				return [match.group(i), match.start(i), match.end(i)]

	def on_suspend_resume(self):
		if self._wait_timeout:
			glib.source_remove(self._wait_timeout)
			self._wait_timeout = 0
		else:
			self._cancel_button.destroy()
			self._cancel_button = None
			self.info_status(None)

		self._entry.set_sensitive(True)
		self.command_history_done()

		if self._entry.props.has_focus or (self._info_window and not self._info_window.empty()):
			self._entry.grab_focus()

		self.on_execute(None, 0)

	def ellipsize(self, s, size):
		if len(s) <= size:
			return s

		mid = (size - 4) / 2
		return s[:mid] + '...' + s[-mid:]

	def destroy(self):
		self.hide()
		gtk.EventBox.destroy(self)

	def run_command(self, cb):
		self._suspended = None

		try:
			ret = cb()
		except Exception, e:
			self.command_history_done()
			self._command_state.clear()

			self.prompt()

			# Show error in info
			self.info_show('<b><span color="#f66">Error:</span></b> ' + saxutils.escape(str(e)), True)

			if not isinstance(e, commands.exceptions.Execute):
				self.info_show(traceback.format_exc(), False)

			return None

		if ret == commands.result.Result.SUSPEND:
			# Wait for it...
			self._suspended = ret
			ret.register(self.on_suspend_resume)

			self._wait_timeout = glib.timeout_add(500, self._show_wait_cancel)
			self._entry.set_sensitive(False)
		else:
			self.command_history_done()
			self.prompt('')

			if ret == commands.result.Result.PROMPT:
				self.prompt(ret.prompt)
			elif (ret == None or ret == commands.result.HIDE) and not self._prompt and (not self._info_window or self._info_window.empty()):
				self._command_state.clear()
				self._view.grab_focus()
				self.destroy()
			else:
				self._entry.grab_focus()

		return ret

	def on_execute(self, dummy, modifier):
		if self._info_window and not self._suspended:
			self._info_window.destroy()

		text = self._entry.get_text().strip()
		words = list(self._re_complete.finditer(text))
		wordsstr = []

		for word in words:
			spec = self._complete_word_match(word)
			wordsstr.append(spec[0])

		if not wordsstr and not self._command_state:
			self._entry.set_text('')
			return

		self.run_command(lambda: commands.Commands().execute(self._command_state, text, words, wordsstr, self, modifier))

		return True

	def on_complete(self, dummy, modifier):
		# First split all the text in words
		text = self._entry.get_text()
		pos = self._entry.get_position()

		words = list(self._re_complete.finditer(text))
		wordsstr = []

		for word in words:
			spec = self._complete_word_match(word)
			wordsstr.append(spec[0])

		# Find out at which word the cursor actually is
		# Examples:
		#  * hello world|
		#  * hello| world
		#  * |hello world
		#  * hello wor|ld
		#  * hello  |  world
		#  * "hello world|"
		posidx = None

		for idx in xrange(0, len(words)):
			spec = self._complete_word_match(words[idx])

			if words[idx].start(0) > pos:
				# Empty space, new completion
				wordsstr.insert(idx, '')
				words.insert(idx, None)
				posidx = idx
				break
			elif spec[2] == pos:
				# At end of word, resume completion
				posidx = idx
				break
			elif spec[1] <= pos and spec[2] > pos:
				# In middle of word, do not complete
				return True

		if posidx == None:
			wordsstr.append('')
			words.append(None)
			posidx = len(wordsstr) - 1

		# First word completes a command, if not in any special 'mode'
		# otherwise, relay completion to the command, or complete by advice
		# from the 'mode' (prompt)
		cmds = commands.Commands()

		if not self._command_state and posidx == 0:
			# Complete the first command
			ret = commands.completion.command(words=wordsstr, idx=posidx)
		else:
			complete = None
			realidx = posidx

			if not self._command_state:
				# Get the command first
				cmd = commands.completion.single_command(wordsstr, 0)
				realidx -= 1

				ww = wordsstr[1:]
			else:
				cmd = self._command_state.top()
				ww = wordsstr

			if cmd:
				complete = cmd.autocomplete_func()

			if not complete:
				return True

			# 'complete' contains a dict with arg -> func to do the completion
			# of the named argument the command (or stack item) expects
			args, varargs = cmd.args()

			# Remove system arguments
			s = ['argstr', 'args', 'entry', 'view']
			args = filter(lambda x: not x in s, args)

			if realidx < len(args):
				arg = args[realidx]
			elif varargs:
				arg = '*'
			else:
				return True

			if not arg in complete:
				return True

			func = complete[arg]

			try:
				spec = utils.getargspec(func)

				if not ww:
					ww = ['']

				kwargs = {
					'words': ww,
					'idx': realidx,
					'view': self._view
				}

				if not spec.keywords:
					for k in kwargs.keys():
						if not k in spec.args:
							del kwargs[k]

				ret = func(**kwargs)
			except Exception, e:
				# Can be number of arguments, or return values or simply buggy
				# modules
				print e
				traceback.print_exc()
				return True

		if not ret or not ret[0]:
			return True

		res = ret[0]
		completed = ret[1]

		if len(ret) > 2:
			after = ret[2]
		else:
			after = ' '

		# Replace the word
		if words[posidx] == None:
			# At end of everything, just append
			spec = None

			self._entry.insert_text(completed, self._entry.get_text_length())
			self._entry.set_position(-1)
		else:
			spec = self._complete_word_match(words[posidx])

			self._entry.delete_text(spec[1], spec[2])
			self._entry.insert_text(completed, spec[1])
			self._entry.set_position(spec[1] + len(completed))

		if len(res) == 1:
			# Full completion
			lastpos = self._entry.get_position()

			if not isinstance(res[0], commands.module.Module) or not res[0].commands():
				if words[posidx] and after == ' ' and (words[posidx].group(2) != None or words[posidx].group(3) != None):
					lastpos = lastpos + 1

				self._entry.insert_text(after, lastpos)
				self._entry.set_position(lastpos + 1)
			elif completed == wordsstr[posidx] or not res[0].method:
				self._entry.insert_text('.', lastpos)
				self._entry.set_position(lastpos + 1)

			if self._info_window:
				self._info_window.destroy()
		else:
			# Show popup with completed items
			if self._info_window:
				self._info_window.clear()

			ret = []

			for x in res:
				if isinstance(x, commands.method.Method):
					ret.append('<b>' + saxutils.escape(x.name) + '</b> (<i>' + x.oneline_doc() + '</i>)')
				else:
					ret.append(str(x))

			self.info_show("\n".join(ret), True)

		return True

	def on_destroy(self, widget):
		self._view.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM, 0)

		if self._info_window:
			self._info_window.destroy()

		self._history.save()

gtk.rc_parse_string("""
binding "TerminalLike" {
	unbind "<Control>A"

	bind "<Control>W" {
		"delete-from-cursor" (word-ends, -1)
	}
	bind "<Control>A" {
		"move-cursor" (buffer-ends, -1, 0)
	}
	bind "<Control>U" {
		"delete-from-cursor" (display-line-ends, -1)
	}
	bind "<Control>K" {
		"delete-from-cursor" (display-line-ends, 1)
	}
	bind "<Control>E" {
		"move-cursor" (buffer-ends, 1, 0)
	}
	bind "Escape" {
		"delete-from-cursor" (display-lines, 1)
	}
}

style "NoBackground" {
	engine "pixmap" {
		image {
			function = FLAT_BOX
			detail = "entry_bg"
		}
	}
}

widget "*.command-bar" binding "TerminalLike"
widget "*.command-bar" style "NoBackground"
""")
