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
if __name__ == '__main__':
	import sys
	try:
		import sqlalchemy
	except ImportError as err:
		print('LuxFire.Dispatcher startup error: %s' % err)
		sys.exit(-1)
	
	# Set verbose mode to see table creation
	import Dispatcher.Database
	Dispatcher.Database.DATABASE_VERBOSE |= True
	
	# Set auto table create
	Dispatcher.Database.AUTO_TABLE_CREATE |= True
	
	# Just importing the Models is enough to cause Table creation when
	# AUTO_TABLE_CREATE == True. They need to be imported in the correct order
	# to meet relationship dependencies
	from Dispatcher.Models.Role import Role
	from Dispatcher.Models.User import User
	from Dispatcher.Models.Queue import Queue
	from Dispatcher.Models.Result import Result
