class Result(object):
	HIDE = 1
	DONE = 2
	PROMPT = 3
	SUSPEND = 4

	def __init__(self, value):
		self._value = value

	def __int__(self):
		return self._value

	def __cmp__(self, other):
		if isinstance(other, int) or isinstance(other, Result):
			return cmp(int(self), int(other))
		else:
			return 1

# Easy shortcuts
HIDE = Result(Result.HIDE)
DONE = Result(Result.DONE)

class Prompt(Result):
	def __init__(self, prompt, autocomplete={}):
		Result.__init__(self, Result.PROMPT)

		self.prompt = prompt
		self.autocomplete = autocomplete

class Suspend(Result):
	def __init__(self):
		Result.__init__(self, Result.SUSPEND)
		self._callbacks = []

	def register(self, cb, *args):
		self._callbacks.append([cb, args])

	def resume(self):
		for cb in self._callbacks:
			args = cb[1]
			cb[0](*args)
