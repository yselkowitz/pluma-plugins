import gtk

class Accelerator:
	def __init__(self, accelerators, arguments={}):
		if not hasattr(accelerators, '__iter__'):
			accelerators = [accelerators]

		self.accelerators = accelerators
		self.arguments = arguments

class AccelCallback:
	def __init__(self, accel, callback, data):
		self.accelerator = accel
		self.callback = callback
		self.data = data

	def activate(self, state, entry):
		self.callback(self.accelerator, self.data, state, entry)

class AccelGroup:
	def __init__(self, parent=None, name='', accelerators={}):
		self.accelerators = dict(accelerators)
		self.parent = parent
		self.name = name

	def add(self, accel, callback, data=None):
		num = len(accel.accelerators)
		mapping = self.accelerators

		for i in range(num):
			parsed = gtk.accelerator_parse(accel.accelerators[i])

			if not gtk.accelerator_valid(*parsed):
				return

			named = gtk.accelerator_name(*parsed)
			inmap = named in mapping

			if i == num - 1 and inmap:
				# Last one cannot be in the map
				return
			elif inmap and isinstance(mapping[named], AccelCallback):
				# It's already mapped...
				return
			else:
				if not inmap:
					mapping[named] = {}

				if i == num - 1:
					mapping[named] = AccelCallback(accel, callback, data)

				mapping = mapping[named]

	def remove_real(self, accelerators, accels):
		if not accels:
			return

		parsed = gtk.accelerator_parse(accels[0])

		if not gtk.accelerator_valid(*parsed):
			return

		named = gtk.accelerator_name(*parsed)

		if not named in accelerators:
			return

		if len(accels) == 1:
			del accelerators[named]
		else:
			self.remove_real(accelerators[named], accels[1:])

			if not accelerators[named]:
				del accelerators[named]

	def remove(self, accel):
		self.remove_real(self.accelerators, accel.accelerators)

	def activate(self, key, mod):
		named = gtk.accelerator_name(key, mod)

		if not named in self.accelerators:
			return None

		accel = self.accelerators[named]

		if isinstance(accel, AccelCallback):
			return accel
		else:
			return AccelGroup(self, named, accel)

	def full_name(self):
		name = ''

		if self.parent:
			name = self.parent.full_name()

		if self.name:
			if name:
				name += ', '

			name += self.name

		return name
