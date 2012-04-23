import gtk
import cairo

class TransparentWindow(gtk.Window):
	def __init__(self, lvl=gtk.WINDOW_TOPLEVEL):
		gtk.Window.__init__(self, lvl)

		self.set_decorated(False)
		self.set_app_paintable(True)
		self.set_skip_pager_hint(True)
		self.set_skip_taskbar_hint(True)
		self.set_events(gtk.gdk.ALL_EVENTS_MASK)

		self.set_rgba()

	def set_rgba(self):
		cmap = self.get_screen().get_rgba_colormap()

		if not cmap:
			return

		self.set_colormap(cmap)
		self.connect('realize', self.on_realize)
		self.connect('expose-event', self.on_expose)

	def on_realize(self, widget):
		self.window.set_back_pixmap(None, False)

	def background_color(self):
		return [0, 0, 0, 0.8]

	def background_shape(self, ct):
		ct.rectangle(0, 0, self.allocation.width, self.allocation.height)

	def draw_background(self, ct, widget=None, shape=True):
		if widget == None:
			widget = self

		ct.set_operator(cairo.OPERATOR_SOURCE)
		ct.rectangle(0, 0, widget.allocation.width, widget.allocation.height)
		ct.set_source_rgba(0, 0, 0, 0)

		if not shape:
			ct.fill_preserve()
		else:
			ct.fill()

		color = self.background_color()

		if shape:
			self.background_shape(ct)

		ct.set_source_rgba(color[0], color[1], color[2], color[3])
		ct.fill()

	def on_expose(self, widget, evnt):
		if not self.window:
			return

		ct = evnt.window.cairo_create()
		ct.save()

		area = evnt.area
		ct.rectangle(area.x, area.y, area.width, area.height)
		ct.clip()

		self.draw_background(ct)

		ct.restore()
		return False
