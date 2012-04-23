import sys
import os
import types

import commander.commands as commands
import commander.commands.completion

from xml.sax import saxutils

__commander_module__ = True

def _name_match(first, second):
	first = first.split('-')
	second = second.split('-')

	if len(first) > len(second):
		return False

	for i in xrange(0, len(first)):
		if not second[i].startswith(first[i]):
			return False

	return True

def _doc_text(command, func):
	if not _name_match(command.split('.')[-1], func.name):
		prefix = '<i>(Alias):</i> '
	else:
		prefix = ''

	doc = func.doc()

	if not doc:
		doc = "<b>%s</b>\n\n<i>No documentation available</i>" % (func.name,)
	else:
		parts = doc.split("\n")
		parts[0] = prefix + '<b>' + parts[0] + '</b>'
		doc = "\n".join(parts)

	return doc

@commands.autocomplete(command=commander.commands.completion.command)
def __default__(entry, command='help'):
	"""Show help on commands: help &lt;command&gt;

Show detailed information on how to use a certain command (if available)"""
	res = commander.commands.completion.command([command], 0)

	if not res:
		raise commander.commands.exceptions.Execute('Could not find command: ' + command)

	entry.info_show(_doc_text(command, res[0][0]), True)
	return commands.result.DONE
