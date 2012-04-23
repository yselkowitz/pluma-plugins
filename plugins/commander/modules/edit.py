"""Edit files or commands"""
import os
import gio
import pluma
import glob
import sys
import types
import inspect
import gio

import commander.commands as commands
import commander.commands.completion
import commander.commands.result
import commander.commands.exceptions

__commander_module__ = True

@commands.autocomplete(filename=commander.commands.completion.filename)
def __default__(filename, view):
	"""Edit file: edit &lt;filename&gt;"""

	doc = view.get_buffer()
	cwd = os.getcwd()

	if not doc.is_untitled():
		cwd = doc.get_location().get_parent().get_path()
	else:
		cwd = os.path.expanduser('~/')

	if not os.path.isabs(filename):
		filename = os.path.join(cwd, filename)

	matches = glob.glob(filename)
	files = []

	if matches:
		for match in matches:
			f = gio.File(match)
			files.append(f.get_uri())
	else:
		f = gio.File(filename)
		files.append(f.get_uri())

	if files:
		window = view.get_toplevel()
		pluma.commands.load_uris(window, files)

	return commander.commands.result.HIDE

def _dummy_cb(num, total):
	pass

@commands.autocomplete(newfile=commander.commands.completion.filename)
def rename(view, newfile):
	"""Rename current file: edit.rename &lt;newname&gt;"""

	doc = view.get_buffer()

	if not hasattr(doc, 'set_uri'):
		raise commander.commands.exceptions.Execute('Your version of pluma does not support this action')

	if doc.is_untitled():
		raise commander.commands.exceptions.Execute('Document is unsaved and thus cannot be renamed')

	if doc.get_modified():
		raise commander.commands.exceptions.Execute('You have unsaved changes in your document')

	if not doc.is_local():
		raise commander.commands.exceptions.Execute('You can only rename local files')

	f = doc.get_location()

	if not f.query_exists():
		raise commander.commands.exceptions.Execute('Current document file does not exist')

	if os.path.isabs(newfile):
		dest = gio.File(newfile)
	else:
		dest = f.get_parent().resolve_relative_path(newfile)

	if f.equal(dest):
		yield commander.commands.result.HIDE

	if not dest.get_parent().query_exists():
		# Check to create parent directory
		fstr, words, modifierret = (yield commands.result.Prompt('Directory does not exist, create? [Y/n] '))

		if fstr.strip().lower() in ['y', 'ye', 'yes', '']:
			# Create parent directories
			try:
				os.makedirs(dest.get_parent().get_path())
			except OSError, e:
				raise commander.commands.exceptions.Execute('Could not create directory')
		else:
			yield commander.commands.result.HIDE

	if dest.query_exists():
		fstr, words, modifierret = (yield commands.result.Prompt('Destination already exists, overwrite? [Y/n]'))

		if not fstr.strip().lower() in ['y', 'ye', 'yes', '']:
			yield commander.commands.result.HIDE

	try:
		f.move(dest, _dummy_cb, flags=gio.FILE_COPY_OVERWRITE)

		doc.set_uri(dest.get_uri())
		yield commander.commands.result.HIDE
	except Exception, e:
		raise commander.commands.exceptions.Execute('Could not move file: %s' % (e,))

def _mod_has_func(mod, func):
	return func in mod.__dict__ and type(mod.__dict__[func]) == types.FunctionType

def _mod_has_alias(mod, alias):
	return '__root__' in mod.__dict__ and alias in mod.__dict__['__root__']

def _edit_command(view, mod, func=None):
	try:
		location = gio.File(inspect.getsourcefile(mod))
	except:
		return False

	if not func:
		pluma.commands.load_uri(view.get_toplevel(), location.get_uri())
	else:
		try:
			lines = inspect.getsourcelines(func)
			line = lines[-1]
		except:
			line = 0

		pluma.commands.load_uri(view.get_toplevel(), location.get_uri(), None, line)

	return True

def _resume_command(view, mod, parts):
	if not parts:
		return _edit_command(view, mod)

	func = parts[0].replace('-', '_')

	if len(parts) == 1 and _mod_has_func(mod, func):
		return _edit_command(view, mod, mod.__dict__[func])
	elif len(parts) == 1 and _mod_has_alias(mod, parts[0]):
		return _edit_command(view, mod)

	if not func in mod.__dict__:
		return False

	if not commands.is_commander_module(mod.__dict__[func]):
		return False

	return _resume_command(view, mod.__dict__[func], parts[1:])

@commands.autocomplete(name=commander.commands.completion.command)
def command(view, name):
	"""Edit commander command: edit.command &lt;command&gt;"""
	parts = name.split('.')

	for mod in sys.modules:
		if commands.is_commander_module(sys.modules[mod]) and (mod == parts[0] or _mod_has_alias(sys.modules[mod], parts[0])):
			if mod == parts[0]:
				ret = _resume_command(view, sys.modules[mod], parts[1:])
			else:
				ret = _resume_command(view, sys.modules[mod], parts)

			if not ret:
				raise commander.commands.exceptions.Execute('Could not find command: ' + name)
			else:
				return commander.commands.result.HIDE

	raise commander.commands.exceptions.Execute('Could not find command: ' + name)

COMMAND_TEMPLATE="""import commander.commands as commands
import commander.commands.completion
import commander.commands.result
import commander.commands.exceptions

__commander_module__ = True

def __default__(view, entry):
	\"\"\"Some kind of cool new feature: cool &lt;something&gt;

Use this to apply the cool new feature\"\"\"
	pass
"""

def new_command(view, entry, name):
	"""Create a new commander command module: edit.new-command &lt;command&gt;"""

	filename = os.path.expanduser('~/.config/pluma/commander/modules/' + name + '.py')

	if os.path.isfile(filename):
		raise commander.commands.exceptions.Execute('Commander module `' + name + '\' already exists')

	dirname = os.path.dirname(filename)

	if not os.path.isdir(dirname):
		os.makedirs(dirname)

	f = open(filename, 'w')
	f.write(COMMAND_TEMPLATE)
	f.close()

	return __default__(filename, view)

def save(view):
	window = view.get_toplevel()
	pluma.commands.save_document(window, view.get_buffer())

	return commander.commands.result.HIDE

def save_all(view):
	window = view.get_toplevel()
	pluma.commands.save_all_documents(window)

	return commander.commands.result.HIDE

locals()['file'] = __default__
move = rename
