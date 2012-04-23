from transparentwindow import TransparentWindow
import gtk
import math
import pango

class Info(TransparentWindow):
	def __init__(self, entry):
		TransparentWindow.__init__(self, gtk.WINDOW_POPUP)

		self._entry = entry
		self._vbox = gtk.VBox(False, 3)

		self.set_transient_for(entry.get_toplevel())

		self._vw = gtk.ScrolledWindow()
		self._vw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
		self._vw.show()

		self._text = gtk.TextView()
		self._text.modify_font(entry._view.style.font_desc)
		self._text.modify_text(gtk.STATE_NORMAL, entry._entry.style.text[gtk.STATE_NORMAL])
		self._text.connect('expose-event', self.on_text_expose)
		self._text.set_wrap_mode(gtk.WRAP_WORD_CHAR)

		buf = self._text.get_buffer()

		buf.connect_after('insert-text', self.on_text_insert_text)
		buf.connect_after('delete-range', self.on_text_delete_range)

		self._text.set_editable(False)

		self._vw.add(self._text)
		self._vbox.pack_end(self._vw, expand=False, fill=False)
		self._vbox.show()
		self._button_bar = None

		self.add(self._vbox)
		self._text.show()
		self._status_label = None

		self.props.can_focus = False
		self.set_border_width(8)

		self._text.connect('realize', self.on_text_realize)

		self.attach()
		self.show()

		self.connect_after('size-allocate', self.on_size_allocate)
		self._vw.connect_after('size-allocate', self.on_text_size_allocate)

		self.max_lines = 10

		self._attr_map = {
			pango.ATTR_STYLE: 'style',
			pango.ATTR_WEIGHT: 'weight',
			pango.ATTR_VARIANT: 'variant',
			pango.ATTR_STRETCH: 'stretch',
			pango.ATTR_SIZE: 'size',
			pango.ATTR_FOREGROUND: 'foreground',
			pango.ATTR_BACKGROUND: 'background',
			pango.ATTR_UNDERLINE: 'underline',
			pango.ATTR_STRIKETHROUGH: 'strikethrough',
			pango.ATTR_RISE: 'rise',
			pango.ATTR_SCALE: 'scale'
		}

	def empty(self):
		buf = self._text.get_buffer()
		return buf.get_start_iter().equal(buf.get_end_iter())

	def status(self, text=None):
		if self._status_label == None and text != None:
			self._status_label = gtk.Label('')
			self._status_label.modify_font(self._text.style.font_desc)
			self._status_label.modify_fg(gtk.STATE_NORMAL, self._text.style.text[gtk.STATE_NORMAL])
			self._status_label.show()
			self._status_label.set_alignment(0, 0.5)
			self._status_label.set_padding(10, 0)
			self._status_label.set_use_markup(True)

			self.ensure_button_bar()
			self._button_bar.pack_start(self._status_label, True, True, 0)

		if text != None:
			self._status_label.set_markup(text)
		elif self._status_label:
			self._status_label.destroy()

			if not self._button_bar and self.empty():
				self.destroy()

	def attrs_to_tags(self, attrs):
		buf = self._text.get_buffer()
		table = buf.get_tag_table()
		ret = []

		for attr in attrs:
			if not attr.type in self._attr_map:
				continue

			if attr.type == pango.ATTR_FOREGROUND or attr.type == pango.ATTR_BACKGROUND:
				value = attr.color
			else:
				value = attr.value

			tagname = str(attr.type) + ':' + str(value)

			tag = table.lookup(tagname)

			if not tag:
				tag = buf.create_tag(tagname)
				tag.set_property(self._attr_map[attr.type], value)

			ret.append(tag)

		return ret

	def add_lines(self, line, use_markup=False):
		buf = self._text.get_buffer()

		if not buf.get_start_iter().equal(buf.get_end_iter()):
			line = "\n" + line

		if not use_markup:
			buf.insert(buf.get_end_iter(), line)
			return

		try:
			ret = pango.parse_markup(line)
		except Exception, e:
			print 'Could not parse markup:', e
			buf.insert(buf.get_end_iter(), line)
			return

		piter = ret[0].get_iterator()
		text = ret[1]

		while piter:
			attrs = piter.get_attrs()
			begin, end = piter.range()

			tags = self.attrs_to_tags(attrs)
			buf.insert_with_tags(buf.get_end_iter(), text[begin:end], *tags)

			if not piter.next():
				break

	def toomany_lines(self):
		buf = self._text.get_buffer()
		piter = buf.get_start_iter()
		num = 0

		while self._text.forward_display_line(piter):
			num += 1

			if num > self.max_lines:
				return True

		return False

	def contents_changed(self):
		buf = self._text.get_buffer()

		if self.toomany_lines() and (self._vw.get_policy()[1] != gtk.POLICY_ALWAYS):
			self._vw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)

			layout = self._text.create_pango_layout('Some text to measure')
			extents = layout.get_pixel_extents()

			self._text.set_size_request(-1, extents[1][3] * self.max_lines)
		elif not self.toomany_lines() and (self._vw.get_policy()[1] == gtk.POLICY_ALWAYS):
			self._vw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
			self._text.set_size_request(-1, -1)

		if not self.toomany_lines():
			size = self.get_size()
			self.resize(size[0], 1)

	def ensure_button_bar(self):
		if not self._button_bar:
			self._button_bar = gtk.HBox(False, 3)
			self._button_bar.show()
			self._vbox.pack_start(self._button_bar, False, False, 0)

	def add_action(self, stock, callback, data=None):
		image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
		image.show()

		image.set_data('COMMANDER_ACTION_STOCK_ITEM', [stock, gtk.ICON_SIZE_MENU])

		self.ensure_button_bar()

		ev = gtk.EventBox()
		ev.set_visible_window(False)
		ev.add(image)
		ev.show()

		self._button_bar.pack_end(ev, False, False, 0)

		ev.connect('button-press-event', self.on_action_activate, callback, data)
		ev.connect('enter-notify-event', self.on_action_enter_notify)
		ev.connect('leave-notify-event', self.on_action_leave_notify)

		ev.connect_after('destroy', self.on_action_destroy)
		return ev

	def on_action_destroy(self, widget):
		if self._button_bar and len(self._button_bar.get_children()) == 0:
			self._button_bar.destroy()
			self._button_bar = None

	def on_action_enter_notify(self, widget, evnt):
		img = widget.get_child()
		img.set_state(gtk.STATE_PRELIGHT)
		widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))

		stock = img.get_data('COMMANDER_ACTION_STOCK_ITEM')
		pix = img.render_icon(stock[0], stock[1])
		img.set_from_pixbuf(pix)

	def on_action_leave_notify(self, widget, evnt):
		img = widget.get_child()
		img.set_state(gtk.STATE_NORMAL)
		widget.window.set_cursor(None)

		stock = img.get_data('COMMANDER_ACTION_STOCK_ITEM')
		pix = img.render_icon(stock[0], stock[1])
		img.set_from_pixbuf(pix)

	def on_action_activate(self, widget, evnt, callback, data):
		if data:
			callback(data)
		else:
			callback()

	def clear(self):
		self._text.get_buffer().set_text('')

	def on_text_expose(self, widget, evnt):
		if evnt.window != widget.get_window(gtk.TEXT_WINDOW_TEXT):
			return False

		ct = evnt.window.cairo_create()
		ct.save()

		area = evnt.area
		ct.rectangle(area.x, area.y, area.width, area.height)
		ct.clip()

		self.draw_background(ct, self._text, False)

		ct.restore()
		return False

	def on_text_realize(self, widget):
		self._text.get_window(gtk.TEXT_WINDOW_TEXT).set_back_pixmap(None, False)

	def attach(self):
		vwwnd = self._entry._view.get_window(gtk.TEXT_WINDOW_TEXT)
		origin = vwwnd.get_origin()
		geom = vwwnd.get_geometry()

		margin = 5

		self.realize()

		self.move(origin[0], origin[1] + geom[3] - self.allocation.height)
		self.resize(geom[2] - margin * 2, self.allocation.height)

	def on_text_insert_text(self, buf, piter, text, length):
		self.contents_changed()

	def on_text_delete_range(self, buf, start, end):
		self.contents_changed()

	def on_size_allocate(self, widget, allocation):
		vwwnd = self._entry._view.get_window(gtk.TEXT_WINDOW_TEXT)
		origin = vwwnd.get_origin()
		geom = vwwnd.get_geometry()

		self.move(origin[0] + (geom[2] - self.allocation.width) / 2, origin[1] + geom[3] - self.allocation.height)

	def on_expose(self, widget, evnt):
		ret = TransparentWindow.on_expose(self, widget, evnt)

		if ret:
			return True

		ct = evnt.window.cairo_create()
		ct.save()

		area = evnt.area
		ct.rectangle(area.x, area.y, area.width, area.height)
		ct.clip()

		color = self.background_color()

		self.background_shape(ct)

		ct.set_source_rgba(1 - color[0], 1 - color[1], 1 - color[2], 0.3)
		ct.stroke()

		ct.restore()
		return False

	def background_shape(self, ct):
		w = self.allocation.width
		h = self.allocation.height

		ct.set_line_width(1)
		radius = 10

		ct.move_to(0.5, h)

		if self.is_composited():
			ct.arc(radius + 0.5, radius, radius, math.pi, math.pi * 1.5)
			ct.arc(w - radius - 0.5, radius, radius, math.pi * 1.5, math.pi * 2)
		else:
			ct.line_to(0.5, 0)
			ct.line_to(w - 0.5, 0)

		ct.line_to(w - 0.5, h)

	def background_color(self):
		return self._entry.background_color()

	def on_text_size_allocate(self, widget, alloc):
		pass

