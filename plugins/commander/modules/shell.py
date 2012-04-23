import subprocess
import glib
import fcntl
import os
import tempfile
import signal
import gio

import commander.commands as commands
import commander.commands.exceptions
import commander.commands.result

__commander_module__ = True
__root__ = ['!', '!!', '!&']

class Process:
	def __init__(self, entry, pipe, replace, background, tmpin, stdout, suspend):
		self.pipe = pipe
		self.replace = replace
		self.tmpin = tmpin
		self.entry = entry
		self.suspend = suspend

		if replace:
			self.entry.view().set_editable(False)

		if not background:
			fcntl.fcntl(stdout, fcntl.F_SETFL, os.O_NONBLOCK)
			conditions = glib.IO_IN | glib.IO_PRI | glib.IO_ERR | glib.IO_HUP

			self.watch = glib.io_add_watch(stdout, conditions, self.collect_output)
			self._buffer = ''
		else:
			stdout.close()

	def update(self):
		parts = self._buffer.split("\n")

		for p in parts[:-1]:
			self.entry.info_show(p)

		self._buffer = parts[-1]

	def collect_output(self, fd, condition):
		if condition & (glib.IO_IN | glib.IO_PRI):
			try:
				ret = fd.read()

				# This seems to happen on OS X...
				if ret == '':
					condition = condition | glib.IO_HUP
				else:
					self._buffer += ret

					if not self.replace:
						self.update()
			except:
				self.entry.info_show(self._buffer.strip("\n"))
				self.stop()
				return False

		if condition & (glib.IO_ERR | glib.IO_HUP):
			if self.replace:
				buf = self.entry.view().get_buffer()
				buf.begin_user_action()

				bounds = buf.get_selection_bounds()

				if bounds:
					buf.delete(bounds[0], bounds[1])

				buf.insert_at_cursor(self._buffer)
				buf.end_user_action()
			else:
				self.entry.info_show(self._buffer.strip("\n"))

			self.stop()
			return False

		return True

	def stop(self):
		if not self.suspend:
			return

		if hasattr(self.pipe, 'kill'):
			self.pipe.kill()

		glib.source_remove(self.watch)

		if self.replace:
			self.entry.view().set_editable(True)

		if self.tmpin:
			self.tmpin.close()

		sus = self.suspend
		self.suspend = None
		sus.resume()

def _run_command(entry, replace, background, argstr):
	tmpin = None

	cwd = None
	doc = entry.view().get_buffer()

	if not doc.is_untitled() and doc.is_local():
		gfile = doc.get_location()
		cwd = os.path.dirname(gfile.get_path())

	if '<!' in argstr:
		bounds = entry.view().get_buffer().get_selection_bounds()

		if not bounds:
			bounds = entry.view().get_buffer().get_bounds()

		inp = bounds[0].get_text(bounds[1])

		# Write to temporary file
		tmpin = tempfile.NamedTemporaryFile(delete=False)
		tmpin.write(inp)
		tmpin.flush()

		# Replace with temporary file
		argstr = argstr.replace('<!', '< "' + tmpin.name + '"')

	try:
		p = subprocess.Popen(argstr, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		stdout = p.stdout

	except Exception, e:
		raise commander.commands.exceptions.Execute('Failed to execute: ' + e)

	suspend = None

	if not background:
		suspend = commander.commands.result.Suspend()

	proc = Process(entry, p, replace, background, tmpin, stdout, suspend)

	if not background:
		yield suspend

		# Cancelled or simply done
		proc.stop()

		yield commander.commands.result.DONE
	else:
		yield commander.commands.result.HIDE

def __default__(entry, argstr):
	"""Run shell command: ! &lt;command&gt;

You can use <b>&lt;!</b> as a special input meaning the current selection or current
document."""
	return _run_command(entry, False, False, argstr)

def background(entry, argstr):
	"""Run shell command in the background: !&amp; &lt;command&gt;

You can use <b>&lt;!</b> as a special input meaning the current selection or current
document."""
	return _run_command(entry, False, True, argstr)

def replace(entry, argstr):
	"""Run shell command and place output in document: !! &lt;command&gt;

You can use <b>&lt;!</b> as a special input meaning the current selection or current
document."""
	return _run_command(entry, True, False, argstr)

locals()['!'] = __default__
locals()['!!'] = replace
locals()['!&'] = background

