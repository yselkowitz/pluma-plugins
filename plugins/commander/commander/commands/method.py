import exceptions
import types
import inspect
import sys
import commander.utils as utils

class Method:
	def __init__(self, method, name, parent):
		self.method = method
		self.name = name.replace('_', '-')
		self.parent = parent
		self._func_props = None

	def __str__(self):
		return self.name

	def autocomplete_func(self):
		if hasattr(self.method, 'autocomplete'):
			return getattr(self.method, 'autocomplete')

		return None

	def accelerator(self):
		if hasattr(self.method, 'accelerator'):
			return getattr(self.method, 'accelerator')

		return None

	def args(self):
		fp = self.func_props()

		return fp.args, fp.varargs

	def func_props(self):
		if not self._func_props:
			# Introspect the function arguments
			self._func_props = utils.getargspec(self.method)

		return self._func_props

	def commands(self):
		return []

	def cancel(self, view):
		if self.parent:
			self.parent.cancel(view, self)

	def cancel_continuation(self, view):
		if self.parent:
			self.parent.continuation(view, self)

	def doc(self):
		if self.method.__doc__:
			return self.method.__doc__
		else:
			return ''

	def oneline_doc(self):
		return self.doc().split("\n")[0]

	def execute(self, argstr, words, entry, modifier, kk = {}):
		fp = self.func_props()

		kwargs = {'argstr': argstr, 'args': words, 'entry': entry, 'view': entry.view(), 'modifier': modifier, 'window': entry.view().get_toplevel()}
		oargs = list(fp.args)
		args = []
		idx = 0

		if fp.defaults:
			numdef = len(fp.defaults)
		else:
			numdef = 0

		for k in fp.args:
			if k in kwargs:
				args.append(kwargs[k])
				oargs.remove(k)
				del kwargs[k]
			elif idx >= len(words):
				if numdef < len(oargs):
					raise exceptions.Execute('Invalid number of arguments (need %s)' % (oargs[0],))
			else:
				args.append(words[idx])
				oargs.remove(k)
				idx += 1

		# Append the rest if it can handle varargs
		if fp.varargs and idx < len(words):
			args.extend(words[idx:])

		if not fp.keywords:
			kwargs = {}

		for k in kk:
			kwargs[k] = kk[k]

		return self.method(*args, **kwargs)

	def __cmp__(self, other):
		if isinstance(other, Method):
			return cmp(self.name, other.name)
		else:
			return cmp(self.name, other)

