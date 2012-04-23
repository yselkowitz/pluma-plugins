# Word Completion plugin
plugindir = $(PLUMA_PLUGINS_LIBS_DIR)

INCLUDES = \
	-I$(top_srcdir) 				\
	$(PLUMA_CFLAGS) 				\
	$(WARN_CFLAGS)					\
	$(DISABLE_DEPRECATED_CFLAGS)

plugin_LTLIBRARIES = libwordcompletion.la

libwordcompletion_la_SOURCES = \
	pluma-word-completion-plugin.h				\
	pluma-word-completion-plugin.c				

libwordcompletion_la_LDFLAGS = $(PLUGIN_LIBTOOL_FLAGS)
libwordcompletion_la_LIBADD = $(PLUMA_LIBS)

# Plugin Info

plugin_in_files = wordcompletion.pluma-plugin.desktop.in

%.pluma-plugin: %.pluma-plugin.desktop.in $(INTLTOOL_MERGE) $(wildcard $(top_srcdir)/po/*po) ; $(INTLTOOL_MERGE) $(top_srcdir)/po $< $@ -d -u -c $(top_builddir)/po/.intltool-merge-cache

plugin_DATA = $(plugin_in_files:.pluma-plugin.desktop.in=.pluma-plugin)

CLEANFILES = $(plugin_DATA)
DISTCLEANFILES = $(plugin_DATA)

-include $(top_srcdir)/git.mk
