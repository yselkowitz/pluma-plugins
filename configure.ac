dnl Process this file with autoconf to produce a configure script.

AC_PREREQ(2.59)
 
m4_define(pluma_plugins_major_version,  1)
m4_define(pluma_plugins_minor_version,  16)
m4_define(pluma_plugins_micro_version,  0)
m4_define(pluma_plugins_version, pluma_plugins_major_version.pluma_plugins_minor_version.pluma_plugins_micro_version)

AC_INIT(pluma-plugins, pluma_plugins_version,
        http://github.com/yselkowitz/pluma-plugins/issues,
        pluma-plugins)

AC_CONFIG_SRCDIR([plugins])
AC_CONFIG_MACRO_DIR([m4])
AC_PREFIX_PROGRAM([pluma])

AM_INIT_AUTOMAKE([1.11 dist-xz no-dist-gzip tar-ustar])
AM_MAINTAINER_MODE
AM_SILENT_RULES([yes])
AC_CONFIG_HEADERS([config.h])

IT_PROG_INTLTOOL([0.35.0])

AC_DISABLE_STATIC
AC_PROG_LIBTOOL

AC_ISC_POSIX
AC_PROG_CC
AC_PROG_INSTALL
AC_PROG_MAKE_SET

# make sure we keep ACLOCAL_FLAGS around for maintainer builds to work
AC_SUBST(ACLOCAL_AMFLAGS, "$ACLOCAL_FLAGS -I m4")

dnl check for win32 platform
AC_MSG_CHECKING([for some Win32 platform])
case "$host" in
  *-*-mingw*|*-*-cygwin*)
    platform_win32=yes
    ;;
  *)
    platform_win32=no
    ;;
esac
AC_MSG_RESULT([$platform_win32])
AM_CONDITIONAL(PLATFORM_WIN32, test "$platform_win32" = "yes")

# ================================================================
# Gettext stuff.
# ================================================================

GETTEXT_PACKAGE=pluma-plugins
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE,"$GETTEXT_PACKAGE", [Gettext package])
AM_GLIB_GNU_GETTEXT

# ================================================================
# Start of pkg-config checks
# ================================================================

PKG_CHECK_MODULES(PLUMA, [
	glib-2.0 >= 2.26.0
	gio-2.0 >= 2.26.0
	gtk+-3.0
	gtksourceview-3.0
	pluma >= 1.16.0
])

# ================================================================
# GSettings
# ================================================================

GLIB_GSETTINGS

# ================================================================
# Plugins
# ================================================================

#FIXME
#PLUMA_HAS_PYTHON=1
#/FIXME

AC_MSG_CHECKING([which plugins to build])

ALL_PLUGINS="bookmarks showtabbar charmap drawspaces wordcompletion"
USEFUL_PLUGINS="bookmarks showtabbar charmap drawspaces wordcompletion"
DEFAULT_PLUGINS="bookmarks showtabbar charmap drawspaces wordcompletion"

PYTHON_ALL_PLUGINS="bracketcompletion codecomment colorpicker commander joinlines multiedit textsize sessionsaver smartspaces terminal synctex"
PYTHON_USEFUL_PLUGINS="bracketcompletion codecomment colorpicker commander joinlines multiedit textsize sessionsaver smartspaces synctex"
PYTHON_DEFAULT_PLUGINS="bracketcompletion codecomment colorpicker commander joinlines multiedit textsize sessionsaver smartspaces synctex"

DIST_PLUGINS="$ALL_PLUGINS $PYTHON_ALL_PLUGINS"

if test $PLUMA_HAS_PYTHON
then
	ALL_PLUGINS="$ALL_PLUGINS $PYTHON_ALL_PLUGINS"
	USEFUL_PLUGINS="$USEFUL_PLUGINS $PYTHON_USEFUL_PLUGINS"
	DEFAULT_PLUGINS="$DEFAULT_PLUGINS $PYTHON_DEFAULT_PLUGINS"
else
	AC_MSG_WARN([pluma compiled without python support, plugins $PYTHON_ALL_PLUGINS will not be available])
fi

# due to an autoconf bug, commas in the first arg to
# AS_HELP_STRING() cause problems.
#
# AS_HELP_STRING(--with-plugins=ext1,ext2,...,build the specified plugins)
AC_ARG_WITH([plugins],
[  --with-plugins=plugin1,plugin2,...
			  build the specified plugins. Available:
			  bracketcompletion, charmap, codecomment,
			  colorpicker, drawspaces, joinlines, multiedit,
			  textsize, showtabbar, sessionsaver, smartspaces,
			  terminal, wordcompletion, as well as the aliases
			  default, all, and really-all],
			  [plugins=$with_plugins],
			  [plugins="default"])

if test "x$with_plugins" = xyes
then
	plugins="default"
fi

need_python=no
explicit_plugins=
PLUGINS=
IFS="${IFS=	}"; plumapl_save_ifs="$IFS"; IFS=","
for pl in $plugins
do
	if echo "$ALL_PLUGINS" | egrep "(^| )$pl(\$| )" > /dev/null
	then
		PLUGINS="$PLUGINS $pl"
		explicit_plugins="$explicit_plugins $pl"
	elif test "x$pl" = "xdefault"
	then
		PLUGINS="$PLUGINS $DEFAULT_PLUGINS"
	elif test "x$pl" = "xall"
	then
		PLUGINS="$PLUGINS $USEFUL_PLUGINS"
	elif test "x$pl" = "xreally-all"
	then
		PLUGINS="$PLUGINS $ALL_PLUGINS"
	else
		AC_MSG_ERROR([the specified plugin $pl does not exist])
	fi
	
	if echo "$PYTHON_ALL_PLUGINS" | egrep "(^| )$pl(\$| )" > /dev/null
	then
		need_python=yes
	fi
done
IFS="$plumapl_save_ifs"

AC_MSG_RESULT([$PLUGINS])


# ================================================================
# Python
# ================================================================

AC_MSG_CHECKING([whether Python support is requested])
AC_ARG_ENABLE([python],
	      AS_HELP_STRING([--enable-python], [Enable python support]),
	      [enable_python=$enableval have_python=$enableval],
	      [enable_python=autodetect have_python=yes])
AC_MSG_RESULT([$enable_python])

if test "x$have_python" != "xno"
then
	AM_PATH_PYTHON([2.3], [], [no])
	if test "x$PYTHON" = "x:"
	then
		have_python=no
	fi
fi

if test "x$have_python" != "xno"
then
	AM_CHECK_PYTHON_HEADERS([], [have_python=no])
fi

if test "x$have_python" != "xno"
then
	PY_PREFIX=`$PYTHON -c 'import sys ; print sys.prefix'`
	PY_EXEC_PREFIX=`$PYTHON -c 'import sys ; print sys.exec_prefix'`
	PYTHON_LIBS="-lpython$PYTHON_VERSION"
	PYTHON_LIB_LOC="-L$PY_EXEC_PREFIX/lib/python$PYTHON_VERSION/config"
	PYTHON_CFLAGS="-I$PY_PREFIX/include/python$PYTHON_VERSION"
	PYTHON_MAKEFILE="$PY_EXEC_PREFIX/lib/python$PYTHON_VERSION/config/Makefile"
	PYTHON_LOCALMODLIBS=`sed -n -e 's/^LOCALMODLIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
	PYTHON_BASEMODLIBS=`sed -n -e 's/^BASEMODLIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
	PYTHON_OTHER_LIBS=`sed -n -e 's/^LIBS=\(.*\)/\1/p' $PYTHON_MAKEFILE`
	PYTHON_EXTRA_LIBS="$PYTHON_LOCALMODLIBS $PYTHON_BASEMODLIBS $PYTHON_OTHER_LIBS"
	AC_SUBST([PYTHON_LIBS])
	AC_SUBST([PYTHON_LIB_LOC])
	AC_SUBST([PYTHON_CFLAGS])
	AC_SUBST([PYTHON_EXTRA_LIBS])
fi

if test "x$have_python" != "xno"
then
	PYGOBJECT_REQUIRED=2.15.4
	PYGTK_REQUIRED=2.12.0
	PYGTKSOURCEVIEW_REQUIRED=2.2.0

	PKG_CHECK_MODULES([PYGTK], [
		pygobject-2.0 >= $PYGOBJECT_REQUIRED
		pygtk-2.0 >= $PYGTK_REQUIRED
		pygtksourceview-2.0 >= $PYGTKSOURCEVIEW_REQUIRED],
		[],[have_python=no])

	AC_SUBST([PYGTK_CFLAGS])
	AC_SUBST([PYGTK_LIBS])
fi

if test "x$have_python" != "xno"
then
	AC_MSG_CHECKING([for pygtk defs])
	PYGTK_DEFSDIR=`$PKG_CONFIG --variable=defsdir pygtk-2.0`
	AC_MSG_RESULT([$PYGTK_DEFSDIR])

	AC_MSG_CHECKING([for pygtk codegen])
	PYGTK_CODEGEN="$PYTHON `$PKG_CONFIG --variable=codegendir pygtk-2.0`/codegen.py"
	AC_MSG_RESULT([$PYGTK_CODEGEN])

	AC_MSG_CHECKING([for pygtk h2def])
	PYGTK_H2DEF="$PYTHON `$PKG_CONFIG --variable=codegendir pygtk-2.0`/h2def.py"
	AC_MSG_RESULT([$PYGTK_H2DEF])

	AC_SUBST([PYGTK_DEFSDIR])
	AC_SUBST([PYGTK_CODEGEN])
	AC_SUBST([PYGTK_H2DEF])

	dnl Check for -fno-strict-aliasing
	FLAGS="-fno-strict-aliasing"
	save_CFLAGS="$CFLAGS"
	CFLAGS="$CFLAGS $FLAGS"
	AC_MSG_CHECKING([whether [$]CC understands $FLAGS])
	AC_TRY_COMPILE([], [], [compiler_has_option=yes], [compiler_has_option=no])
	CFLAGS="$save_CFLAGS"
	AC_MSG_RESULT($compiler_has_option)
	if test $compiler_has_option = yes
	then
		NO_STRICT_ALIASING_CFLAGS="$FLAGS"
	fi
	AC_SUBST([NO_STRICT_ALIASING_CFLAGS])
fi

if test "x$have_python" != "xyes"
then
	if test "x$enable_python" = "xyes"
	then
		AC_MSG_ERROR([Python not found])
	elif test "x$enable_python" = "xautodetect"
	then
		enable_python=no
		AC_MSG_WARN([Python not found, disabling python support])
	fi
elif test "x$enable_python" != "xno"
then
	enable_python=yes
	AC_DEFINE([ENABLE_PYTHON],[1],[Define to compile with python support])
fi

AM_CONDITIONAL([ENABLE_PYTHON],[test "x$enable_python" = "xyes"])

disabled_plugins=
# ================================================================
# Plugin specific checks
# ================================================================
check_plugin_defined() {
	if echo "$2" | egrep "\b($1)\b" > /dev/null;
	then
		return 1
	else
		return 0
	fi
}

plugin_defined() {
	check_plugin_defined "$1" "$PLUGINS"
	return $?
}

plugin_defined_explicit() {
	check_plugin_defined "$1" "$explicit_plugins"
	return $?
}

undef_plugin() {
	if test -z "$disabled_plugins"
	then
		disabled_plugins="$1 ($2)"
	else
		disabled_plugins="$disabled_plugins, $1 ($2)"
	fi
	
	PLUGINS=$(echo "$PLUGINS" | sed -e "s/[[^a-zA-Z0-9_]]$1[[ \t\r\n\f]]\{1,\}/ /" -e "s/[[^a-zA-Z0-9_]]$1$//" -e "s/^$1[[ \t\r\n\f]]\{1,\}//")
}

# ================================================================
# disable all python plugins if there is no python support
# ================================================================
if test "x$enable_python" = "xno"
then
	for pl in $PYTHON_ALL_PLUGINS
	do
		undef_plugin "$pl" "no python support"
	done
fi

# ================================================================
# gucharmap
# ================================================================
plugin_defined charmap
if test "$?" = 1
then
	PKG_CHECK_MODULES([GUCHARMAP],
		[gucharmap-2.90],
		[have_gucharmap=yes],[have_gucharmap=no])

	AC_SUBST([GUCHARMAP_CFLAGS])
	AC_SUBST([GUCHARMAP_LIBS])

	if test "$have_gucharmap" = "no"; then
		plugin_defined_explicit charmap
		if test "$?" = 1
		then
			AC_MSG_ERROR([gucharmap could not be found, needed to built charmap plugin])
		else
			AC_MSG_WARN(gucharmap could not be found, charmap plugin will be disabled])
			undef_plugin charmap "libgucharmap not found"
		fi
	fi
fi

# ================================================================
# Synctex (dbus-python)
# ================================================================
plugin_defined synctex
if test "$?" = 1
then
	DBUSPYTHON_REQUIRED=0.82
	PKG_CHECK_MODULES([DBUSPYTHON],
		[dbus-python >= $DBUSPYTHON_REQUIRED],
		[have_synctex=yes],[have_synctex=no])

	AC_SUBST([DBUS_PYTHON_CFLAGS])
	AC_SUBST([DBUS_PYTHON_LIBS])

	if test "x$have_synctex" = "xno"; then
		plugin_defined_explicit synctex
		if test "$?" = 1
		then
			AC_MSG_ERROR([dbus-python could not be found, needed for synctex plugin])
		else
			AC_MSG_WARN([dbus-python could not be found, synctex plugin will be disabled])
			undef_plugin synctex "dbus-python not found"
		fi
	fi
fi

# ================================================================
# Terminal plugin vte check
# ================================================================
plugin_defined terminal
if test "$?" = 1
then
	PYVTE_REQUIRED=0.19.4
	PKG_CHECK_MODULES([PYVTE],
		[pyvte >= $PYVTE_REQUIRED],
		[have_pyvte=yes],[have_pyvte=no])

	AC_SUBST([PYVTE_CFLAGS])
	AC_SUBST([PYVTE_LIBS])

	if test "x$have_pyvte" = "xno";	then
		plugin_defined_explicit terminal
		if test "$?" = 1
		then
			AC_MSG_ERROR([pyvte could not be found, needed to built terminal plugin])
		else
			AC_MSG_WARN([pyvte could not be found, terminal plugin will be disabled])
			undef_plugin terminal "pyvte not found"
		fi
	fi
fi

if test -z "$disabled_plugins"
then
	disabled_plugins="none"
fi

PLUGINS=$(echo $PLUGINS | tr ' ' '\n' | sort | uniq | tr '\n' ' ')
AC_SUBST([DIST_PLUGINS])
AC_SUBST([BUILD_PLUGINS],[$PLUGINS])

# ================================================================
# Misc
# ================================================================
AC_PATH_PROG(GLIB_GENMARSHAL, glib-genmarshal)
			      
#MATE_COMPILE_WARNINGS(yes)

AC_ARG_ENABLE(deprecations,
              [AC_HELP_STRING([--enable-deprecations],
                              [warn about deprecated usages [default=no]])],,
              [enable_deprecations=no])

if test "x$enable_deprecations" = "xyes"
then
	DISABLE_DEPRECATED_CFLAGS="\
		-DG_DISABLE_DEPRECATED		\
		-DGDK_DISABLE_DEPRECATED	\
		-DGTK_DISABLE_DEPRECATED	\
		-DGDK_PIXBUF_DISABLE_DEPRECATED	\
		-DMATE_DISABLE_DEPRECATED"
	AC_SUBST(DISABLE_DEPRECATED_CFLAGS)
fi

if test "$platform_win32" = yes; then
	PLUGIN_LIBTOOL_FLAGS="-module -avoid-version -no-undefined"
else
	PLUGIN_LIBTOOL_FLAGS="-module -avoid-version"
fi
AC_SUBST(PLUGIN_LIBTOOL_FLAGS)

PLUMA_PLUGINS_LIBS_DIR="$libdir/pluma/plugins"
AC_SUBST(PLUMA_PLUGINS_LIBS_DIR)

PLUMA_PLUGINS_DATA_DIR="$datadir/pluma/plugins"
AC_SUBST(PLUMA_PLUGINS_DATA_DIR)

AC_CONFIG_FILES([
Makefile
plugins/gpdefs.py
plugins/Makefile
plugins/bookmarks/Makefile
plugins/bookmarks/bookmarks.pluma-plugin.desktop.in
plugins/bracketcompletion/Makefile
plugins/bracketcompletion/bracketcompletion.pluma-plugin.desktop.in
plugins/charmap/Makefile
plugins/charmap/charmap.pluma-plugin.desktop.in
plugins/codecomment/Makefile
plugins/codecomment/codecomment.pluma-plugin.desktop.in
plugins/colorpicker/Makefile
plugins/colorpicker/colorpicker.pluma-plugin.desktop.in
plugins/commander/Makefile
plugins/commander/commander.pluma-plugin.desktop.in
plugins/commander/commander/Makefile
plugins/commander/commander/commands/Makefile
plugins/commander/modules/Makefile
plugins/commander/modules/find/Makefile
plugins/drawspaces/Makefile
plugins/drawspaces/drawspaces.pluma-plugin.desktop.in
plugins/drawspaces/org.mate.pluma.plugins.drawspaces.gschema.xml.in
plugins/joinlines/Makefile
plugins/joinlines/joinlines.pluma-plugin.desktop.in
plugins/multiedit/Makefile
plugins/multiedit/multiedit/Makefile
plugins/multiedit/multiedit.pluma-plugin.desktop.in
plugins/textsize/Makefile
plugins/textsize/textsize/Makefile
plugins/textsize/textsize.pluma-plugin.desktop.in
plugins/sessionsaver/Makefile
plugins/sessionsaver/sessionsaver.pluma-plugin.desktop.in
plugins/showtabbar/Makefile
plugins/showtabbar/showtabbar.pluma-plugin.desktop.in
plugins/showtabbar/org.mate.pluma.plugins.showtabbar.gschema.xml.in
plugins/smartspaces/Makefile
plugins/smartspaces/smartspaces.pluma-plugin.desktop.in
plugins/terminal/Makefile
plugins/terminal/terminal.pluma-plugin.desktop.in
plugins/wordcompletion/Makefile
plugins/wordcompletion/wordcompletion.pluma-plugin.desktop.in
plugins/synctex/Makefile
plugins/synctex/synctex/Makefile
plugins/synctex/synctex.pluma-plugin.desktop.in
po/Makefile.in])

AC_OUTPUT

echo "

Configuration:

	Source code location:   ${srcdir}
	Compiler:               ${CC}
	Prefix:			${prefix}
	Python Plugins Support: $enable_python
	Plugins:                $PLUGINS
	
	Disabled plugins:       $disabled_plugins

Note: you have to install these plugins into the same prefix as your pluma
installation (probably /usr if you're using your distro packages, /usr/local
if you have compiled it on your own).
"

