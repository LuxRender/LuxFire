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
Database.Create is responsible for initalising the database necessary for some
LuxFire components to operate.
"""

if __name__ == '__main__':
	import sys
	try:
		import sqlalchemy	#@UnusedImport
	except ImportError as err:
		print('LuxFire.Database.Create startup error: %s' % err)
		sys.exit(-1)
	
	import optparse
	parser = optparse.OptionParser(
		prog='LuxFire.Database.Create',
		description='Creates the database required for LuxFire. '
		'If a non-default database connection string is specified, it will '
		'be saved into the luxfire.cfg file so that LuxFire can '
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
	parser.add_option(
		'-b',
		'--bind',
		dest='bind',
		metavar='ADDR',
		help='Specify the local IP/hostname to bind services to. This would '
		'usually be the IP address of this machine\'s main network adaptor. '
		'It is not advisable to bind to IP addresses that are accessible on '
		'the internet.'
	)
	(options, args) = parser.parse_args()
	
	from .. import LuxFireLog
	
	# Use the database connection specified, and save it to config file
	from .. import LuxFireConfig
	from . import Database
	if options.database:
		LuxFireConfig.Instance().set('LuxFire', 'database', options.database)
		# Renew the _instance to force reloading the new configuration
		Database.Instance(new=True)
	
	if options.bind:
		LuxFireConfig.Instance().set('LuxFire', 'bind', options.bind)
	
	# Update/create a default config file too
	LuxFireLog('Creating/updating local config file...')
	LuxFireConfig.Instance().Save()
	
	LuxFireLog('Creating new database...')
	
	from .Models.Role import Role	#@UnusedImport
	from .Models.User import User	#@UnusedImport
	from .Models.UserSession import UserSession	#@UnusedImport
	from .Models.Queue import Queue	#@UnusedImport
	from .Models.Result import Result	#@UnusedImport
	
	# TODO: create default root user if not exists
	
	Database.CreateDatabase(options.verbose)
	
	LuxFireLog('... done')
