/*
 * pluma-charmap-panel.c
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

#include <pluma/pluma-plugin.h>
#include "pluma-charmap-panel.h"

#include <gucharmap/gucharmap.h>

#define PLUMA_CHARMAP_PANEL_GET_PRIVATE(object)	(G_TYPE_INSTANCE_GET_PRIVATE ( \
						 (object),		       \
						 PLUMA_TYPE_CHARMAP_PANEL,     \
						 PlumaCharmapPanelPrivate))

struct _PlumaCharmapPanelPrivate
{
	GucharmapChaptersView *chapters_view;
	GucharmapChartable *chartable;
};

PLUMA_PLUGIN_DEFINE_TYPE(PlumaCharmapPanel, pluma_charmap_panel, GTK_TYPE_BOX)

static void
on_chapter_view_selection_changed (GtkTreeSelection *selection,
				   PlumaCharmapPanel *panel)
{
	PlumaCharmapPanelPrivate *priv = panel->priv;
	GucharmapCodepointList *codepoint_list;
	GtkTreeIter iter;

	if (!gtk_tree_selection_get_selected (selection, NULL, &iter))
		return;

	codepoint_list = gucharmap_chapters_view_get_codepoint_list (priv->chapters_view);
	gucharmap_chartable_set_codepoint_list (priv->chartable, codepoint_list);
	g_object_unref (codepoint_list);
}

static void
pluma_charmap_panel_init (PlumaCharmapPanel *panel)
{
	PlumaCharmapPanelPrivate *priv;
	GtkPaned *paned;
	GtkWidget *scrolled_window, *view, *chartable;
	GtkTreeSelection *selection;
	GucharmapChaptersModel *model;

	priv = panel->priv = PLUMA_CHARMAP_PANEL_GET_PRIVATE (panel);

	paned = GTK_PANED (gtk_paned_new (GTK_ORIENTATION_VERTICAL));

	scrolled_window = gtk_scrolled_window_new (NULL, NULL);
	gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW (scrolled_window),
					GTK_POLICY_NEVER, GTK_POLICY_AUTOMATIC);
	gtk_scrolled_window_set_shadow_type (GTK_SCROLLED_WINDOW (scrolled_window),
					    GTK_SHADOW_ETCHED_IN);

	view = gucharmap_chapters_view_new ();
	priv->chapters_view = GUCHARMAP_CHAPTERS_VIEW (view);
	gtk_tree_view_set_headers_visible (GTK_TREE_VIEW (view), FALSE);

	model = gucharmap_script_chapters_model_new ();
	gucharmap_chapters_view_set_model (priv->chapters_view, model);
	g_object_unref (model);

	selection = gtk_tree_view_get_selection (GTK_TREE_VIEW (view));
	g_signal_connect (selection, "changed",
			  G_CALLBACK (on_chapter_view_selection_changed), panel);

	gtk_container_add (GTK_CONTAINER (scrolled_window), view);
	gtk_widget_show (view);

	gtk_paned_pack1 (paned, scrolled_window, FALSE, TRUE);
	gtk_widget_show (scrolled_window);

	scrolled_window = gtk_scrolled_window_new (NULL, NULL);
	gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW (scrolled_window),
					GTK_POLICY_NEVER, GTK_POLICY_AUTOMATIC);
	gtk_scrolled_window_set_shadow_type (GTK_SCROLLED_WINDOW (scrolled_window),
					    GTK_SHADOW_ETCHED_IN);

	chartable = gucharmap_chartable_new ();
	priv->chartable = GUCHARMAP_CHARTABLE (chartable);
	gtk_container_add (GTK_CONTAINER (scrolled_window), chartable);
	gtk_widget_show (chartable);

	gtk_paned_pack2 (paned, scrolled_window, TRUE, TRUE);
	gtk_widget_show (scrolled_window);

	gucharmap_chapters_view_select_character (priv->chapters_view,
                  gucharmap_chartable_get_active_character (priv->chartable));

	gtk_paned_set_position (paned, 150);

	gtk_box_pack_start (GTK_BOX (panel), GTK_WIDGET (paned), TRUE, TRUE, 0);
}

static void
pluma_charmap_panel_finalize (GObject *object)
{
	G_OBJECT_CLASS (pluma_charmap_panel_parent_class)->finalize (object);
}

static void
pluma_charmap_panel_class_init (PlumaCharmapPanelClass *klass)
{
	GObjectClass *object_class = G_OBJECT_CLASS (klass);

	g_type_class_add_private (klass, sizeof (PlumaCharmapPanelPrivate));

	object_class->finalize = pluma_charmap_panel_finalize;
}

GtkWidget *
pluma_charmap_panel_new (void)
{
	return GTK_WIDGET (g_object_new (PLUMA_TYPE_CHARMAP_PANEL, NULL));
}

GucharmapChartable *
pluma_charmap_panel_get_chartable (PlumaCharmapPanel *panel)
{
	return panel->priv->chartable;
}
