import commander.commands as commands
import finder

import pluma
import re

__commander_module__ = True
__root__ = ['regex_i']

class RegexFinder(finder.Finder):
	def __init__(self, entry, flags = 0):
		finder.Finder.__init__(self, entry)

		self.flags = re.UNICODE | re.MULTILINE | re.DOTALL | flags
		self.groupre = re.compile('(\\\\)?\\$([0-9]+|{(([0-9]+):([^}]+))})')

	def set_find(self, findstr):
		finder.Finder.set_find(self, findstr)

		try:
			self.findre = re.compile(findstr, self.flags)
		except Exception, e:
			raise commands.exceptions.Execute('Invalid regular expression: ' + str(e))

	def do_find(self, bounds):
		buf = self.view.get_buffer()

		text = bounds[0].get_text(bounds[1])
		ret = self.findre.search(text)

		if ret:
			start = bounds[0].copy()
			start.forward_chars(ret.start())

			end = bounds[0].copy()
			end.forward_chars(ret.end())

			return [start, end]
		else:
			return False

	def _transform(self, text, trans):
		if not trans:
			return text

		transforms = {
			'u': lambda x: "%s%s" % (x[0].upper(), x[1:]),
			'U': lambda x: x.upper(),
			'l': lambda x: "%s%s" % (x[0].lower(), x[1:]),
			'L': lambda x: x.lower(),
			't': lambda x: x.title()
		}

		for i in trans.split(','):
			if i in transforms:
				text = transforms[i](text)

		return text

	def _do_re_replace_group(self, matchit, group):
		if group.group(3):
			num = int(group.group(4))
		else:
			num = int(group.group(2))

		if group.group(1):
			return group.group(2)
		elif num < len(matchit.groups()) + 1:
			return self._transform(matchit.group(num), group.group(5))
		else:
			return group.group(0)

	def _do_re_replace(self, matchit):
		return self.groupre.sub(lambda x: self._do_re_replace_group(matchit, x), self.replacestr)

	def get_replace(self, text):
		try:
			return self.findre.sub(self._do_re_replace, text)
		except Exception, e:
			raise commands.exceptions.Execute('Invalid replacement: ' + str(e))

class SemanticFinder(RegexFinder):
	def __init__(self, entry):
		RegexFinder.__init__(self, entry, re.IGNORECASE)

	def split_semantic(self, s):
		# Can be specified in _ separated syntax, or in TitleCase
		if '_' in s:
			return s.lower().split('_')
		else:
			return [m.group(0).lower() for m in re.finditer('[A-Z]+([^A-Z]+)?', s)]

	def set_find(self, findstr):
		self.findparts = self.split_semantic(findstr)
		RegexFinder.set_find(self, '(' + ')(_?)('.join(map(lambda x: re.escape(x), self.findparts)) + ')')

	def set_replace(self, replstr):
		self.replaceparts = self.split_semantic(replstr)
		RegexFinder.set_replace(self, replstr)

	def copy_case(self, orig, repl):
		lo = len(orig)
		lr = len(repl)

		ret = ''

		for i in range(min(lr, lo)):
			if orig[i].isupper():
				ret += repl[i].upper()
			else:
				ret += repl[i].lower()

		if lr > lo:
			if orig.isupper():
				ret += repl[lo:].upper()
			else:
				ret += repl[lo:].lower()

		return ret

	def get_replace(self, text):
		m = self.findre.match(text)
		groups = m.groups()

		ret = []

		for i in range(len(groups)):
			ri = i / 2

			if i % 2 == 0:
				if ri >= len(self.replaceparts):
					break

				ret.append(self.copy_case(groups[i], self.replaceparts[ri]))
			else:
				ret.append(groups[i])

		return ''.join(ret)

def __default__(entry, argstr):
	"""Find regex in document: find.regex &lt;regex&gt;

Find text in the document that matches a given regular expression. The regular
expression syntax is that of python regular expressions."""
	fd = RegexFinder(entry)
	yield fd.find(argstr)

def _find_insensitive(entry, argstr):
	"""Find regex in document (case insensitive): find.regex-i &lt;regex&gt;

Find text in the document that matches a given regular expression. The regular
expression syntax is that of python regular expressions. Matching dicards case."""
	fd = RegexFinder(entry, re.IGNORECASE)
	yield fd.find(argstr)

def replace(entry, findre, replstr=None):
	"""Find/replace regex in document: find.replace &lt;find&gt; [&lt;replace&gt;]

Quickly find and replace phrases in the document using regular expressions"""
	fd = RegexFinder(entry)
	yield fd.replace(findre, False, replstr)

def replace_i(entry, findre, replstr=None):
	"""Find/replace regex in document (case insensitive): find.replace-i &lt;find&gt; [&lt;replace&gt;]

Quickly find and replace phrases in the document using regular expressions"""
	fd = RegexFinder(entry, re.IGNORECASE)
	yield fd.replace(findre, False, replstr)

def replace_all(entry, findre, replstr=None):
	"""Find/replace all regex in document: find.regex.replace-all &lt;find&gt; [&lt;replace&gt;]

Quickly find and replace all phrases in the document using regular expressions"""
	fd = RegexFinder(entry, 0)
	yield fd.replace(findre, True, replstr)

def replace_all_i(entry, findre, replstr=None):
	"""Find/replace all regex in document: find.regex.replace-all-i &lt;find&gt; [&lt;replace&gt;]

Quickly find and replace all phrases in the document using regular expressions"""
	fd = RegexFinder(entry, re.IGNORECASE)
	yield fd.replace(findre, True, replstr)

def replace_semantic(entry, findstr, replstr=None):
	"""Find/replace in document (semantically): find.regex.replace-s &lt;find&gt; [&lt;replace&gt;]

Find and replace semantically"""
	fd = SemanticFinder(entry)
	yield fd.replace(findstr, False, replstr)

def replace_all_semantic(entry, findstr, replstr=None):
	"""Find/replace in document (semantically): find.regex.replace-s &lt;find&gt; [&lt;replace&gt;]

Find and replace semantically"""
	fd = SemanticFinder(entry)
	yield fd.replace(findstr, True, replstr)
