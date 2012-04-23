import commander.commands
import commander.commands.exceptions

__commander_module__ = True

def check_bookmark_plugin(window):
	if not window.get_message_bus().is_registered('/plugins/bookmarks', 'toggle'):
		raise commander.commands.exceptions.Execute("The bookmarks plugin is not installed, not active or too old")

def __default__(view, window):
	"""Commander interface to the bookmarks plugin: bookmark

This module provides an interface to the bookmarks plugin from pluma-plugins.
If installed and active, you can add/remove/toggle bookmarks using the
commander."""

	check_bookmark_plugin(window)
	window.get_message_bus().send('/plugins/bookmarks', 'toggle', view=view)

def add(view, window):
	"""Add bookmark: bookmark.add

Add bookmark on the current line. If there already is a bookmark on the current
line, nothing happens."""

	check_bookmark_plugin(window)
	window.get_message_bus().send('/plugins/bookmarks', 'add', view=view)

def remove(view, window):
	"""Remove bookmark: bookmark.remove

Remove bookmark from the current line. If there is no bookmark on the current
line, nothing happens."""

	check_bookmark_plugin(window)
	window.get_message_bus().send('/plugins/bookmarks', 'remove', view=view)

def toggle(view, window):
	"""Toggle bookmark: bookmark.toggle

Toggle bookmark on the current line."""

	check_bookmark_plugin(window)
	window.get_message_bus().send('/plugins/bookmarks', 'toggle', view=view)

def next(view, window):
	"""Goto next bookmark: bookmark.next

Jump to the next bookmark location"""

	check_bookmark_plugin(window)

	window.get_message_bus().send('/plugins/bookmarks', 'goto_next', view=view)

def previous(view, window):
	"""Goto previous bookmark: bookmark.previous

Jump to the previous bookmark location"""

	check_bookmark_plugin(window)

	window.get_message_bus().send('/plugins/bookmarks', 'goto_previous', view=view)
