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
Dispatcher.CreateDatabase is responsible for initalising the database necessary
for Dispatcher to operate.
"""

if __name__ == '__main__':
	import sys
	try:
		import sqlalchemy
	except ImportError as err:
		print('LuxFire.Dispatcher startup error: %s' % err)
		sys.exit(-1)
	
	import optparse
	parser = optparse.OptionParser(
		prog='LuxFire.Dispatcher.CreateDatabase',
		description='Creates the database required for LuxFire.Dispatcher. '
		'If a non-default database connection string is specified, it will '
		'be saved into the luxfire.cfg file so that LuxFire.Dispatcher can '
		'connect to it automatically the next time it is run'
	)
	parser.add_option(
		'-d',
		'--database',
		dest='database',
		metavar='STR',
		help='Database connection string to use. '
		'See sqlalchemy docs for supported connection types'
	)
	parser.add_option(
		'-v',
		'--verbose',
		action='store_true',
		dest='verbose',
		default=False,
		help='Show database creation progress'
	)
	(options, args) = parser.parse_args()
	
	from . import DispatcherLog
	
	# Set verbose mode to see table creation output
	from . import Database
	Database.DATABASE_VERBOSE = options.verbose
	
	# Set auto table create
	Database.AUTO_TABLE_CREATE = True
	
	# Use the database connection specified, and save it to config file
	if options.database:
		from .. import LuxFireConfig
		LuxFireConfig.Instance().set('Dispatcher', 'database', options.database)
		LuxFireConfig.Instance().Save()
	
	DispatcherLog('Creating new database...')
	
	# Just importing the Models is enough to cause Table creation when
	# AUTO_TABLE_CREATE == True. They need to be imported in the correct order
	# to meet relationship dependencies
	from .Models.Role import Role
	from .Models.User import User
	from .Models.Queue import Queue
	from .Models.Result import Result
	
	DispatcherLog('... done')
