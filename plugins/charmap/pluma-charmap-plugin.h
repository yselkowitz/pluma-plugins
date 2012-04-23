/*
 * pluma-charmap-plugin.h - Character map side-pane for pluma
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

#ifndef __PLUMA_CHARMAP_PLUGIN_H__
#define __PLUMA_CHARMAP_PLUGIN_H__

#include <glib.h>
#include <glib-object.h>
#include <pluma/pluma-plugin.h>

G_BEGIN_DECLS

/*
 * Type checking and casting macros
 */
#define PLUMA_TYPE_CHARMAP_PLUGIN		(pluma_charmap_plugin_get_type ())
#define PLUMA_CHARMAP_PLUGIN(o)			(G_TYPE_CHECK_INSTANCE_CAST ((o), PLUMA_TYPE_CHARMAP_PLUGIN, PlumaCharmapPlugin))
#define PLUMA_CHARMAP_PLUGIN_CLASS(k)		(G_TYPE_CHECK_CLASS_CAST((k), PLUMA_TYPE_CHARMAP_PLUGIN, PlumaCharmapPluginClass))
#define PLUMA_IS_CHARMAP_PLUGIN(o)		(G_TYPE_CHECK_INSTANCE_TYPE ((o), PLUMA_TYPE_CHARMAP_PLUGIN))
#define PLUMA_IS_CHARMAP_PLUGIN_CLASS(k)	(G_TYPE_CHECK_CLASS_TYPE ((k), PLUMA_TYPE_CHARMAP_PLUGIN))
#define PLUMA_CHARMAP_PLUGIN_GET_CLASS(o)	(G_TYPE_INSTANCE_GET_CLASS ((o), PLUMA_TYPE_CHARMAP_PLUGIN, PlumaCharmapPluginClass))

/* Private structure type */
typedef struct _PlumaCharmapPluginPrivate	PlumaCharmapPluginPrivate;

/*
 * Main object structure
 */
typedef struct _PlumaCharmapPlugin		PlumaCharmapPlugin;

struct _PlumaCharmapPlugin
{
	PlumaPlugin parent_instance;
};

/*
 * Class definition
 */
typedef struct _PlumaCharmapPluginClass	PlumaCharmapPluginClass;

struct _PlumaCharmapPluginClass
{
	PlumaPluginClass parent_class;
};

/*
 * Public methods
 */
GType	pluma_charmap_plugin_get_type	(void) G_GNUC_CONST;

/* All the plugins must implement this function */
G_MODULE_EXPORT GType register_pluma_plugin (GTypeModule *module);

G_END_DECLS

#endif /* __PLUMA_CHARMAP_PLUGIN_H__ */
