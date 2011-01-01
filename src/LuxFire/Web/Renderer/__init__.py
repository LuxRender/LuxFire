# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# LuxFire Distributed Rendering System
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
#
"""
LuxFire.Renderer information views
"""

from ...Client import ClientException
from ...Renderer.Client import RendererGroup, RendererClient

from .. import LuxFireWeb
from .. import User

@LuxFireWeb.route('/renderer')
@User.protected()
def renderer_index():
	out = LuxFireWeb._templater.get_template('renderer_index.html').render()
	
	try:
		renderers = []
		for rn, (client, proxy) in RendererGroup().items():
			renderers.append(
				(rn, client, proxy)
			)
		out += LuxFireWeb._templater.get_template('renderer_stats.html').render(
			renderers=renderers
		)
	except ClientException as err:
		out += '<div style="clear:both;"><em>Error: %s</em></div>' % err
	
	return out