# Advanced Editing plugin
plugindir = $(PLUMA_PLUGINS_LIBS_DIR)
supportdir = $(PLUMA_PLUGINS_DATA_DIR)/bookmarks

INCLUDES = \
	-I$(top_srcdir) 				\
	$(PLUMA_CFLAGS) 				\
	$(WARN_CFLAGS)					\
	$(DISABLE_DEPRECATED_CFLAGS)

plugin_LTLIBRARIES = libbookmarks.la

libbookmarks_la_SOURCES = \
	pluma-bookmarks-plugin.h			\
	pluma-bookmarks-plugin.c	

libbookmarks_la_LDFLAGS = $(PLUGIN_LIBTOOL_FLAGS)				\
libbookmarks_la_LDADD =	$(PLUMA_LIBS)

support_DATA = bookmark.png

# Plugin Info
plugin_in_files = bookmarks.pluma-plugin.desktop.in

%.pluma-plugin: %.pluma-plugin.desktop.in $(INTLTOOL_MERGE) $(wildcard $(top_srcdir)/po/*po) ; $(INTLTOOL_MERGE) $(top_srcdir)/po $< $@ -d -u -c $(top_builddir)/po/.intltool-merge-cache

BUILDFILES = $(plugin_in_files:.pluma-plugin.desktop.in=.pluma-plugin)

plugin_DATA = $(BUILDFILES)

EXTRA_DIST = $(support_DATA)

CLEANFILES = $(BUILDFILES) 
DISTCLEANFILES = $(BUILDFILES)

-include $(top_srcdir)/git.mk
