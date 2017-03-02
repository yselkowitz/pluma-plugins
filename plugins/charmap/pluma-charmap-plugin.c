/*
 * pluma-charmap-plugin.c - Character map side-pane for pluma
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
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "pluma-charmap-plugin.h"
#include "pluma-charmap-panel.h"

#include <glib/gi18n-lib.h>
#include <pluma/pluma-debug.h>
#include <pluma/pluma-window.h>
#include <pluma/pluma-panel.h>
#include <pluma/pluma-document.h>
#include <pluma/pluma-prefs-manager.h>

#include <gucharmap/gucharmap.h>

#define WINDOW_DATA_KEY	"PlumaCharmapPluginWindowData"

#define PLUMA_CHARMAP_PLUGIN_GET_PRIVATE(object) \
				(G_TYPE_INSTANCE_GET_PRIVATE ((object),	\
				PLUMA_TYPE_CHARMAP_PLUGIN,		\
				PlumaCharmapPluginPrivate))

typedef struct
{
	GtkWidget	*panel;
	guint		 context_id;
} WindowData;

PLUMA_PLUGIN_REGISTER_TYPE_WITH_CODE (PlumaCharmapPlugin, pluma_charmap_plugin,
		pluma_charmap_panel_register_type (module);
)

static void
pluma_charmap_plugin_init (PlumaCharmapPlugin *plugin)
{
	pluma_debug_message (DEBUG_PLUGINS, "PlumaCharmapPlugin initializing");
}

static void
pluma_charmap_plugin_finalize (GObject *object)
{
	pluma_debug_message (DEBUG_PLUGINS, "PlumaCharmapPlugin finalizing");

	G_OBJECT_CLASS (pluma_charmap_plugin_parent_class)->finalize (object);
}

static void
free_window_data (WindowData *data)
{
	g_slice_free (WindowData, data);
}

static void
on_table_status_message (GucharmapChartable *chartable,
			 const gchar    *message,
			 PlumaWindow    *window)
{
	GtkStatusbar *statusbar;
	WindowData *data;

	statusbar = GTK_STATUSBAR (pluma_window_get_statusbar (window));
	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	gtk_statusbar_pop (statusbar, data->context_id);

	if (message)
		gtk_statusbar_push (statusbar, data->context_id, message);
}

static void
on_table_sync_active_char (GucharmapChartable *chartable,
			   GParamSpec         *psepc,
			   PlumaWindow        *window)
{
	GString *gs;
	const gchar **temps;
	gint i;
	gunichar wc;

	wc = gucharmap_chartable_get_active_character (chartable);

	gs = g_string_new (NULL);
	g_string_append_printf (gs, "U+%4.4X %s", wc,
				gucharmap_get_unicode_name (wc));

	temps = gucharmap_get_nameslist_equals (wc);
	if (temps)
	{
		g_string_append_printf (gs, "   = %s", temps[0]);
		for (i = 1;  temps[i];  i++)
			g_string_append_printf (gs, "; %s", temps[i]);
		g_free (temps);
	}

	temps = gucharmap_get_nameslist_stars (wc);
	if (temps)
	{
		g_string_append_printf (gs, "   \342\200\242 %s", temps[0]);
		for (i = 1;  temps[i];  i++)
			g_string_append_printf (gs, "; %s", temps[i]);
		g_free (temps);
	}

	on_table_status_message (chartable, gs->str, window);
	g_string_free (gs, TRUE);
}

static gboolean
on_table_focus_out_event (GtkWidget      *drawing_area,
			  GdkEventFocus  *event,
			  PlumaWindow    *window)
{
	GucharmapChartable *chartable;
	WindowData *data;

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_val_if_fail (data != NULL, FALSE);

	chartable = pluma_charmap_panel_get_chartable
					(PLUMA_CHARMAP_PANEL (data->panel));

	on_table_status_message (chartable, NULL, window);
	return FALSE;
}

static void
on_table_activate (GucharmapChartable *chartable,
		   PlumaWindow *window)
{
	GtkTextView   *view;
	GtkTextBuffer *document;
	GtkTextIter start, end;
	gchar buffer[6];
	gchar length;
        gunichar wc;

        wc = gucharmap_chartable_get_active_character (chartable);

	g_return_if_fail (gucharmap_unichar_validate (wc));

	view = GTK_TEXT_VIEW (pluma_window_get_active_view (window));

	if (!view || !gtk_text_view_get_editable (view))
		return;

	document = gtk_text_view_get_buffer (view);

	g_return_if_fail (document != NULL);

	length = g_unichar_to_utf8 (wc, buffer);

	gtk_text_buffer_begin_user_action (document);

	gtk_text_buffer_get_selection_bounds (document, &start, &end);

	gtk_text_buffer_delete_interactive (document, &start, &end, TRUE);
	if (gtk_text_iter_editable (&start, TRUE))
		gtk_text_buffer_insert (document, &start, buffer, length);

	gtk_text_buffer_end_user_action (document);
}

static GtkWidget *
create_charmap_panel (PlumaWindow *window)
{
	GtkWidget      *panel;
	GucharmapChartable *chartable;
	PangoFontDescription *font_desc;
	gchar *font;

	panel = pluma_charmap_panel_new ();

	/* Use the same font as the document */
	font = pluma_prefs_manager_get_editor_font ();

	chartable = pluma_charmap_panel_get_chartable (PLUMA_CHARMAP_PANEL (panel));
	font_desc = pango_font_description_from_string (font);
	gucharmap_chartable_set_font_desc (chartable, font_desc);
	pango_font_description_free (font_desc);

	g_free (font);

	g_signal_connect (chartable,
			  "notify::active-character",
			  G_CALLBACK (on_table_sync_active_char),
			  window);
	g_signal_connect (chartable,
			  "focus-out-event",
			  G_CALLBACK (on_table_focus_out_event),
			  window);
	g_signal_connect (chartable,
			  "status-message",
			  G_CALLBACK (on_table_status_message),
			  window);
	g_signal_connect (chartable,
			  "activate",
			  G_CALLBACK (on_table_activate),
			  window);

	gtk_widget_show_all (panel);

	return panel;
}

static void
impl_activate (PlumaPlugin *plugin,
	       PlumaWindow *window)
{
	PlumaPanel *panel;
	GtkWidget *image;
	GtkIconTheme *theme;
	GtkStatusbar *statusbar;
	WindowData *data;

	pluma_debug (DEBUG_PLUGINS);

	panel = pluma_window_get_side_panel (window);

	data = g_slice_new (WindowData);

	theme = gtk_icon_theme_get_default ();

	if (gtk_icon_theme_has_icon (theme, "accessories-character-map"))
		image = gtk_image_new_from_icon_name ("accessories-character-map",
						      GTK_ICON_SIZE_MENU);
	else
		image = gtk_image_new_from_icon_name ("gucharmap",
						      GTK_ICON_SIZE_MENU);

	data->panel = create_charmap_panel (window);

	pluma_panel_add_item (panel,
			      data->panel,
			      _("Character Map"),
			      image);

	g_object_ref_sink (G_OBJECT (image));

	statusbar = GTK_STATUSBAR (pluma_window_get_statusbar (window));
	data->context_id = gtk_statusbar_get_context_id (statusbar,
							 "Character Description");

	g_object_set_data_full (G_OBJECT (window),
				WINDOW_DATA_KEY,
				data,
				(GDestroyNotify) free_window_data);
}

static void
impl_deactivate	(PlumaPlugin *plugin,
		 PlumaWindow *window)
{
	PlumaPanel *panel;
	WindowData *data;
	GucharmapChartable *chartable;

	pluma_debug (DEBUG_PLUGINS);

	data = (WindowData *) g_object_get_data (G_OBJECT (window),
						 WINDOW_DATA_KEY);
	g_return_if_fail (data != NULL);

	chartable = pluma_charmap_panel_get_chartable
					(PLUMA_CHARMAP_PANEL (data->panel));
	on_table_status_message (chartable, NULL, window);

	panel = pluma_window_get_side_panel (window);
	pluma_panel_remove_item (panel, data->panel);

	g_object_set_data (G_OBJECT (window), WINDOW_DATA_KEY, NULL);
}

static void
pluma_charmap_plugin_class_init (PlumaCharmapPluginClass *klass)
{
	GObjectClass *object_class = G_OBJECT_CLASS (klass);
	PlumaPluginClass *plugin_class = PLUMA_PLUGIN_CLASS (klass);

	object_class->finalize = pluma_charmap_plugin_finalize;

	plugin_class->activate = impl_activate;
	plugin_class->deactivate = impl_deactivate;
}
