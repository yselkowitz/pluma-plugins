/*
 * Copyright (C) 2008 Ignacio Casal Quinteiro <nacho.resa@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "pluma-drawspaces-plugin.h"

#include <glib/gi18n-lib.h>
#include <pluma/pluma-app.h>
#include <pluma/pluma-debug.h>
#include <pluma/pluma-window.h>
#include <pluma/pluma-view.h>
#include <pluma/pluma-tab.h>
#include <pluma/pluma-utils.h>

#define DRAWSPACES_SETTINGS_BASE   "org.mate.pluma.plugins.drawspaces"
#define SETTINGS_KEY_ENABLE        "enable"
#define SETTINGS_KEY_DRAW_TABS     "draw-tabs"
#define SETTINGS_KEY_DRAW_SPACES   "draw-spaces"
#define SETTINGS_KEY_DRAW_NEWLINE  "draw-newline"
#define SETTINGS_KEY_DRAW_NBSP     "draw-nbsp"
#define SETTINGS_KEY_DRAW_LEADING  "draw-leading"
#define SETTINGS_KEY_DRAW_TEXT     "draw-text"
#define SETTINGS_KEY_DRAW_TRAILING "draw-trailing"

#define UI_FILE "drawspaces.ui"

#define WINDOW_DATA_KEY "PlumaDrawspacesPluginWindowData"

#define PLUMA_DRAWSPACES_PLUGIN_GET_PRIVATE(object) \
				(G_TYPE_INSTANCE_GET_PRIVATE ((object),	\
				PLUMA_TYPE_DRAWSPACES_PLUGIN,		\
				PlumaDrawspacesPluginPrivate))


PLUMA_PLUGIN_REGISTER_TYPE (PlumaDrawspacesPlugin, pluma_drawspaces_plugin)

struct _PlumaDrawspacesPluginPrivate
{
	GSettings *settings;

	GtkSourceDrawSpacesFlags flags;
};

typedef struct
{
	GtkActionGroup *action_group;
	guint           ui_id;

	gboolean enable;
} WindowData;

typedef struct
{
	PlumaWindow *window;
	PlumaDrawspacesPlugin *plugin;
} ActionData;

typedef struct _DrawspacesConfigureDialog DrawspacesConfigureDialog;

struct _DrawspacesConfigureDialog
{
	GtkWidget *dialog;

	GtkWidget *draw_tabs;
	GtkWidget *draw_spaces;
	GtkWidget *draw_newline;
	GtkWidget *draw_nbsp;
	GtkWidget *draw_leading;
	GtkWidget *draw_text;
	GtkWidget *draw_trailing;
};

enum
{
	COLUMN_LABEL,
	COLUMN_LOCATION
};

static const gchar submenu [] = {
"<ui>"
"  <menubar name='MenuBar'>"
"    <menu name='ViewMenu' action='View'>"
"      <separator />"
"      <menuitem name='DrawSpacesMenu' action='DrawSpaces'/>"
"    </menu>"
"  </menubar>"
"</ui>"
};

static void draw_spaces_in_window (PlumaWindow *window, PlumaDrawspacesPlugin *plugin);

static void
free_window_data (WindowData *data)
{
	g_return_if_fail (data != NULL);

	g_slice_free (WindowData, data);
}

static void
free_action_data (gpointer data)
{
	g_slice_free (ActionData, data);
}

static void
on_active_toggled (GtkToggleAction *action,
		   ActionData *action_data)
{
	WindowData *data;
	gboolean value;

	data = (WindowData *) g_object_get_data (G_OBJECT (action_data->window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	value = gtk_toggle_action_get_active (action);
	data->enable = value;

	g_settings_set_boolean (action_data->plugin->priv->settings,
				SETTINGS_KEY_ENABLE, value);

	draw_spaces_in_window (action_data->window, action_data->plugin);
}

static const GtkToggleActionEntry action_entries[] =
{
	{ "DrawSpaces", NULL, N_("Show _White Space"), NULL,
	 N_("Show spaces and tabs"),
	 G_CALLBACK (on_active_toggled)},
};

static void
draw_spaces (PlumaDrawspacesPlugin *plugin)
{
	const GList *windows, *l;

	windows = pluma_app_get_windows (pluma_app_get_default ());

	for (l = windows; l != NULL; l = g_list_next (l))
		draw_spaces_in_window (l->data, plugin);
}

static void
on_settings_changed (GSettings *settings,
		     const gchar *key,
		     PlumaDrawspacesPlugin *plugin)
{
	gboolean value;

	value = g_settings_get_boolean (settings, key);

	if (strcmp (key, SETTINGS_KEY_DRAW_TABS) == 0)
	{
		if (value)
			plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_TAB;
		else
			plugin->priv->flags &= ~GTK_SOURCE_DRAW_SPACES_TAB;
	 }
	else if (strcmp (key, SETTINGS_KEY_DRAW_SPACES) == 0)
	{
		if (value)
			plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_SPACE;
		else
			plugin->priv->flags &= ~GTK_SOURCE_DRAW_SPACES_SPACE;
	}
	else if (strcmp (key, SETTINGS_KEY_DRAW_NEWLINE) == 0)
	{
		if (value)
			plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_NEWLINE;
		else
			plugin->priv->flags &= ~GTK_SOURCE_DRAW_SPACES_NEWLINE;
	}
	else if (strcmp (key, SETTINGS_KEY_DRAW_NBSP) == 0)
	{
		if (value)
			 plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_NBSP;
		else
			plugin->priv->flags &= ~GTK_SOURCE_DRAW_SPACES_NBSP;
	}
	else if (strcmp (key, SETTINGS_KEY_DRAW_LEADING) == 0)
	{
		if (value)
			plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_LEADING;
		else
			plugin->priv->flags &= ~GTK_SOURCE_DRAW_SPACES_LEADING;
	}
	else if (strcmp (key, SETTINGS_KEY_DRAW_TEXT) == 0)
	{
		if (value)
			plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_TEXT;
		else
			plugin->priv->flags &= ~GTK_SOURCE_DRAW_SPACES_TEXT;
	}
	else if (strcmp (key, SETTINGS_KEY_DRAW_TRAILING) == 0)
	{
		if (value)
			plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_TRAILING;
		else
			plugin->priv->flags &= ~GTK_SOURCE_DRAW_SPACES_TRAILING;
	}

	draw_spaces (plugin);
}

static void
pluma_drawspaces_plugin_init (PlumaDrawspacesPlugin *plugin)
{
	pluma_debug_message (DEBUG_PLUGINS, "PlumaDrawspacesPlugin initializing");

	plugin->priv = PLUMA_DRAWSPACES_PLUGIN_GET_PRIVATE (plugin);

	plugin->priv->settings = g_settings_new (DRAWSPACES_SETTINGS_BASE);

	g_signal_connect (plugin->priv->settings,
			  "changed",
			  G_CALLBACK (on_settings_changed),
			  plugin);
}

static void
pluma_drawspaces_plugin_dispose (GObject *object)
{
	PlumaDrawspacesPlugin *plugin = PLUMA_DRAWSPACES_PLUGIN (object);

	pluma_debug_message (DEBUG_PLUGINS, "PlumaDrawspacesPlugin disposing");

	if (plugin->priv->settings != NULL)
	{
		g_object_unref (G_OBJECT (plugin->priv->settings));
		plugin->priv->settings = NULL;
	}

	G_OBJECT_CLASS (pluma_drawspaces_plugin_parent_class)->dispose (object);
}

static void
draw_spaces_in_window (PlumaWindow *window,
		       PlumaDrawspacesPlugin *plugin)
{
	GList *views, *l;
	WindowData *data;

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	views = pluma_window_get_views (window);
	for (l = views; l != NULL; l = g_list_next (l))
	{
		gtk_source_view_set_draw_spaces (GTK_SOURCE_VIEW (l->data),
						 data->enable ? plugin->priv->flags : 0);
	}

	g_list_free (views);
}

static void
tab_added_cb (PlumaWindow *window,
	      PlumaTab *tab,
	      PlumaDrawspacesPlugin *plugin)
{
	PlumaView *view;
	WindowData *data;

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	if (data->enable)
	{
		view = pluma_tab_get_view (tab);

		gtk_source_view_set_draw_spaces (GTK_SOURCE_VIEW (view),
						 plugin->priv->flags);
	}
}

static void
get_config_options (WindowData *data,
		    PlumaDrawspacesPlugin *plugin)
{
	gboolean tabs, spaces, newline, nbsp, leading, text, trailing;

	data->enable = g_settings_get_boolean (plugin->priv->settings,
					       SETTINGS_KEY_ENABLE);

	tabs = g_settings_get_boolean (plugin->priv->settings,
				       SETTINGS_KEY_DRAW_TABS);

	spaces = g_settings_get_boolean (plugin->priv->settings,
					 SETTINGS_KEY_DRAW_SPACES);

	newline = g_settings_get_boolean (plugin->priv->settings,
					  SETTINGS_KEY_DRAW_NEWLINE);

	nbsp = g_settings_get_boolean (plugin->priv->settings,
				       SETTINGS_KEY_DRAW_NBSP);

	leading = g_settings_get_boolean (plugin->priv->settings,
					  SETTINGS_KEY_DRAW_LEADING);

	text = g_settings_get_boolean (plugin->priv->settings,
				       SETTINGS_KEY_DRAW_TEXT);

	trailing = g_settings_get_boolean (plugin->priv->settings,
					   SETTINGS_KEY_DRAW_TRAILING);

	if (tabs)
	{
		plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_TAB;
	}

	if (spaces)
	{
		plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_SPACE;
	}

	if (newline)
	{
		plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_NEWLINE;
	}

	if (nbsp)
	{
		plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_NBSP;
	}

	if (leading)
	{
		plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_LEADING;
	}

	if (text)
	{
		plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_TEXT;
	}

	if (trailing)
	{
		plugin->priv->flags |= GTK_SOURCE_DRAW_SPACES_TRAILING;
	}
}

static void
impl_activate (PlumaPlugin *plugin,
	       PlumaWindow *window)
{
	PlumaDrawspacesPlugin *ds_plugin;
	GtkUIManager *manager;
	GError *error = NULL;
	GtkAction *action;
	WindowData *data;
	ActionData *action_data;

	pluma_debug (DEBUG_PLUGINS);

	ds_plugin = PLUMA_DRAWSPACES_PLUGIN (plugin);

	data = g_slice_new (WindowData);
	action_data = g_slice_new (ActionData);

	action_data->window = window;
	action_data->plugin = ds_plugin;

	get_config_options (data, ds_plugin);

	manager = pluma_window_get_ui_manager (window);

	data->action_group = gtk_action_group_new ("PlumaDrawspacesPluginActions");
	gtk_action_group_set_translation_domain (data->action_group,
						 GETTEXT_PACKAGE);
	gtk_action_group_add_toggle_actions_full (data->action_group,
						  action_entries,
						  G_N_ELEMENTS (action_entries),
						  action_data,
						  (GDestroyNotify) free_action_data);

	/* Lets set the default value */
	action = gtk_action_group_get_action (data->action_group,
					      "DrawSpaces");
	g_signal_handlers_block_by_func (action, on_active_toggled, action_data);
	gtk_toggle_action_set_active (GTK_TOGGLE_ACTION (action),
				      data->enable);
	g_signal_handlers_unblock_by_func (action, on_active_toggled, action_data);

	gtk_ui_manager_insert_action_group (manager, data->action_group, -1);

	data->ui_id = gtk_ui_manager_add_ui_from_string (manager,
							 submenu,
							 -1,
							 &error);
	if (error)
	{
		g_warning ("%s", error->message);
		g_error_free (error);
	}

	g_object_set_data_full (G_OBJECT (window),
				WINDOW_DATA_KEY,
				data,
				(GDestroyNotify) free_window_data);

	if (data->enable)
	{
		draw_spaces_in_window (window, ds_plugin);
	}

	g_signal_connect (window, "tab-added",
			  G_CALLBACK (tab_added_cb), ds_plugin);
}

static void
impl_deactivate	(PlumaPlugin *plugin,
		 PlumaWindow *window)
{
	PlumaDrawspacesPlugin *ds_plugin = PLUMA_DRAWSPACES_PLUGIN (plugin);
	GtkUIManager *manager;
	WindowData *data;

	pluma_debug (DEBUG_PLUGINS);

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	manager = pluma_window_get_ui_manager (window);

	data->enable = FALSE;
	draw_spaces_in_window (window, ds_plugin);

	g_signal_handlers_disconnect_by_func (window, tab_added_cb, ds_plugin);

	gtk_ui_manager_remove_ui (manager, data->ui_id);
	gtk_ui_manager_remove_action_group (manager, data->action_group);

	g_object_set_data (G_OBJECT (window), WINDOW_DATA_KEY, NULL);
}

static void
dialog_destroyed (GObject *obj, gpointer dialog_pointer)
{
	pluma_debug (DEBUG_PLUGINS);

	g_slice_free (DrawspacesConfigureDialog, dialog_pointer);

	pluma_debug_message (DEBUG_PLUGINS, "END");
}

static DrawspacesConfigureDialog *
get_configuration_dialog (PlumaDrawspacesPlugin *plugin)
{
	DrawspacesConfigureDialog *dialog = NULL;
	gboolean ret;
	GtkWidget *error_widget;
	gchar *datadir;
	gchar *filename;

	gchar *root_objects[] = {
		"dialog_draw_spaces",
		NULL
	};

	dialog = g_slice_new (DrawspacesConfigureDialog);

	datadir = pluma_plugin_get_data_dir (PLUMA_PLUGIN (plugin));
	filename = g_build_filename (datadir, UI_FILE, NULL);

	ret = pluma_utils_get_ui_objects (filename,
					  root_objects,
					  &error_widget,
					  "dialog_draw_spaces", &dialog->dialog,
					  "check_button_draw_tabs", &dialog->draw_tabs,
					  "check_button_draw_spaces", &dialog->draw_spaces,
					  "check_button_draw_new_lines", &dialog->draw_newline,
					  "check_button_draw_nbsp", &dialog->draw_nbsp,
					  "check_button_draw_leading", &dialog->draw_leading,
					  "check_button_draw_text", &dialog->draw_text,
					  "check_button_draw_trailing", &dialog->draw_trailing,
					  NULL);

	g_free (datadir);
	g_free (filename);

	if (!ret)
	{
		GtkWidget *dialog_error;
		GtkWidget *content;

		dialog_error = gtk_dialog_new_with_buttons (_("Error dialog"),
							    NULL,
							    GTK_DIALOG_DESTROY_WITH_PARENT,
							    "_Close",
							    GTK_RESPONSE_CLOSE,
							    NULL);
		content = gtk_dialog_get_content_area (GTK_DIALOG (dialog_error));
		gtk_widget_show (error_widget);

		gtk_box_pack_start (GTK_BOX (content), error_widget, TRUE, TRUE, 0);
		gtk_widget_show (dialog_error);
		gtk_dialog_run (GTK_DIALOG (dialog_error));
		gtk_widget_destroy (dialog_error);
	}

	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (dialog->draw_tabs),
				      plugin->priv->flags & GTK_SOURCE_DRAW_SPACES_TAB);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (dialog->draw_spaces),
				      plugin->priv->flags & GTK_SOURCE_DRAW_SPACES_SPACE);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (dialog->draw_newline),
				      plugin->priv->flags & GTK_SOURCE_DRAW_SPACES_NEWLINE);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (dialog->draw_nbsp),
				      plugin->priv->flags & GTK_SOURCE_DRAW_SPACES_NBSP);

	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (dialog->draw_leading),
				      plugin->priv->flags & GTK_SOURCE_DRAW_SPACES_LEADING);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (dialog->draw_text),
				      plugin->priv->flags & GTK_SOURCE_DRAW_SPACES_TEXT);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (dialog->draw_trailing),
				      plugin->priv->flags & GTK_SOURCE_DRAW_SPACES_TRAILING);

	g_settings_bind (plugin->priv->settings,
			 SETTINGS_KEY_DRAW_TABS,
			 dialog->draw_tabs,
			 "active",
			 (G_SETTINGS_BIND_GET | G_SETTINGS_BIND_SET));
	g_settings_bind (plugin->priv->settings,
			SETTINGS_KEY_DRAW_SPACES,
			dialog->draw_spaces,
			"active",
			(G_SETTINGS_BIND_GET | G_SETTINGS_BIND_SET));
	g_settings_bind (plugin->priv->settings,
			SETTINGS_KEY_DRAW_NEWLINE,
			dialog->draw_newline,
			"active",
			(G_SETTINGS_BIND_GET | G_SETTINGS_BIND_SET));
	g_settings_bind (plugin->priv->settings,
			SETTINGS_KEY_DRAW_NBSP,
			dialog->draw_nbsp,
			"active",
			(G_SETTINGS_BIND_GET | G_SETTINGS_BIND_SET));
	g_settings_bind (plugin->priv->settings,
			SETTINGS_KEY_DRAW_LEADING,
			dialog->draw_leading,
			"active",
			(G_SETTINGS_BIND_GET | G_SETTINGS_BIND_SET));
	g_settings_bind (plugin->priv->settings,
			SETTINGS_KEY_DRAW_TEXT,
			dialog->draw_text,
			"active",
			(G_SETTINGS_BIND_GET | G_SETTINGS_BIND_SET));
	g_settings_bind (plugin->priv->settings,
			SETTINGS_KEY_DRAW_TRAILING,
			dialog->draw_trailing,
			"active",
			(G_SETTINGS_BIND_GET | G_SETTINGS_BIND_SET));

	g_signal_connect (dialog->dialog, "destroy",
			  G_CALLBACK (dialog_destroyed), dialog);

	return dialog;
}

static GtkWidget *
impl_create_configure_dialog (PlumaPlugin *plugin)
{
	DrawspacesConfigureDialog *dialog;

	dialog = get_configuration_dialog (PLUMA_DRAWSPACES_PLUGIN (plugin));

	g_signal_connect (dialog->dialog,
			  "response",
			  G_CALLBACK (gtk_widget_destroy),
			  dialog->dialog);

	return dialog->dialog;
}

static void
pluma_drawspaces_plugin_class_init (PlumaDrawspacesPluginClass *klass)
{
	GObjectClass *object_class = G_OBJECT_CLASS (klass);
	PlumaPluginClass *plugin_class = PLUMA_PLUGIN_CLASS (klass);

	g_type_class_add_private (object_class, sizeof (PlumaDrawspacesPluginPrivate));

	object_class->dispose = pluma_drawspaces_plugin_dispose;

	plugin_class->activate = impl_activate;
	plugin_class->deactivate = impl_deactivate;
	plugin_class->create_configure_dialog = impl_create_configure_dialog;
}
