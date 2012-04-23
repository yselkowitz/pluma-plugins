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
 *
 * $Id: pluma-drawspaces-plugin.h 137 2006-04-23 15:13:27Z sfre $
 */

#ifndef __PLUMA_DRAWSPACES_PLUGIN_H__
#define __PLUMA_DRAWSPACES_PLUGIN_H__

#include <glib.h>
#include <glib-object.h>
#include <pluma/pluma-plugin.h>

G_BEGIN_DECLS

/*
 * Type checking and casting macros
 */
#define PLUMA_TYPE_DRAWSPACES_PLUGIN		(pluma_drawspaces_plugin_get_type ())
#define PLUMA_DRAWSPACES_PLUGIN(o)		(G_TYPE_CHECK_INSTANCE_CAST ((o), PLUMA_TYPE_DRAWSPACES_PLUGIN, PlumaDrawspacesPlugin))
#define PLUMA_DRAWSPACES_PLUGIN_CLASS(k)	(G_TYPE_CHECK_CLASS_CAST((k), PLUMA_TYPE_DRAWSPACES_PLUGIN, PlumaDrawspacesPluginClass))
#define PLUMA_IS_DRAWSPACES_PLUGIN(o)		(G_TYPE_CHECK_INSTANCE_TYPE ((o), PLUMA_TYPE_DRAWSPACES_PLUGIN))
#define PLUMA_IS_DRAWSPACES_PLUGIN_CLASS(k)	(G_TYPE_CHECK_CLASS_TYPE ((k), PLUMA_TYPE_DRAWSPACES_PLUGIN))
#define PLUMA_DRAWSPACES_PLUGIN_GET_CLASS(o)	(G_TYPE_INSTANCE_GET_CLASS ((o), PLUMA_TYPE_DRAWSPACES_PLUGIN, PlumaDrawspacesPluginClass))

/* Private structure type */
typedef struct _PlumaDrawspacesPluginPrivate	PlumaDrawspacesPluginPrivate;

/*
 * Main object structure
 */
typedef struct _PlumaDrawspacesPlugin		PlumaDrawspacesPlugin;

struct _PlumaDrawspacesPlugin
{
	PlumaPlugin parent_instance;

	/* private */
	PlumaDrawspacesPluginPrivate *priv;
};

/*
 * Class definition
 */
typedef struct _PlumaDrawspacesPluginClass	PlumaDrawspacesPluginClass;

struct _PlumaDrawspacesPluginClass
{
	PlumaPluginClass parent_class;
};

/*
 * Public methods
 */
GType	pluma_drawspaces_plugin_get_type	(void) G_GNUC_CONST;

/* All the plugins must implement this function */
G_MODULE_EXPORT GType register_pluma_plugin (GTypeModule *module);

G_END_DECLS

#endif /* __PLUMA_DRAWSPACES_PLUGIN_H__ */
