/*
 * pluma-show-tabbar-plugin.c
 *
 * Copyright (C) 2006 Steve Frécinaux
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
 *
 * $Id$
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "pluma-show-tabbar-plugin.h"

#include <glib/gi18n-lib.h>
#include <pluma/pluma-debug.h>


#define WINDOW_DATA_KEY	"PlumaShowTabbarWindowData"
#define MENU_PATH 	"/MenuBar/ViewMenu"
#define SETTINGS_BASE		"org.mate.pluma.plugins.showtabbar"
#define SETTINGS_KEY_TABBAR	"tabbar-visible"

#define PLUMA_SHOW_TABBAR_PLUGIN_GET_PRIVATE(object)	(G_TYPE_INSTANCE_GET_PRIVATE ((object), PLUMA_TYPE_SHOW_TABBAR_PLUGIN, PlumaShowTabbarPluginPrivate))

PLUMA_PLUGIN_REGISTER_TYPE (PlumaShowTabbarPlugin, pluma_show_tabbar_plugin)

struct _PlumaShowTabbarPluginPrivate
{
	GSettings	*settings;
};

typedef struct
{
	PlumaShowTabbarPlugin *plugin;
	GtkActionGroup *action_group;
	guint           ui_id;
	gulong		signal_handler_id;
} WindowData;

static void
pluma_show_tabbar_plugin_init (PlumaShowTabbarPlugin *plugin)
{
	pluma_debug_message (DEBUG_PLUGINS,
			     "PlumaShowTabbarPlugin initializing");

	plugin->priv = PLUMA_SHOW_TABBAR_PLUGIN_GET_PRIVATE (plugin);

	plugin->priv->settings = g_settings_new (SETTINGS_BASE);
}

static void
pluma_show_tabbar_plugin_dispose (GObject *object)
{
	PlumaShowTabbarPlugin *plugin = PLUMA_SHOW_TABBAR_PLUGIN (object);

	pluma_debug_message (DEBUG_PLUGINS,
			     "PlumaShowTabbar plugin disposing");

	if (plugin->priv->settings != NULL)
	{
		g_object_unref (plugin->priv->settings);
		plugin->priv->settings = NULL;
	}

	G_OBJECT_CLASS (pluma_show_tabbar_plugin_parent_class)->dispose (object);
}

static GtkNotebook *
get_notebook (PlumaWindow *window)
{
	GList *list;
	GtkContainer *container;
	GtkNotebook *notebook;

	g_return_val_if_fail (window != NULL, NULL);

	container = GTK_CONTAINER (gtk_bin_get_child (GTK_BIN (window)));
								/* VBox   */

	list = gtk_container_get_children (container);
	container = GTK_CONTAINER (g_list_nth_data (list, 2));	/* HPaned */
	g_list_free (list);

	list = gtk_container_get_children (container);
	container = GTK_CONTAINER (g_list_nth_data (list, 1));	/* VPaned */
	g_list_free (list);

	list = gtk_container_get_children (container);
	notebook = GTK_NOTEBOOK (g_list_nth_data (list, 0));	/* Notebook */
	g_list_free (list);

	return notebook;
}

static void
on_notebook_show_tabs_changed (GtkNotebook	*notebook,
			       GParamSpec	*pspec,
			       WindowData	*data)
{
	GtkAction *action;
	gboolean visible;

#if 0
	/* this works quite bad due to update_tabs_visibility in
	   pluma-notebook.c */
	visible = gtk_notebook_get_show_tabs (notebook);

	if (gtk_toggle_action_get_active (action) != visible)
		gtk_toggle_action_set_active (action, visible);
#endif

	action = gtk_action_group_get_action (data->action_group, "ShowTabbar");
	visible = gtk_toggle_action_get_active (GTK_TOGGLE_ACTION (action));

	/* this is intendend to avoid the PlumaNotebook to show the tabs again
	   (it does so everytime a new tab is added) */
	if (visible != gtk_notebook_get_show_tabs (notebook))
		gtk_notebook_set_show_tabs (notebook, visible);

	g_settings_set_boolean (data->plugin->priv->settings,
				SETTINGS_KEY_TABBAR, visible);
}

static void
on_view_tabbar_toggled (GtkToggleAction	*action,
			PlumaWindow	*window)
{
	gtk_notebook_set_show_tabs (get_notebook (window),
				    gtk_toggle_action_get_active (action));
}

static void
free_window_data (WindowData *data)
{
	g_return_if_fail (data != NULL);

	g_object_unref (data->action_group);
	g_slice_free (WindowData, data);
}

static void
impl_activate (PlumaPlugin *plugin,
	       PlumaWindow *window)
{
	GtkUIManager *manager;
	WindowData *data;
	GtkToggleAction *action;
	GtkNotebook *notebook;
	gboolean visible;

	pluma_debug (DEBUG_PLUGINS);

	data = g_slice_new (WindowData);
	data->plugin = PLUMA_SHOW_TABBAR_PLUGIN (plugin);

	visible = g_settings_get_boolean (data->plugin->priv->settings,
					  SETTINGS_KEY_TABBAR);

	notebook = get_notebook (window);

	gtk_notebook_set_show_tabs (notebook, visible);

	manager = pluma_window_get_ui_manager (window);

	data->action_group = gtk_action_group_new ("PlumaHideTabbarPluginActions");
	gtk_action_group_set_translation_domain (data->action_group,
						 GETTEXT_PACKAGE);

	action = gtk_toggle_action_new ("ShowTabbar",
					_("Tab_bar"),
					_("Show or hide the tabbar in the current window"),
					NULL);

	gtk_toggle_action_set_active (action, visible);

	g_signal_connect (action,
			  "toggled",
			  G_CALLBACK (on_view_tabbar_toggled),
			  window);

	gtk_action_group_add_action (data->action_group, GTK_ACTION (action));

	gtk_ui_manager_insert_action_group (manager, data->action_group, -1);

	data->ui_id = gtk_ui_manager_new_merge_id (manager);

	gtk_ui_manager_add_ui (manager,
			       data->ui_id,
			       MENU_PATH,
			       "ShowTabbar",
			       "ShowTabbar",
			       GTK_UI_MANAGER_MENUITEM,
			       TRUE);

	data->signal_handler_id =
		g_signal_connect (notebook,
				  "notify::show-tabs",
				  G_CALLBACK (on_notebook_show_tabs_changed),
				  data);

	g_object_set_data_full (G_OBJECT (window),
				WINDOW_DATA_KEY,
				data,
				(GDestroyNotify) free_window_data);
}

static void
impl_deactivate	(PlumaPlugin *plugin,
		 PlumaWindow *window)
{
	GtkUIManager *manager;
	WindowData *data;

	pluma_debug (DEBUG_PLUGINS);

	manager = pluma_window_get_ui_manager (window);

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	gtk_ui_manager_remove_ui (manager, data->ui_id);
	gtk_ui_manager_remove_action_group (manager, data->action_group);

	g_signal_handler_disconnect (get_notebook (window),
				     data->signal_handler_id);

	g_object_set_data (G_OBJECT (window), WINDOW_DATA_KEY, NULL);
}

static void
pluma_show_tabbar_plugin_class_init (PlumaShowTabbarPluginClass *klass)
{
	GObjectClass *object_class = G_OBJECT_CLASS (klass);
	PlumaPluginClass *plugin_class = PLUMA_PLUGIN_CLASS (klass);

	g_type_class_add_private (object_class, sizeof (PlumaShowTabbarPluginPrivate));

	object_class->dispose = pluma_show_tabbar_plugin_dispose;

	plugin_class->activate = impl_activate;
	plugin_class->deactivate = impl_deactivate;
}
