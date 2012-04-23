import sys
import os
import types
import bisect

import utils
import exceptions
import method
import rollbackimporter

class Module(method.Method):
	def __init__(self, base, mod, parent=None):
		method.Method.__init__(self, None, base, parent)

		self._commands = None
		self._dirname = None
		self._roots = None

		if type(mod) == types.ModuleType:
			self.mod = mod

			if '__default__' in mod.__dict__:
				self.method = mod.__dict__['__default__']
			else:
				self.method = None
		else:
			self.mod = None
			self._dirname = mod
			self._rollback = rollbackimporter.RollbackImporter()

	def commands(self):
		if self._commands == None:
			self.scan_commands()

		return self._commands

	def clear(self):
		self._commands = None

	def roots(self):
		if self._roots == None:
			if not self.mod:
				return []

			dic = self.mod.__dict__

			if '__root__' in dic:
				root = dic['__root__']
			else:
				root = []

			root = filter(lambda x: x in dic and type(dic[x]) == types.FunctionType, root)
			self._roots = map(lambda x: method.Method(dic[x], x, self.mod), root)

		return self._roots

	def scan_commands(self):
		self._commands = []

		if self.mod == None:
			return

		dic = self.mod.__dict__

		if '__root__' in dic:
			root = dic['__root__']
		else:
			root = []

		for k in dic:
			if k.startswith('_') or k in root:
				continue

			item = dic[k]

			if type(item) == types.FunctionType:
				bisect.insort(self._commands, method.Method(item, k, self))
			elif type(item) == types.ModuleType and utils.is_commander_module(item):
				mod = Module(k, item, self)
				bisect.insort(self._commands, mod)

				# Insert root functions into this module
				for r in mod.roots():
					bisect.insert(self._commands, r)

	def unload(self):
		self._commands = None

		if not self._dirname:
			return False

		self._rollback.uninstall()
		self.mod = None

		return True

	def reload(self):
		if not self.unload():
			return

		if self.name in sys.modules:
			raise Exception('Module already exists...')

		oldpath = list(sys.path)

		try:
			sys.path.insert(0, self._dirname)

			self._rollback.monitor()
			self.mod = __import__(self.name, globals(), locals(), [], 0)
			self._rollback.cancel()

			if not utils.is_commander_module(self.mod):
				raise Exception('Module is not a commander module...')

			if '__default__' in self.mod.__dict__:
				self.method = self.mod.__dict__['__default__']
			else:
				self.method = None

			self._func_props = None
		except:
			sys.path = oldpath
			self._rollback.uninstall()

			if self.name in sys.modules:
				del sys.modules[self.name]
			raise

		sys.path = oldpath

