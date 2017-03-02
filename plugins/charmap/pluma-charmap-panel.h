/*
 * charmap-panel.h
 * This file is part of pluma
 *
 * Copyright (C) 2006 - Steve Frécinaux
 *
 * pluma is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * pluma is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with pluma; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor,
 * Boston, MA  02110-1301  USA
 */

#ifndef __PLUMA_CHARMAP_PANEL_H__
#define __PLUMA_CHARMAP_PANEL_H__

#include <glib.h>
#include <glib-object.h>
#include <gtk/gtk.h>

#include <gucharmap/gucharmap.h>

G_BEGIN_DECLS

/*
 * Type checking and casting macros
 */
#define PLUMA_TYPE_CHARMAP_PANEL		(pluma_charmap_panel_get_type ())
#define PLUMA_CHARMAP_PANEL(o)			(G_TYPE_CHECK_INSTANCE_CAST ((o), PLUMA_TYPE_CHARMAP_PANEL, PlumaCharmapPanel))
#define PLUMA_CHARMAP_PANEL_CLASS(k)		(G_TYPE_CHECK_CLASS_CAST((k), PLUMA_TYPE_CHARMAP_PANEL, PlumaCharmapPanelClass))
#define PLUMA_IS_CHARMAP_PANEL(o)		(G_TYPE_CHECK_INSTANCE_TYPE ((o), PLUMA_TYPE_CHARMAP_PANEL))
#define PLUMA_IS_CHARMAP_PANEL_CLASS(k)		(G_TYPE_CHECK_CLASS_TYPE ((k), PLUMA_TYPE_CHARMAP_PANEL))
#define PLUMA_CHARMAP_PANEL_GET_CLASS(o)	(G_TYPE_INSTANCE_GET_CLASS ((o), PLUMA_TYPE_CHARMAP_PANEL, PlumaCharmapPanelClass))

/* Private structure type */
typedef struct _PlumaCharmapPanelPrivate	PlumaCharmapPanelPrivate;

/*
 * Main object structure
 */
typedef struct _PlumaCharmapPanel		PlumaCharmapPanel;

struct _PlumaCharmapPanel
{
	GtkBox parent_instance;

	/*< private > */
	PlumaCharmapPanelPrivate *priv;
};

/*
 * Class definition
 */
typedef struct _PlumaCharmapPanelClass	PlumaCharmapPanelClass;

struct _PlumaCharmapPanelClass
{
	GtkBoxClass parent_class;
};

/*
 * Public methods
 */
GType		 pluma_charmap_panel_get_type	   (void) G_GNUC_CONST;
GType		 pluma_charmap_panel_register_type (GTypeModule * module);
GtkWidget	*pluma_charmap_panel_new	   (void);

GucharmapChartable *pluma_charmap_panel_get_chartable (PlumaCharmapPanel *panel);

G_END_DECLS

#endif /* __CHARMAP_PANEL_H__ */
