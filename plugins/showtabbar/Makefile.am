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

# MateConf Schemas

schemasdir	 = $(MATECONF_SCHEMA_FILE_DIR)
schemas_in_files = pluma-show-tabbar-plugin.schemas.in
schemas_DATA 	 = $(schemas_in_files:.schemas.in=.schemas)
@INTLTOOL_SCHEMAS_RULE@

if MATECONF_SCHEMAS_INSTALL
install-data-local:
	        if test -z "$(DESTDIR)" ; then \
	                for p in $(schemas_DATA) ; do \
	                        MATECONF_CONFIG_SOURCE=$(MATECONF_SCHEMA_CONFIG_SOURCE) $(MATECONFTOOL) --makefile-install-rule $$p ; \
	                done \
	        fi
else
install-data-local:
endif

EXTRA_DIST = $(schemas_in_files)

CLEANFILES = $(plugin_DATA) $(schemas_DATA)
DISTCLEANFILES = $(plugin_DATA) $(schemas_DATA)

-include $(top_srcdir)/git.mk
