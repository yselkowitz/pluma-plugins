# Drawspaces plugin
plugindir = $(PLUMA_PLUGINS_LIBS_DIR)

INCLUDES = \
	-I$(top_srcdir) 				\
	$(PLUMA_CFLAGS) 				\
	$(WARN_CFLAGS)					\
	$(DISABLE_DEPRECATED_CFLAGS)

plugin_LTLIBRARIES = libdrawspaces.la

libdrawspaces_la_SOURCES = \
	pluma-drawspaces-plugin.h				\
	pluma-drawspaces-plugin.c				

libdrawspaces_la_LDFLAGS = $(PLUGIN_LIBTOOL_FLAGS)
libdrawspaces_la_LIBADD = $(PLUMA_LIBS)

uidir = $(PLUMA_PLUGINS_DATA_DIR)/drawspaces
ui_DATA = drawspaces.ui

# Plugin Info

plugin_in_files = drawspaces.pluma-plugin.desktop.in

%.pluma-plugin: %.pluma-plugin.desktop.in $(INTLTOOL_MERGE) $(wildcard $(top_srcdir)/po/*po) ; $(INTLTOOL_MERGE) $(top_srcdir)/po $< $@ -d -u -c $(top_builddir)/po/.intltool-merge-cache

plugin_DATA = $(plugin_in_files:.pluma-plugin.desktop.in=.pluma-plugin)

schemasdir	 = $(MATECONF_SCHEMA_FILE_DIR)
schemas_in_files = pluma-drawspaces.schemas.in
schemas_DATA 	 = $(schemas_in_files:.schemas.in=.schemas)
@INTLTOOL_SCHEMAS_RULE@

if MATECONF_SCHEMAS_INSTALL
install-data-local:
	        if test -z "$(DESTDIR)" ; then \
	                for p in $(schemas_DATA) ; do \
	                        MATECONF_CONFIG_SOURCE=$(MATECONF_SCHEMA_CONFIG_SOURCE) $(MATECONFTOOL) --makefile-install-rule $(top_builddir)/plugins/drawspaces/$$p ; \
	                done \
	        fi
else
install-data-local:
endif

EXTRA_DIST = $(ui_DATA) $(schemas_in_files)

CLEANFILES = $(plugin_DATA) $(schemas_DATA)
DISTCLEANFILES = $(plugin_DATA) $(schemas_DATA)

-include $(top_srcdir)/git.mk
