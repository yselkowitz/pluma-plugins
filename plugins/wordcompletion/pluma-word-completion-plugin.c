/*
 * Copyright (C) 2009 Ignacio Casal Quinteiro <icq@gnome.org>
 *               2009 Jesse van den Kieboom <jesse@gnome.org>
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

#include "pluma-word-completion-plugin.h"

#include <glib/gi18n-lib.h>
#include <pluma/pluma-debug.h>
#include <pluma/pluma-window.h>
#include <pluma/pluma-view.h>
#include <pluma/pluma-tab.h>
#include <gtksourceview/gtksourcecompletion.h>
#include <gtksourceview/completion-providers/words/gtksourcecompletionwords.h>

#define WINDOW_DATA_KEY "PlumaWordCompletionPluginWindowData"

PLUMA_PLUGIN_REGISTER_TYPE (PlumaWordCompletionPlugin, pluma_word_completion_plugin)

typedef struct
{
	GtkSourceCompletionWords *provider;
	gulong tab_added_id;
	gulong tab_removed_id;
} WindowData;

static void
free_window_data (WindowData *data)
{
	g_return_if_fail (data != NULL);

	g_object_unref (data->provider);
	g_slice_free (WindowData, data);
}

static void
pluma_word_completion_plugin_init (PlumaWordCompletionPlugin *plugin)
{
	pluma_debug_message (DEBUG_PLUGINS, "PlumaWordCompletionPlugin initializing");
}

static void
pluma_word_completion_plugin_dispose (GObject *object)
{
	G_OBJECT_CLASS (pluma_word_completion_plugin_parent_class)->dispose (object);
}

static void
add_view (WindowData    *data,
	  GtkSourceView *view)
{
	GtkSourceCompletion *completion;
	GtkTextBuffer *buf;

	completion = gtk_source_view_get_completion (view);
	buf = gtk_text_view_get_buffer (GTK_TEXT_VIEW (view));

	gtk_source_completion_add_provider (completion,
					    GTK_SOURCE_COMPLETION_PROVIDER (data->provider),
					    NULL);
	gtk_source_completion_words_register (data->provider,
					      buf);
}

static void
remove_view (WindowData    *data,
	     GtkSourceView *view)
{
	GtkSourceCompletion *completion;
	GtkTextBuffer *buf;

	completion = gtk_source_view_get_completion (view);
	buf = gtk_text_view_get_buffer (GTK_TEXT_VIEW (view));

	gtk_source_completion_remove_provider (completion,
					       GTK_SOURCE_COMPLETION_PROVIDER (data->provider),
					       NULL);
	gtk_source_completion_words_unregister (data->provider,
						buf);
}

static void
tab_added_cb (PlumaWindow *window,
	      PlumaTab    *tab,
	      gpointer     useless)
{
	PlumaView *view;
	WindowData *data;

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	view = pluma_tab_get_view (tab);

	add_view (data, GTK_SOURCE_VIEW (view));
}

static void
tab_removed_cb (PlumaWindow *window,
		PlumaTab    *tab,
		gpointer     useless)
{
	PlumaView *view;
	WindowData *data;

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	view = pluma_tab_get_view (tab);

	remove_view (data, GTK_SOURCE_VIEW (view));
}

static void
impl_activate (PlumaPlugin *plugin,
	       PlumaWindow *window)
{
	WindowData *data;
	GList *views, *l;

	pluma_debug (DEBUG_PLUGINS);

	data = g_slice_new (WindowData);
	data->provider = gtk_source_completion_words_new (_("Document Words"),
							  NULL);

	views = pluma_window_get_views (window);
	for (l = views; l != NULL; l = g_list_next (l))
	{
		add_view (data, GTK_SOURCE_VIEW (l->data));
	}

	g_object_set_data_full (G_OBJECT (window),
				WINDOW_DATA_KEY,
				data,
				(GDestroyNotify) free_window_data);

	data->tab_added_id =
		g_signal_connect (window, "tab-added",
				  G_CALLBACK (tab_added_cb),
				  NULL);
	data->tab_removed_id =
		g_signal_connect (window, "tab-removed",
				  G_CALLBACK (tab_removed_cb),
				  NULL);
}

static void
impl_deactivate	(PlumaPlugin *plugin,
		 PlumaWindow *window)
{
	WindowData *data;
	GList *views, *l;

	pluma_debug (DEBUG_PLUGINS);

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	views = pluma_window_get_views (window);
	for (l = views; l != NULL; l = g_list_next (l))
	{
		remove_view (data, GTK_SOURCE_VIEW (l->data));
	}

	g_signal_handler_disconnect (window, data->tab_added_id);
	g_signal_handler_disconnect (window, data->tab_removed_id);

	g_object_set_data (G_OBJECT (window), WINDOW_DATA_KEY, NULL);
}

static void
pluma_word_completion_plugin_class_init (PlumaWordCompletionPluginClass *klass)
{
	GObjectClass *object_class = G_OBJECT_CLASS (klass);
	PlumaPluginClass *plugin_class = PLUMA_PLUGIN_CLASS (klass);

	object_class->dispose = pluma_word_completion_plugin_dispose;

	plugin_class->activate = impl_activate;
	plugin_class->deactivate = impl_deactivate;
}
