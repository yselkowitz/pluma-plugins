/*
 * pluma-bookmarks-plugin.c - Bookmarking for pluma
 *
 * Copyright (C) 2008 Jesse van den Kieboom
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

#include "pluma-bookmarks-plugin.h"

#include <stdlib.h>	/* atoi */
#include <glib/gi18n-lib.h>
#include <gtk/gtk.h>
#include <gtksourceview/gtksource.h>
#include <pluma/pluma-debug.h>
#include <pluma/pluma-window.h>
#include <pluma/pluma-panel.h>
#include <pluma/pluma-document.h>
#include <pluma/pluma-prefs-manager.h>

#define WINDOW_DATA_KEY	"PlumaBookmarksPluginWindowData"

#define PLUMA_BOOKMARKS_PLUGIN_GET_PRIVATE(object) \
				(G_TYPE_INSTANCE_GET_PRIVATE ((object),	\
				PLUMA_TYPE_BOOKMARKS_PLUGIN,		\
				PlumaBookmarksPluginPrivate))

#define BOOKMARKS_DATA(window) ((WindowData *)(g_object_get_data (G_OBJECT (window), WINDOW_DATA_KEY)))

#define BOOKMARK_CATEGORY "PlumaBookmarksPluginBookmark"
#define BOOKMARK_PRIORITY 1

#define INSERT_DATA_KEY "PlumaBookmarksInsertData"
#define METADATA_ATTR "metadata::pluma-bookmarks"

#define MESSAGE_OBJECT_PATH "/plugins/bookmarks"
#define BUS_CONNECT(bus, name, data) pluma_message_bus_connect(bus, MESSAGE_OBJECT_PATH, #name, (PlumaMessageCallback)  message_##name##_cb, data, NULL)

typedef struct
{
	GtkSourceMark *bookmark;
	GtkTextMark *mark;
} InsertTracker;

typedef struct
{
	GSList *trackers;
	guint user_action;
} InsertData;

static void on_style_scheme_notify		(GObject     *object,
						 GParamSpec  *pspec,
						 PlumaView   *view);

static void on_delete_range			(GtkTextBuffer *buffer,
						 GtkTextIter   *start,
						 GtkTextIter   *end,
						 gpointer       user_data);

static void on_insert_text_before		(GtkTextBuffer *buffer,
						 GtkTextIter   *location,
						 gchar         *text,
						 gint		len,
						 InsertData    *data);

static void on_begin_user_action		(GtkTextBuffer *buffer,
						 InsertData    *data);

static void on_end_user_action			(GtkTextBuffer *buffer,
						 InsertData    *data);

static void on_toggle_bookmark_activate 	(GtkAction   *action,
						 PlumaWindow *window);
static void on_next_bookmark_activate 		(GtkAction   *action,
						 PlumaWindow *window);
static void on_previous_bookmark_activate 	(GtkAction   *action,
						 PlumaWindow *window);
static void on_tab_added 			(PlumaWindow *window,
						 PlumaTab    *tab,
						 PlumaPlugin *plugin);
static void on_tab_removed 			(PlumaWindow *window,
						 PlumaTab    *tab,
						 PlumaPlugin *plugin);

static void add_bookmark (GtkSourceBuffer *buffer, GtkTextIter *iter);
static void remove_bookmark (GtkSourceBuffer *buffer, GtkTextIter *iter);
static void toggle_bookmark (GtkSourceBuffer *buffer, GtkTextIter *iter);

typedef struct
{
	GtkActionGroup * action_group;
	guint ui_id;
} WindowData;

PLUMA_PLUGIN_REGISTER_TYPE (PlumaBookmarksPlugin, pluma_bookmarks_plugin)

static void
pluma_bookmarks_plugin_init (PlumaBookmarksPlugin *plugin)
{
	pluma_debug_message (DEBUG_PLUGINS, "PlumaBookmarksPlugin initializing");
}

static void
pluma_bookmarks_plugin_finalize (GObject *object)
{
	pluma_debug_message (DEBUG_PLUGINS, "PlumaBookmarksPlugin finalizing");

	G_OBJECT_CLASS (pluma_bookmarks_plugin_parent_class)->finalize (object);
}

static void
free_window_data (WindowData *data)
{
	g_slice_free (WindowData, data);
}

static void
free_insert_data (InsertData *data)
{
	g_slice_free (InsertData, data);
}

static GtkActionEntry const action_entries[] = {
	{"ToggleBookmark", NULL, N_("Toggle Bookmark"), "<Control><Alt>B",
	 N_("Toggle bookmark status of the current line"),
	 G_CALLBACK (on_toggle_bookmark_activate)},
	{"NextBookmark", NULL, N_("Goto Next Bookmark"), "<Control>B",
	 N_("Goto the next bookmark"),
	 G_CALLBACK (on_next_bookmark_activate)},
	{"PreviousBookmark", NULL, N_("Goto Previous Bookmark"), "<Control><Shift>B",
	 N_("Goto the previous bookmark"),
	 G_CALLBACK (on_previous_bookmark_activate)}
};

static gchar const uidefinition[] = ""
"<ui>"
"  <menubar name='MenuBar'>"
"    <menu name='EditMenu' action='Edit'>"
"      <placeholder name='EditOps_6'>"
"        <menuitem action='ToggleBookmark'/>"
"        <menuitem action='PreviousBookmark'/>"
"        <menuitem action='NextBookmark'/>"
"      </placeholder>"
"    </menu>"
"  </menubar>"
"</ui>";

static void
install_menu (PlumaWindow *window)
{
	GtkUIManager *manager;
	WindowData *data = BOOKMARKS_DATA (window);
	GError *error = NULL;

	manager = pluma_window_get_ui_manager (window);
	data->action_group = gtk_action_group_new ("PlumaBookmarksPluginActions");

	gtk_action_group_set_translation_domain (data->action_group,
						 GETTEXT_PACKAGE);

	gtk_action_group_add_actions (data->action_group,
				      action_entries,
				      G_N_ELEMENTS (action_entries),
				      window);

	gtk_ui_manager_insert_action_group (manager, data->action_group, -1);
	data->ui_id = gtk_ui_manager_add_ui_from_string (manager, uidefinition, -1, &error);

	if (!data->ui_id)
	{
		g_warning ("Could not load UI: %s", error->message);
		g_error_free (error);
	}
}

static void
uninstall_menu (PlumaWindow *window)
{
	WindowData *data = BOOKMARKS_DATA (window);
	GtkUIManager *manager;

	manager = pluma_window_get_ui_manager (window);

	gtk_ui_manager_remove_ui (manager, data->ui_id);
	gtk_ui_manager_remove_action_group (manager, data->action_group);

	g_object_unref (data->action_group);
}

static void
disable_bookmarks (PlumaView *view)
{
	GtkTextIter start;
	GtkTextIter end;
	GtkTextBuffer *buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (view));
	gpointer data;

	gtk_source_view_set_show_line_marks (GTK_SOURCE_VIEW (view), FALSE);

	gtk_text_buffer_get_bounds (buffer, &start, &end);
	gtk_source_buffer_remove_source_marks (GTK_SOURCE_BUFFER (buffer),
					       &start,
					       &end,
					       BOOKMARK_CATEGORY);

	g_signal_handlers_disconnect_by_func (buffer, on_style_scheme_notify, view);
	g_signal_handlers_disconnect_by_func (buffer, on_delete_range, NULL);

	data = g_object_get_data (G_OBJECT (buffer), INSERT_DATA_KEY);

	g_signal_handlers_disconnect_by_func (buffer, on_insert_text_before, data);
	g_signal_handlers_disconnect_by_func (buffer, on_begin_user_action, data);
	g_signal_handlers_disconnect_by_func (buffer, on_end_user_action, data);

	g_object_set_data (G_OBJECT (buffer), INSERT_DATA_KEY, NULL);
}

static GdkPixbuf *
get_bookmark_pixbuf (PlumaPlugin *plugin)
{
	gchar *datadir;
	gchar *iconpath;
	GdkPixbuf *pixbuf;

	datadir = pluma_plugin_get_data_dir (plugin);
	iconpath = g_build_filename (datadir, "bookmark.png", NULL);
	pixbuf = gdk_pixbuf_new_from_file (iconpath, NULL);

	g_free (datadir);
	g_free (iconpath);

	return pixbuf;
}

static void
update_background_color (GtkSourceMarkAttributes *attrs, GtkSourceBuffer *buffer)
{
	GtkSourceStyleScheme *scheme;
	GtkSourceStyle *style;

	scheme = gtk_source_buffer_get_style_scheme (buffer);
	style = gtk_source_style_scheme_get_style (scheme, "search-match");

	if (style)
	{
		gboolean bgset;
		gchar *bg;

		g_object_get (style, "background-set", &bgset, "background", &bg, NULL);

		if (bgset)
		{
			GdkRGBA color;
			gdk_rgba_parse (&color, bg);
			gtk_source_mark_attributes_set_background (attrs, &color);
			g_free (bg);

			return;
		}
	}

	gtk_source_mark_attributes_set_background (attrs, NULL);
}

static void
enable_bookmarks (PlumaView   *view,
		  PlumaPlugin *plugin)
{
	GdkPixbuf *pixbuf;

	pixbuf = get_bookmark_pixbuf (plugin);

	/* Make sure the category pixbuf is set */
	if (pixbuf)
	{
		GtkSourceMarkAttributes *attrs;
		GtkTextBuffer *buffer;
		InsertData *data;

		attrs = gtk_source_mark_attributes_new ();
		buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (view));

		update_background_color (attrs, GTK_SOURCE_BUFFER(buffer));
		gtk_source_mark_attributes_set_pixbuf (attrs, pixbuf);
		g_object_unref (pixbuf);

		gtk_source_view_set_mark_attributes (GTK_SOURCE_VIEW (view),
						     BOOKMARK_CATEGORY,
						     attrs,
						     BOOKMARK_PRIORITY);

		gtk_source_view_set_show_line_marks (GTK_SOURCE_VIEW (view), TRUE);

		g_signal_connect (buffer,
				  "notify::style-scheme",
				  G_CALLBACK (on_style_scheme_notify),
				  view);

		g_signal_connect_after (buffer,
				        "delete-range",
				        G_CALLBACK (on_delete_range),
				        NULL);

		data = g_slice_new0 (InsertData);

		g_object_set_data_full (G_OBJECT (buffer),
					INSERT_DATA_KEY,
					data,
					(GDestroyNotify) free_insert_data);

		g_signal_connect (buffer,
				  "insert-text",
				  G_CALLBACK (on_insert_text_before),
				  data);

		g_signal_connect (buffer,
				  "begin-user-action",
				  G_CALLBACK (on_begin_user_action),
				  data);

		g_signal_connect (buffer,
				  "end-user-action",
				  G_CALLBACK (on_end_user_action),
				  data);

	}
	else
	{
		g_warning ("Could not set bookmark icon!");
	}
}

static void
load_bookmarks (PlumaView *view,
		gchar    **bookmarks)
{
	GtkSourceBuffer *buf;
	GtkTextIter iter;
	gint tot_lines;
	gint i;

	buf = GTK_SOURCE_BUFFER (gtk_text_view_get_buffer (GTK_TEXT_VIEW (view)));

	gtk_text_buffer_get_end_iter (GTK_TEXT_BUFFER (buf), &iter);
	tot_lines = gtk_text_iter_get_line (&iter);

	for (i = 0; bookmarks != NULL && bookmarks[i] != NULL; i++)
	{
		gint line;

		line = atoi (bookmarks[i]);

		if (line >= 0 && line < tot_lines)
		{
			GSList *marks;

			gtk_text_buffer_get_iter_at_line (GTK_TEXT_BUFFER (buf),
							  &iter, line);

			marks = gtk_source_buffer_get_source_marks_at_iter (buf, &iter,
									    BOOKMARK_CATEGORY);

			if (marks == NULL)
			{
				/* Add new bookmark */
				gtk_source_buffer_create_source_mark (buf,
								      NULL,
								      BOOKMARK_CATEGORY,
								      &iter);
			}
			else
			{
				g_slist_free (marks);
			}
		}
	}
}

static void
load_bookmark_metadata (PlumaView *view)
{
	PlumaDocument *doc;
	gchar *bookmarks_attr;

	doc = PLUMA_DOCUMENT (gtk_text_view_get_buffer (GTK_TEXT_VIEW (view)));
	bookmarks_attr = pluma_document_get_metadata (doc, METADATA_ATTR);

	if (bookmarks_attr != NULL)
	{
		gchar **bookmarks;

		bookmarks = g_strsplit (bookmarks_attr, ",", -1);
		g_free (bookmarks_attr);

		load_bookmarks (view, bookmarks);

		g_strfreev (bookmarks);
	}
}

typedef gboolean (*IterSearchFunc)(GtkSourceBuffer *buffer, GtkTextIter *iter, const gchar *category);
typedef void (*CycleFunc)(GtkTextBuffer *buffer, GtkTextIter *iter);

static void
goto_bookmark (PlumaWindow    *window,
               GtkSourceView  *view,
               GtkTextIter    *iter,
	       IterSearchFunc  func,
	       CycleFunc       cycle_func)
{
	GtkTextBuffer *buffer;
	GtkTextIter at;
	GtkTextMark *insert;
	GtkTextIter end;

	if (view == NULL)
	{
		view = GTK_SOURCE_VIEW (pluma_window_get_active_view (window));
	}

	if (view == NULL)
	{
		return;
	}

	buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (view));

	if (iter == NULL)
	{
		gtk_text_buffer_get_iter_at_mark (buffer,
		                                  &at,
		                                  gtk_text_buffer_get_insert (buffer));
	}
	else
	{
		at = *iter;
	}

	/* Move the iter to the beginning of the line, where the bookmarks are */
	gtk_text_iter_set_line_offset (&at, 0);

	/* Try to find the next bookmark */
	if (!func (GTK_SOURCE_BUFFER (buffer), &at, BOOKMARK_CATEGORY))
	{
		GSList *marks;

		/* cycle through */
		cycle_func (buffer, &at);
		gtk_text_iter_set_line_offset (&at, 0);

		marks = gtk_source_buffer_get_source_marks_at_iter (GTK_SOURCE_BUFFER (buffer),
		                                                    &at,
		                                                    BOOKMARK_CATEGORY);

		if (!marks && !func (GTK_SOURCE_BUFFER (buffer), &at, BOOKMARK_CATEGORY))
		{
			return;
		}

		g_slist_free (marks);
	}

	end = at;

	if (!gtk_text_iter_forward_visible_line (&end))
	{
		gtk_text_buffer_get_end_iter (buffer, &end);
	}
	else
	{
		gtk_text_iter_backward_char (&end);
	}

	gtk_text_buffer_select_range (buffer, &at, &end);
	gtk_text_view_scroll_to_iter (GTK_TEXT_VIEW (view), &at, 0.3, FALSE, 0, 0);
}

static void
message_get_view_iter (PlumaWindow    *window,
                       PlumaMessage   *message,
                       GtkSourceView **view,
                       GtkTextIter    *iter)
{
	if (pluma_message_has_key (message, "view"))
	{
		pluma_message_get (message, "view", view, NULL);
	}
	else
	{
		*view = GTK_SOURCE_VIEW (pluma_window_get_active_view (window));
	}

	if (!*view)
	{
		return;
	}

	if (pluma_message_has_key (message, "iter"))
	{
		pluma_message_get (message, "iter", iter, NULL);
	}
	else
	{
		GtkTextBuffer *buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (*view));
		gtk_text_buffer_get_iter_at_mark (buffer,
		                                  iter,
		                                  gtk_text_buffer_get_insert (buffer));
	}
}

static void
message_toggle_cb (PlumaMessageBus *bus,
                   PlumaMessage    *message,
                   PlumaWindow     *window)
{
	GtkSourceView *view = NULL;
	GtkTextIter iter;

	message_get_view_iter (window, message, &view, &iter);

	if (!view)
	{
		return;
	}

	toggle_bookmark (GTK_SOURCE_BUFFER (gtk_text_view_get_buffer (GTK_TEXT_VIEW (view))),
	                 &iter);
}

static void
message_add_cb (PlumaMessageBus *bus,
                PlumaMessage    *message,
                PlumaWindow     *window)
{
	GtkSourceView *view = NULL;
	GtkTextIter iter;

	message_get_view_iter (window, message, &view, &iter);

	if (!view)
	{
		return;
	}

	add_bookmark (GTK_SOURCE_BUFFER (gtk_text_view_get_buffer (GTK_TEXT_VIEW (view))),
	              &iter);
}

static void
message_remove_cb (PlumaMessageBus *bus,
                   PlumaMessage    *message,
                   PlumaWindow     *window)
{
	GtkSourceView *view = NULL;
	GtkTextIter iter;

	message_get_view_iter (window, message, &view, &iter);

	if (!view)
	{
		return;
	}

	remove_bookmark (GTK_SOURCE_BUFFER (gtk_text_view_get_buffer (GTK_TEXT_VIEW (view))),
	                 &iter);
}

static void
message_goto_next_cb (PlumaMessageBus *bus,
                      PlumaMessage    *message,
                      PlumaWindow     *window)
{
	GtkSourceView *view = NULL;
	GtkTextIter iter;

	message_get_view_iter (window, message, &view, &iter);

	if (!view)
	{
		return;
	}

	goto_bookmark (window,
	               view,
	               &iter,
	               gtk_source_buffer_forward_iter_to_source_mark,
	               gtk_text_buffer_get_start_iter);
}

static void
message_goto_previous_cb (PlumaMessageBus *bus,
                          PlumaMessage    *message,
                          PlumaWindow     *window)
{
	GtkSourceView *view = NULL;
	GtkTextIter iter;

	message_get_view_iter (window, message, &view, &iter);

	if (!view)
	{
		return;
	}

	goto_bookmark (window,
	               view,
	               &iter,
	               gtk_source_buffer_backward_iter_to_source_mark,
	               gtk_text_buffer_get_end_iter);
}

static void
install_messages (PlumaWindow *window)
{
	PlumaMessageBus *bus = pluma_window_get_message_bus (window);

	pluma_message_bus_register (bus,
	                            MESSAGE_OBJECT_PATH,
	                           "toggle",
	                            2,
	                            "view", GTK_SOURCE_TYPE_VIEW,
	                            "iter", GTK_TYPE_TEXT_ITER,
				    NULL);

	pluma_message_bus_register (bus,
	                            MESSAGE_OBJECT_PATH,
	                            "add",
	                            2,
	                            "view", GTK_SOURCE_TYPE_VIEW,
	                            "iter", GTK_TYPE_TEXT_ITER,
				    NULL);

	pluma_message_bus_register (bus,
	                            MESSAGE_OBJECT_PATH,
	                            "remove",
	                            2,
	                            "view", GTK_SOURCE_TYPE_VIEW,
	                            "iter", GTK_TYPE_TEXT_ITER,
				    NULL);

	pluma_message_bus_register (bus,
	                            MESSAGE_OBJECT_PATH,
	                            "goto_next",
	                            2,
	                            "view", GTK_SOURCE_TYPE_VIEW,
	                            "iter", GTK_TYPE_TEXT_ITER,
				    NULL);

	pluma_message_bus_register (bus,
	                            MESSAGE_OBJECT_PATH,
	                            "goto_previous",
	                            2,
	                            "view", GTK_SOURCE_TYPE_VIEW,
	                            "iter", GTK_TYPE_TEXT_ITER,
				    NULL);

	BUS_CONNECT (bus, toggle, window);
	BUS_CONNECT (bus, add, window);
	BUS_CONNECT (bus, remove, window);
	BUS_CONNECT (bus, goto_next, window);
	BUS_CONNECT (bus, goto_previous, window);
}

static void
uninstall_messages (PlumaWindow *window)
{
	PlumaMessageBus *bus = pluma_window_get_message_bus (window);
	pluma_message_bus_unregister_all (bus, MESSAGE_OBJECT_PATH);
}

static void
impl_activate (PlumaPlugin *plugin,
	       PlumaWindow *window)
{
	WindowData *data;
	GList *views;
	GList *item;

	pluma_debug (DEBUG_PLUGINS);

	data = g_slice_new (WindowData);
	g_object_set_data_full (G_OBJECT (window),
				WINDOW_DATA_KEY,
				data,
				(GDestroyNotify) free_window_data);

	views = pluma_window_get_views (window);
	for (item = views; item != NULL; item = item->next)
	{
		enable_bookmarks (PLUMA_VIEW (item->data), plugin);
		load_bookmark_metadata (PLUMA_VIEW (item->data));
	}

	g_list_free (views);

	g_signal_connect (window, "tab-added",
			  G_CALLBACK (on_tab_added), plugin);

	g_signal_connect (window, "tab-removed",
			  G_CALLBACK (on_tab_removed), plugin);

	install_menu (window);
	install_messages (window);
}

static void
save_bookmark_metadata (PlumaView *view)
{
	GtkTextIter iter;
	GtkTextBuffer *buf;
	GString *string;
	gchar *val = NULL;
	gboolean first = TRUE;

	buf = gtk_text_view_get_buffer (GTK_TEXT_VIEW (view));

	gtk_text_buffer_get_start_iter (buf, &iter);

	string = g_string_new (NULL);

	while (gtk_source_buffer_forward_iter_to_source_mark (GTK_SOURCE_BUFFER (buf),
							      &iter,
							      BOOKMARK_CATEGORY))
	{
		gint line;

		line = gtk_text_iter_get_line (&iter);

		if (!first)
		{
			g_string_append_printf (string, ",%d", line);
		}
		else
		{
			g_string_append_printf (string, "%d", line);
			first = FALSE;
		}
	}

	if (string->len == 0)
	{
		val = g_string_free (string, TRUE);
		val = NULL;
	}
	else
		val = g_string_free (string, FALSE);

	pluma_document_set_metadata (PLUMA_DOCUMENT (buf), METADATA_ATTR,
				     val, NULL);

	g_free (val);
}

static void
impl_deactivate	(PlumaPlugin *plugin,
		 PlumaWindow *window)
{
	WindowData *data;
	GList *views;
	GList *item;

	pluma_debug (DEBUG_PLUGINS);

	uninstall_menu (window);
	uninstall_messages (window);

	views = pluma_window_get_views (window);

	for (item = views; item != NULL; item = item->next)
	{
		disable_bookmarks (PLUMA_VIEW (item->data));
	}

	g_list_free (views);

	data = BOOKMARKS_DATA (window);
	g_return_if_fail (data != NULL);

	g_signal_handlers_disconnect_by_func (window, on_tab_added, plugin);
	g_signal_handlers_disconnect_by_func (window, on_tab_removed, plugin);

	g_object_set_data (G_OBJECT (window), WINDOW_DATA_KEY, NULL);
}

static void
pluma_bookmarks_plugin_class_init (PlumaBookmarksPluginClass *klass)
{
	GObjectClass *object_class = G_OBJECT_CLASS (klass);
	PlumaPluginClass *plugin_class = PLUMA_PLUGIN_CLASS (klass);

	object_class->finalize = pluma_bookmarks_plugin_finalize;

	plugin_class->activate = impl_activate;
	plugin_class->deactivate = impl_deactivate;
}

static void
on_style_scheme_notify (GObject     *object,
			GParamSpec  *pspec,
			PlumaView   *view)
{
	GtkSourceMarkAttributes *attrs;
	attrs = gtk_source_view_get_mark_attributes (GTK_SOURCE_VIEW (view),
						     BOOKMARK_CATEGORY,
						     NULL);
	update_background_color (attrs, GTK_SOURCE_BUFFER(object));
}

static void
on_delete_range (GtkTextBuffer *buffer,
	     	 GtkTextIter   *start,
	     	 GtkTextIter   *end,
	     	 gpointer       user_data)
{
	GtkTextIter iter;
	GSList *marks;
	GSList *item;

	iter = *start;

	/* move to start of line */
	gtk_text_iter_set_line_offset (&iter, 0);

	/* remove any bookmarks that are collapsed on each other due to this */
	marks = gtk_source_buffer_get_source_marks_at_iter (GTK_SOURCE_BUFFER (buffer),
							    &iter,
							    BOOKMARK_CATEGORY);

	if (marks == NULL)
		return;

	/* remove all but the first mark */
	for (item = marks->next; item; item = item->next)
		gtk_text_buffer_delete_mark (buffer, GTK_TEXT_MARK (item->data));

	g_slist_free (marks);
}

static void
on_begin_user_action (GtkTextBuffer *buffer,
		      InsertData    *data)
{
	++data->user_action;
}

static void
on_end_user_action (GtkTextBuffer *buffer,
		    InsertData    *data)
{
	GSList *item;

	if (--data->user_action > 0)
	{
		return;
	}

	/* Remove trackers */
	for (item = data->trackers; item; item = g_slist_next (item))
	{
		InsertTracker *tracker = item->data;
		GtkTextIter curloc;
		GtkTextIter newloc;

		/* Move the category to the line where the mark now is */
		gtk_text_buffer_get_iter_at_mark (buffer,
		                                  &curloc,
		                                  GTK_TEXT_MARK (tracker->bookmark));

		gtk_text_buffer_get_iter_at_mark (buffer,
		                                  &newloc,
		                                  tracker->mark);

		if (gtk_text_iter_get_line (&curloc) != gtk_text_iter_get_line (&newloc))
		{
			gtk_text_iter_set_line_offset (&newloc, 0);
			gtk_text_buffer_move_mark (buffer,
			                           GTK_TEXT_MARK (tracker->bookmark),
			                           &newloc);
		}

		gtk_text_buffer_delete_mark (buffer, tracker->mark);
		g_slice_free (InsertTracker, tracker);
	}

	g_slist_free (data->trackers);
	data->trackers = NULL;
}

static void
add_tracker (GtkTextBuffer *buffer,
             GtkTextIter   *iter,
             GtkSourceMark *bookmark,
             InsertData    *data)
{
	GSList *item;
	InsertTracker *tracker;

	for (item = data->trackers; item; item = g_slist_next (item))
	{
		tracker = item->data;

		if (tracker->bookmark == bookmark)
		{
			return;
		}
	}

	tracker = g_slice_new (InsertTracker);
	tracker->bookmark = bookmark;
	tracker->mark = gtk_text_buffer_create_mark (buffer,
	                                             NULL,
	                                             iter,
	                                             FALSE);

	data->trackers = g_slist_prepend (data->trackers, tracker);
}

static void
on_insert_text_before (GtkTextBuffer *buffer,
		       GtkTextIter   *location,
		       gchar         *text,
		       gint	      len,
		       InsertData    *data)
{
	if (gtk_text_iter_starts_line (location))
	{
		GSList *marks;
		marks = gtk_source_buffer_get_source_marks_at_iter (GTK_SOURCE_BUFFER (buffer),
		                                                    location,
		                                                    BOOKMARK_CATEGORY);

		if (marks != NULL)
		{
			add_tracker (buffer, location, marks->data, data);
			g_slist_free (marks);
		}
	}
}

static GtkSourceMark *
get_bookmark_and_iter (GtkSourceBuffer *buffer,
                       GtkTextIter     *iter,
                       GtkTextIter     *start)
{
	GSList *marks;
	GtkSourceMark *ret = NULL;

	if (!iter)
	{
		gtk_text_buffer_get_iter_at_mark (GTK_TEXT_BUFFER (buffer),
		                                  start,
		                                  gtk_text_buffer_get_insert (GTK_TEXT_BUFFER (buffer)));
	}
	else
	{
		*start = *iter;
	}

	gtk_text_iter_set_line_offset (start, 0);

	marks = gtk_source_buffer_get_source_marks_at_iter (buffer,
							    start,
							    BOOKMARK_CATEGORY);

	if (marks != NULL)
	{
		ret = GTK_SOURCE_MARK (marks->data);
	}

	g_slist_free (marks);
	return ret;
}

static void
remove_bookmark (GtkSourceBuffer *buffer,
                 GtkTextIter     *iter)
{
	GtkTextIter start;
	GtkSourceMark *bookmark;

	bookmark = get_bookmark_and_iter (buffer, iter, &start);

	if (bookmark != NULL)
	{
		gtk_text_buffer_delete_mark (GTK_TEXT_BUFFER (buffer),
		                             GTK_TEXT_MARK (bookmark));
	}
}

static void
add_bookmark (GtkSourceBuffer *buffer,
              GtkTextIter     *iter)
{
	GtkTextIter start;
	GtkSourceMark *bookmark;

	bookmark = get_bookmark_and_iter (buffer, iter, &start);

	if (bookmark == NULL)
	{
		gtk_source_buffer_create_source_mark (GTK_SOURCE_BUFFER (buffer),
						      NULL,
						      BOOKMARK_CATEGORY,
						      &start);
	}
}

static void
toggle_bookmark (GtkSourceBuffer *buffer,
                 GtkTextIter     *iter)
{
	GtkTextIter start;
	GtkSourceMark *bookmark = NULL;

	bookmark = get_bookmark_and_iter (buffer, iter, &start);

	if (bookmark != NULL)
	{
		remove_bookmark (buffer, &start);
	}
	else
	{
		add_bookmark (buffer, &start);
	}
}

static void
on_toggle_bookmark_activate (GtkAction   *action,
			     PlumaWindow *window)
{
	GtkSourceBuffer *buffer = GTK_SOURCE_BUFFER (pluma_window_get_active_document (window));
	toggle_bookmark (buffer, NULL);
}

static void
on_next_bookmark_activate (GtkAction   *action,
			   PlumaWindow *window)
{
	goto_bookmark (window,
	               NULL,
	               NULL,
	               gtk_source_buffer_forward_iter_to_source_mark,
	               gtk_text_buffer_get_start_iter);
}

static void
on_previous_bookmark_activate (GtkAction   *action,
			       PlumaWindow *window)
{
	goto_bookmark (window,
	               NULL,
	               NULL,
	               gtk_source_buffer_backward_iter_to_source_mark,
	               gtk_text_buffer_get_end_iter);
}

static void
on_document_loaded (PlumaDocument *doc,
		    const GError  *error,
		    PlumaView     *view)
{
	if (error == NULL)
	{
		load_bookmark_metadata (view);
	}
}

static void
on_document_saved (PlumaDocument *doc,
		   const GError  *error,
		   PlumaView     *view)
{
	if (error == NULL)
	{
		save_bookmark_metadata (view);
	}
}

static void
on_tab_added (PlumaWindow *window,
	      PlumaTab    *tab,
	      PlumaPlugin *plugin)
{
	PlumaDocument *doc;
	PlumaView *view;

	doc = pluma_tab_get_document (tab);
	view = pluma_tab_get_view (tab);

	g_signal_connect (doc, "loaded",
			  G_CALLBACK (on_document_loaded),
			  view);
	g_signal_connect (doc, "saved",
			  G_CALLBACK (on_document_saved),
			  view);

	enable_bookmarks (view, plugin);
}

static void
on_tab_removed (PlumaWindow *window,
	        PlumaTab    *tab,
	        PlumaPlugin *plugin)
{
	PlumaDocument *doc;
	PlumaView *view;

	doc = pluma_tab_get_document (tab);
	view = pluma_tab_get_view (tab);

	g_signal_handlers_disconnect_by_func (doc, on_document_loaded, view);
	g_signal_handlers_disconnect_by_func (doc, on_document_saved, view);

	disable_bookmarks (view);
}
