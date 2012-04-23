import pluma
import gtk
from entry import Entry
from info import Info
from gpdefs import *

try:
    gettext.bindtextdomain(GETTEXT_PACKAGE, GP_LOCALEDIR)
    _ = lambda s: gettext.dgettext(GETTEXT_PACKAGE, s);
except:
    _ = lambda s: s

ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="EditMenu" action="Edit">
      <placeholder name="EditOps_5">
        <menuitem name="CommanderEditMode" action="CommanderModeAction"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class WindowHelper:
	def __init__(self, plugin, window):
		self._window = window
		self._plugin = plugin
		self._entry = None
		self._view = None

		self.install_ui()

	def install_ui(self):
		manager = self._window.get_ui_manager()

		self._action_group = gtk.ActionGroup("PlumaCommanderPluginActions")
		self._action_group.add_toggle_actions([('CommanderModeAction', None, _('Commander Mode'), '<Ctrl>period', _('Start commander mode'), self.on_commander_mode)])

		manager.insert_action_group(self._action_group, -1)
		self._merge_id = manager.add_ui_from_string(ui_str)

	def uninstall_ui(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._merge_id)
		manager.remove_action_group(self._action_group)

		manager.ensure_update()

	def deactivate(self):
		self.uninstall_ui()

		self._window = None
		self._plugin = None

	def update_ui(self):
		pass

	def on_commander_mode(self, action):
		view = self._window.get_active_view()

		if not view:
			return False

		if action.get_active():
			if not self._entry or view != self._view:
				self._entry = Entry(view)
				self._entry.connect('destroy', self.on_entry_destroy)

			self._entry.grab_focus()
			self._view = view
		elif self._entry:
			self._entry.destroy()
			self._view = None

		return True

	def on_entry_destroy(self, widget):
		self._entry = None
		self._action_group.get_action('CommanderModeAction').set_active(False)
