import os
import types
import inspect
import sys

class Struct(dict):
	def __getattr__(self, name):
		if not name in self:
			val = super(Struct, self).__getattr__(self, name)
		else:
			val = self[name]

		return val

	def __setattr__(self, name, value):
		if not name in self:
			super(Struct, self).__setattr__(self, name, value)
		else:
			self[name] = value

	def __delattr__(self, name):
		del self[name]

def is_commander_module(mod):
	if type(mod) == types.ModuleType:
		return mod and ('__commander_module__' in mod.__dict__)
	else:
		mod = str(mod)
		return mod.endswith('.py') or (os.path.isdir(mod) and os.path.isfile(os.path.join(mod, '__init__.py')))

def getargspec(func):
	ret = inspect.getargspec(func)

	# Before 2.6 this was just a normal tuple, we don't want that
	if sys.version_info < (2, 6):
		ret = Struct({
			'args': ret[0],
			'varargs': ret[1],
			'keywords': ret[2],
			'defaults': ret[3]
		})

	return ret