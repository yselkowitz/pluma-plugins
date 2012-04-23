import sys
import utils

class RollbackImporter:
	def __init__(self):
		"Creates an instance and installs as the global importer"
		self._new_modules = []
		self._original_import = __builtins__['__import__']

	def monitor(self):
		__builtins__['__import__'] = self._import

	def cancel(self):
		__builtins__['__import__'] = self._original_import

	def _import(self, name, globals=None, locals=None, fromlist=[], level=-1):
		maybe = not name in sys.modules

		mod = apply(self._original_import, (name, globals, locals, fromlist, level))

		if maybe and utils.is_commander_module(mod):
			self._new_modules.append(name)

		return mod

	def uninstall(self):
		self.cancel()

		for modname in self._new_modules:
			if modname in sys.modules:
				del sys.modules[modname]

		self._new_modules = []



