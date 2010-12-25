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
import Pyro.errors

from Client import ServerLocator

def list_luxfire_components(grp='Renderer'):
    try:
        LuxSlaves = ServerLocator.get_list('Lux.%s'%grp)
        return LuxSlaves
    except Pyro.errors.NamingError as err:
        print('Lux Pyro NS group "%s" not found - No LuxFire components are running ?'%grp)
        return []
        

if __name__ == '__main__':
    LuxSlavesNames = list_luxfire_components()
    
    if len(LuxSlavesNames) > 0:
        from Client.Renderer import RendererClient
        slaves = {}
        for LN, i in LuxSlavesNames.items():
            RS = ServerLocator.get_by_name(LN)
            LS = RendererClient(RS)
            slaves[LN] = (LS, RS)
        print(slaves)
    else:
        print('No remote Lux components available')
