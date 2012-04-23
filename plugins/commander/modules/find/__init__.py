import commander.commands as commands
import pluma
import re
import regex
from xml.sax import saxutils
import finder

__commander_module__ = True
__root__ = ['/', 'find_i', '//', 'r/', 'r//']

class TextFinder(finder.Finder):
	def __init__(self, entry, flags):
		finder.Finder.__init__(self, entry)

		self.flags = flags

	def do_find(self, bounds):
		buf = self.view.get_buffer()

		if self.get_find():
			buf.set_search_text(self.get_find(), self.flags)

		ret = map(lambda x: x.copy(), bounds)

		if buf.search_forward(bounds[0], bounds[1], ret[0], ret[1]):
			return ret
		else:
			return False

def __default__(entry, argstr):
	"""Find in document: find &lt;text&gt;

Quickly find phrases in the document"""
	fd = TextFinder(entry, pluma.SEARCH_CASE_SENSITIVE)
	yield fd.find(argstr)

def _find_insensitive(entry, argstr):
	"""Find in document (case insensitive): find-i &lt;text&gt;

Quickly find phrases in the document (case insensitive)"""
	fd = TextFinder(entry, 0)
	yield fd.find(argstr)

def replace(entry, findstr, replstr=None):
	"""Find/replace in document: find.replace &lt;find&gt; [&lt;replace&gt;]

Quickly find and replace phrases in the document"""
	fd = TextFinder(entry, pluma.SEARCH_CASE_SENSITIVE)
	yield fd.replace(findstr, False, replstr)

def replace_i(entry, findstr, replstr=None):
	"""Find/replace all in document (case insensitive): find.replace-i &lt;find&gt; [&lt;replace&gt;]

Quickly find and replace phrases in the document (case insensitive)"""
	fd = TextFinder(entry, 0)
	yield fd.replace(findstr, True, replstr)

def replace_all(entry, findstr, replstr=None):
	"""Find/replace all in document: find.replace-all &lt;find&gt; [&lt;replace&gt;]

Quickly find and replace all phrases in the document"""
	fd = TextFinder(entry, pluma.SEARCH_CASE_SENSITIVE)
	yield fd.replace(findstr, True, replstr)

def replace_all_i(entry, findstr, replstr=None):
	"""Find/replace all in document (case insensitive): find.replace-all-i &lt;find&gt; [&lt;replace&gt;]

Quickly find and replace all phrases in the document (case insensitive)"""
	fd = TextFinder(entry,0)
	yield fd.replace(findstr, True, replstr)

locals()['/'] = __default__
locals()['find_i'] = _find_insensitive
locals()['//'] = replace
locals()['r/'] = regex.__default__
locals()['r//'] = regex.replace
