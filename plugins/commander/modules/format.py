import commander.commands as commands

__commander_module__ = True

def remove_trailing_spaces(view, all=False):
	"""Remove trailing spaces: format.remove-trailing-spaces [&lt;all&gt;]

Remove trailing spaces in the selection. If there is no selection, trailing
spaces are removed from the whole document. When the optional argument
&lt;all&gt; is specified, trailing spaces will be removed from all
the open documents."""

	if all:
		buffers = view.get_toplevel().get_documents()
	else:
		buffers = [view.get_buffer()]

	for buf in buffers:
		bounds = buf.get_selection_bounds()

		if not bounds:
			bounds = buf.get_bounds()

		buf.begin_user_action()

		try:
			# For each line, remove trailing spaces
			if not bounds[1].ends_line():
				bounds[1].forward_to_line_end()

			until = buf.create_mark(None, bounds[1], False)
			start = bounds[0]
			start.set_line_offset(0)

			while start.compare(buf.get_iter_at_mark(until)) < 0:
				end = start.copy()
				end.forward_to_line_end()
				last = end.copy()

				if end.equal(buf.get_end_iter()):
					end.backward_char()

				while end.get_char().isspace() and end.compare(start) > 0:
					end.backward_char()

				if not end.ends_line():
					if not end.get_char().isspace():
						end.forward_char()

					buf.delete(end, last)

				start = end.copy()
				start.forward_line()

		except Exception, e:
			print e

		buf.delete_mark(until)
		buf.end_user_action()

	return commands.result.HIDE

def _transform(view, how, all):
	if all:
		buffers = view.get_toplevel().get_documents()
	else:
		buffers = [view.get_buffer()]

	for buf in buffers:
		bounds = buf.get_selection_bounds()

		if not bounds:
			start = buf.get_iter_at_mark(buf.get_insert())
			end = start.copy()

			if not end.ends_line():
				end.forward_to_line_end()

			bounds = [start, end]

		if not bounds[0].equal(bounds[1]):
			text = how(bounds[0].get_text(bounds[1]))

			buf.begin_user_action()
			buf.delete(bounds[0], bounds[1])
			buf.insert(bounds[0], text)
			buf.end_user_action()

	return commands.result.HIDE

def upper(view, all=False):
	"""Make upper case: format.upper [&lt;all&gt;]

Transform text in selection to upper case. If the optional argument &lt;all&gt;
is specified, text in all the open documents will be transformed."""
	return _transform(view, lambda x: x.upper(), all)

def lower(view, all=False):
	"""Make lower case: format.lower [&lt;all&gt;]

Transform text in selection to lower case. If the optional argument &lt;all&gt;
is specified, text in all the open documents will be transformed."""
	return _transform(view, lambda x: x.lower(), all)

def title(view, all=False):
	"""Make title case: format.title [&lt;all&gt;]

Transform text in selection to title case. If the optional argument &lt;all&gt;
is specified, text in all the open documents will be transformed."""
	return _transform(view, lambda x: x.title().replace('_', ''), all)
