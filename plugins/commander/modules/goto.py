"""Goto specific places in the document"""
import os

import commander.commands as commands
import commander.commands.completion
import commander.commands.result
import commander.commands.exceptions

__commander_module__ = True

def __default__(view, line, column=1):
	"""Goto line number"""

	buf = view.get_buffer()
	ins = buf.get_insert()
	citer = buf.get_iter_at_mark(ins)

	try:
		if line.startswith('+'):
			linnum = citer.get_line() + int(line[1:])
		elif line.startswith('-'):
			linnum = citer.get_line() - int(line[1:])
		else:
			linnum = int(line) - 1

		column = int(column) - 1
	except ValueError:
		raise commander.commands.exceptions.Execute('Please specify a valid line number')

	linnum = min(max(0, linnum), buf.get_line_count() - 1)
	citer = buf.get_iter_at_line(linnum)

	column = min(max(0, column), citer.get_chars_in_line() - 1)

	citer = buf.get_iter_at_line(linnum)
	citer.forward_chars(column)

	buf.place_cursor(citer)
	view.scroll_to_iter(citer, 0.0, True)

	return commander.commands.result.HIDE
