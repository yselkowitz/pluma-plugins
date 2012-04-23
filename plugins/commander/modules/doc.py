import commander.commands as commands
import commander.commands.completion
import commander.commands.result
import commander.commands.exceptions
import re

__commander_module__ = True

class Argument:
	def __init__(self, argtype, typename, name):
		self.type = argtype.strip()
		self.type_name = typename.strip()
		self.name = name.strip()

class Function:
	def __init__(self, text):
		self._parse(text)

	def _parse(self, text):
		self.valid = False

		parser = re.compile('^\\s*(?:(?:\\b(?:static|inline)\\b)\\s+)?(([a-z_:][a-z0-9_:<>]*)(?:\\s*(?:\\b(?:const)\\b)\\s*)?\\s*[*&]*\\s+)?([a-z_][a-z0-9_:~]*)\\s*\\(([^)]*)\\)(\\s*const)?', re.I)

		m = parser.match(text)

		if not m:
			return

		self.valid = True

		self.return_type = m.group(1) and m.group(1).strip() != 'void' and m.group(1).strip()
		self.return_type_name = self.return_type and m.group(2).strip()

		parts = m.group(3).split('::')
		self.name = parts[-1]

		if len(parts) > 1:
			self.classname = '::'.join(parts[0:-1])
		else:
			self.classname = None

		self.constructor = self.name == self.classname
		self.destructor = self.name == '~%s' % (self.classname,)

		self.const = m.group(5) != None
		self.args = []

		argre = re.compile('(([a-z_:][a-z0-9_:<>]*)(?:\\s*(?:\\s*\\bconst\\b\\s*|[*&])\s*)*)\\s*([a-z_][a-z_0-9]*)$', re.I)

		for arg in m.group(4).split(','):
			arg = arg.strip()

			if arg == 'void' or arg == '':
				continue
			else:
				m2 = argre.match(arg.strip())

				if not m2:
					self.valid = False
					return

				arg = Argument(m2.group(1), m2.group(2), m2.group(3))

			self.args.append(arg)

class Documenter:
	def __init__(self, window, view, iter):
		self.window = window
		self.view = view
		self.iter = iter

		bus = self.window.get_message_bus()

		self.canplaceholder = bus.lookup('/plugins/snippets', 'parse-and-activate') != None
		self.placeholder = 1
		self.text = ''

	def append(self, *args):
		for text in args:
			self.text += str(text)

		return self

	def append_placeholder(self, *args):
		if not self.canplaceholder:
			return self.append(*args)

		text = " ".join(map(lambda x: str(x), args))
		self.text += "${%d:%s}" % (self.placeholder, text)
		self.placeholder += 1

		return self

	def insert(self):
		if self.canplaceholder:
			bus = self.window.get_message_bus()
			bus.send('/plugins/snippets', 'parse-and-activate', snippet=self.text, iter=self.iter, view=self.view)

def _make_documenter(window, view):
	buf = view.get_buffer()

	bus = window.get_message_bus()
	canplaceholder = bus.lookup('/plugins/snippets', 'parse-and-activate') != None

	insert = buf.get_iter_at_mark(buf.get_insert())
	insert.set_line_offset(0)

	offset = insert.get_offset()

	end = insert.copy()

	# This is just something random
	if not end.forward_chars(500):
		end = buf.get_end_iter()

	text = insert.get_text(end)
	func = Function(text)

	if not func.valid:
		raise commander.commands.exceptions.Execute('Could not find function specification')

	doc = Documenter(window, view, insert)
	return doc, func

def gtk(window, view):
	"""Generate gtk-doc documentation: doc.gtk

Generate a documentation template for the C or C++ function defined at the
cursor. The cursor needs to be on the first line of the function declaration
for it to work."""

	buf = view.get_buffer()
	lang = buf.get_language()

	if not lang or not lang.get_id() in ('c', 'chdr', 'cpp'):
		raise commander.commands.exceptions.Execute('Don\'t know about this language')

	doc, func = _make_documenter(window, view)

	# Generate docstring for this function
	doc.append("/**\n * ", func.name, ":\n")
	structp = re.compile('([A-Z]+[a-zA-Z]*)|struct\s+_([A-Z]+[a-zA-Z]*)')

	for arg in func.args:
		sm = structp.match(arg.type_name)
		doc.append(" * @", arg.name, ": ")

		if sm:
			doc.append_placeholder("A #%s" % (sm.group(1) or sm.group(2),))
		else:
			doc.append_placeholder("Description")

		doc.append("\n")

	doc.append(" * \n * ").append_placeholder("Description").append(".\n")

	if func.return_type:
		sm = structp.match(func.return_type_name)
		doc.append(" *\n * Returns: ")

		if sm:
			doc.append_placeholder("A #%s" % (sm.group(1) or sm.group(2),))
		else:
			doc.append_placeholder("Description")

		doc.append("\n")

	doc.append(" *\n **/\n")
	doc.insert()

def doxygen(window, view):
	"""Generate doxygen documentation: doc.doxygen

Generate a documentation template for the function defined at the
cursor. The cursor needs to be on the first line of the function declaration
for it to work."""

	buf = view.get_buffer()

	if not buf.get_language().get_id() in ('c', 'chdr', 'cpp'):
		raise commander.commands.exceptions.Execute('Don\'t know about this language')

	doc, func = _make_documenter(window, view)

	# Generate docstring for this function
	doc.append("/** \\brief ").append_placeholder("Short description")

	if func.const:
		doc.append(" (const)")

	doc.append(".\n")

	for arg in func.args:
		doc.append(" * @param ", arg.name, " ").append_placeholder("Description").append("\n")

	doc.append(" *\n * ")

	if func.constructor:
		doc.append("Constructor.\n *\n * ")
	elif func.destructor:
		doc.append("Destructor.\n *\n * ")

	doc.append_placeholder("Detailed description").append(".\n")

	if func.return_type:
		doc.append(" *\n * @return: ")

		if func.return_type == 'bool':
			doc.append("true if ").append_placeholder("Description").append(", false otherwise")
		else:
			doc.append_placeholder("Description")

		doc.append("\n")

	doc.append(" *\n */\n")
	doc.insert()
