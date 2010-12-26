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

from ...Client import ServerLocator, ListLuxFireGroup
from ...Renderer.Client import RendererClient

if __name__ == '__main__':
	
	import time
	
	while True:
	
		LuxSlavesNames = ListLuxFireGroup(grp='Renderer')
		
		if len(LuxSlavesNames) > 0:
			slaves = []
			print('------------------------------------------------------------------')
			for LN, i in LuxSlavesNames.items():
				RemoteRenderer = RendererClient(ServerLocator.get_by_name(LN))
				ss = RemoteRenderer.printableStatistics(True)
				if ss == '':
					ss = 'Idle'
				print('%s : %s' % (LN, ss))
		else:
			print('No remote LuxFire components available')
		
		time.sleep(5)
