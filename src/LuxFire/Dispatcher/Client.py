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
Dispatcher.Client provides access to existing remote Dispatcher.Servers.
"""

from ..Client import ListLuxFireGroup, ServerLocator, ClientException

def DispatcherGroup():
	LuxSlavesNames = ListLuxFireGroup('Dispatcher')
	slaves = {}
	
	if len(LuxSlavesNames) > 0:
		for LN in LuxSlavesNames:
			try:
				RS = ServerLocator.Instance().get_by_name(LN)
				slaves[LN] = RS
				break	# Only return the first dispatcher
			except Exception as err:
				raise ClientException('Error with remote dispatcher %s: %s' % (LN, err))
		
	else:
		raise ClientException('No Dispatchers found')
	
	return slaves

if __name__ == '__main__':
	
	try:
		slaves = DispatcherGroup()
		for sn, Dispatcher in slaves.items():
			pass
		print('Just one dispatcher found, available as "Dispatcher" variable.')
		del slaves, sn
	except ClientException as err:
		print('%s'%err)
