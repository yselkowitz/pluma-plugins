# Session Saver Plugin

plugindir = $(PLUMA_PLUGINS_LIBS_DIR)
plugin_in_files = sessionsaver.pluma-plugin.desktop.in
%.pluma-plugin: %.pluma-plugin.desktop.in $(INTLTOOL_MERGE) $(wildcard $(top_srcdir)/po/*po) ; $(INTLTOOL_MERGE) $(top_srcdir)/po $< $@ -d -u -c $(top_builddir)/po/.intltool-merge-cache

sessionsaverdir=$(plugindir)/sessionsaver
sessionsaver_PYTHON = __init__.py store.py dialogs.py

uidir=$(PLUMA_PLUGINS_DATA_DIR)/sessionsaver
ui_DATA = sessionsaver.ui

plugin_DATA = $(plugin_in_files:.pluma-plugin.desktop.in=.pluma-plugin)

EXTRA_DIST = $(ui_DATA)

CLEANFILES = $(plugin_DATA)
DISTCLEANFILES = $(plugin_DATA)

-include $(top_srcdir)/git.mk
