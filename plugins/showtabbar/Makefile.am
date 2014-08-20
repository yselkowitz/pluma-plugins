# Show tabbar plugin
plugindir = $(PLUMA_PLUGINS_LIBS_DIR)

INCLUDES = \
	-I$(top_srcdir) 				\
	$(PLUMA_CFLAGS) 				\
	$(WARN_CFLAGS)					\
	$(DISABLE_DEPRECATED_CFLAGS)

plugin_LTLIBRARIES = libshowtabbar.la

libshowtabbar_la_SOURCES = \
	pluma-show-tabbar-plugin.h	\
	pluma-show-tabbar-plugin.c

libshowtabbar_la_LDFLAGS = $(PLUGIN_LIBTOOL_FLAGS)
libshowtabbar_la_LIBADD = $(PLUMA_LIBS)

# Plugin Info

plugin_in_files = showtabbar.pluma-plugin.desktop.in

%.pluma-plugin: %.pluma-plugin.desktop.in $(INTLTOOL_MERGE) $(wildcard $(top_srcdir)/po/*po) ; $(INTLTOOL_MERGE) $(top_srcdir)/po $< $@ -d -u -c $(top_builddir)/po/.intltool-merge-cache

plugin_DATA = $(plugin_in_files:.pluma-plugin.desktop.in=.pluma-plugin)

gsettings_SCHEMAS = org.mate.pluma.plugins.showtabbar.gschema.xml
@INTLTOOL_XML_NOMERGE_RULE@
@GSETTINGS_RULES@

convertdir = $(datadir)/MateConf/gsettings
convert_DATA = pluma-plugins-showtabbar.convert

EXTRA_DIST = $(convert_DATA)

CLEANFILES = $(plugin_DATA) $(gsettings_SCHEMAS)
DISTCLEANFILES = $(plugin_DATA) $(gsettings_SCHEMAS)

-include $(top_srcdir)/git.mk
