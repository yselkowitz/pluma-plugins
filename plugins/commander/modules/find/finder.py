from xml.sax import saxutils
import commander.commands as commands
import commander.utils as utils
import gtk

class Finder:
	FIND_STARTMARK = 'pluma-commander-find-startmark'
	FIND_ENDMARK = 'pluma-commander-find-endmark'

	FIND_RESULT_STARTMARK = 'pluma-commander-find-result-startmark'
	FIND_RESULT_ENDMARK = 'pluma-commander-find-result-endmark'

	def __init__(self, entry):
		self.entry = entry
		self.view = entry.view()

		self.findstr = None
		self.replacestr = None

		self.search_boundaries = utils.Struct({'start': None, 'end': None})
		self.find_result = utils.Struct({'start': None, 'end': None})

		self.unescapes = [
			['\\n', '\n'],
			['\\r', '\r'],
			['\\t', '\t']
		]

		self.from_start = False
		self.search_start_mark = None

	def unescape(self, s):
		for esc in self.unescapes:
			s = s.replace(esc[0], esc[1])

		return s

	def do_find(self, bounds):
		return None

	def get_replace(self, text):
		return self.replacestr

	def set_replace(self, replacestr):
		self.replacestr = self.unescape(replacestr)

	def set_find(self, findstr):
		self.findstr = self.unescape(findstr)

	def get_find(self):
		return self.findstr

	def select_last_result(self):
		buf = self.view.get_buffer()

		startiter = buf.get_iter_at_mark(self.find_result.start)
		enditer = buf.get_iter_at_mark(self.find_result.end)

		buf.select_range(startiter, enditer)

		visible = self.view.get_visible_rect()
		loc = self.view.get_iter_location(startiter)

		# Scroll there if needed
		if loc.y + loc.height < visible.y or loc.y > visible.y + visible.height:
			self.view.scroll_to_iter(startiter, 0.2, True, 0, 0.5)

	def find_next(self, select=False):
		buf = self.view.get_buffer()

		# Search from the end of the last result to the end of the search boundary
		bounds = [buf.get_iter_at_mark(self.find_result.end),
			      buf.get_iter_at_mark(self.search_boundaries.end)]

		ret = self.do_find(bounds)

		# Check if we need to wrap around if nothing is found
		if self.search_start_mark:
			startiter = buf.get_iter_at_mark(self.search_start_mark)
		else:
			startiter = None

		startbound = buf.get_iter_at_mark(self.search_boundaries.start)

		if not ret and not self.from_start and (startiter and not startiter.equal(startbound)):
			self.from_start = True

			# Try from beginning
			bounds[0] = buf.get_start_iter()
			bounds[1] = startiter

			# Make sure to just stop at the start of the previous
			self.search_boundaries.end = self.search_start_mark

			ret = self.do_find(bounds)

		if not ret:
			return False
		else:
			# Mark find result
			buf.move_mark(self.find_result.start, ret[0])
			buf.move_mark(self.find_result.end, ret[1])

			if select:
				self.select_last_result()

			return True

	def _create_or_move(self, markname, piter, left_gravity):
		buf = self.view.get_buffer()
		mark = buf.get_mark(markname)

		if not mark:
			mark = buf.create_mark(markname, piter, left_gravity)
		else:
			buf.move_mark(mark, piter)

		return mark

	def find_first(self, doend=True, select=False):
		words = []
		buf = self.view.get_buffer()

		while not self.findstr:
			fstr, words, modifier = (yield commands.result.Prompt('Find:'))

			if fstr:
				self.set_find(fstr)

		# Determine search area
		bounds = list(buf.get_selection_bounds())

		if self.search_start_mark:
			buf.delete_mark(self.search_start_mark)
			self.search_start_mark = None

		if not bounds:
			# Search in the whole buffer, from the current cursor position on to the
			# end, and then continue to start from the beginning of the buffer if needed
			bounds = list(buf.get_bounds())
			self.search_start_mark = buf.create_mark(None, buf.get_iter_at_mark(buf.get_insert()), True)
			selection = False
		else:
			selection = True

		bounds[0].order(bounds[1])

		# Set marks at the boundaries
		self.search_boundaries.start = self._create_or_move(Finder.FIND_STARTMARK, bounds[0], True)
		self.search_boundaries.end = self._create_or_move(Finder.FIND_ENDMARK, bounds[1], False)

		# Set the result marks so the next find will start at the correct location
		if selection:
			piter = bounds[0]
		else:
			piter = buf.get_iter_at_mark(buf.get_insert())

		self.find_result.start = self._create_or_move(Finder.FIND_RESULT_STARTMARK, piter, True)
		self.find_result.end = self._create_or_move(Finder.FIND_RESULT_ENDMARK, piter, False)

		if not self.find_next(select=select):
			if doend:
				self.entry.info_show('<i>Search hit end of the document</i>', True)

			yield commands.result.DONE
		else:
			yield True

	def cancel(self):
		buf = self.view.get_buffer()

		buf.set_search_text('', 0)
		buf.move_mark(buf.get_selection_bound(), buf.get_iter_at_mark(buf.get_insert()))

		if self.search_start_mark:
			buf.delete_mark(self.search_start_mark)

	def find(self, findstr):
		if findstr:
			self.set_find(findstr)

		buf = self.view.get_buffer()

		try:
			if (yield self.find_first(select=True)):
				while True:
					argstr, words, modifier = (yield commands.result.Prompt('Search next [<i>%s</i>]:' % (saxutils.escape(self.findstr),)))

					if argstr:
						self.set_find(argstr)

					if not self.find_next(select=True):
						break

				self.entry.info_show('<i>Search hit end of the document</i>', True)
		except GeneratorExit, e:
			self.cancel()
			raise e

		self.cancel()
		yield commands.result.DONE

	def _restore_cursor(self, mark):
		buf = mark.get_buffer()

		buf.place_cursor(buf.get_iter_at_mark(mark))
		buf.delete_mark(mark)

		self.view.scroll_to_mark(buf.get_insert(), 0.2, True, 0, 0.5)

	def get_current_replace(self):
		buf = self.view.get_buffer()
		bounds = utils.Struct({'start': buf.get_iter_at_mark(self.find_result.start),
		                       'end': buf.get_iter_at_mark(self.find_result.end)})

		if not bounds.start.equal(bounds.end):
			text = bounds.start.get_text(bounds.end)
			return self.get_replace(text)
		else:
			return self.replacestr

	def replace(self, findstr, replaceall=False, replacestr=None):
		if findstr:
			self.set_find(findstr)

		if replacestr != None:
			self.set_replace(replacestr)

		# First find something
		buf = self.view.get_buffer()

		if replaceall:
			startmark = buf.create_mark(None, buf.get_iter_at_mark(buf.get_insert()), False)

		ret = (yield self.find_first(select=not replaceall))

		if not ret:
			yield commands.result.DONE

		self.scroll_back = False

		# Then ask for the replacement string
		if not self.replacestr:
			try:
				if replaceall:
					self.scroll_back = True
					self.select_last_result()

				replacestr, words, modifier = (yield commands.result.Prompt('Replace with:'))
				self.set_replace(replacestr)
			except GeneratorExit, e:
				if replaceall:
					self._restore_cursor(startmark)

				self.cancel()
				raise e

		# On replace all, wrap it in begin/end user action
		if replaceall:
			buf.begin_user_action()

		try:
			while True:
				if not replaceall:
					rep, words, modifier = (yield commands.result.Prompt('Replace next [%s]:' % (saxutils.escape(self.get_current_replace()),)))

					if rep:
						self.set_replace(rep)

				bounds = utils.Struct({'start': buf.get_iter_at_mark(self.find_result.start),
				                       'end': buf.get_iter_at_mark(self.find_result.end)})

				# If there is a selection, replace it with the replacement string
				if not bounds.start.equal(bounds.end) and (replaceall or not (modifier & gtk.gdk.CONTROL_MASK)):
					text = bounds.start.get_text(bounds.end)
					repl = self.get_replace(text)

					buf.begin_user_action()
					buf.delete(bounds.start, bounds.end)
					buf.insert(bounds.start, repl)
					buf.end_user_action()

				# Find next
				if not self.find_next(select=not replaceall):
					if not replaceall:
						self.entry.info_show('<i>Search hit end of the document</i>', True)

					break

		except GeneratorExit, e:
			if replaceall:
				self._restore_cursor(startmark)
				buf.end_user_action()

			self.cancel()
			raise e

		if replaceall:
			if self.scroll_back:
				self._restore_cursor(startmark)

			buf.end_user_action()

		self.cancel()
		yield commands.result.DONE
