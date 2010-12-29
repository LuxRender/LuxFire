#!/usr/bin/env python3
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
The luxfire_standalone script will start a local Pyro NS, Renderer.Server and
Dispatcher.Server in order to have a complete running system with one command.
"""

if __name__=='__main__':
	import optparse
	parser = optparse.OptionParser(
		description='All-in-one launcher script for a standalone render queue. '
		'By default, this script will start a Pyro name server, a '
		'LuxFire.Dispatcher.Server and a LuxFire.Renderer.Server. You can '
		'disable any of these with the options below.'
	)
	parser.add_option(
		'-x',
		'--no-nameserver',
		dest='nameserver',
		action='store_false',
		default=True,
		help='Do not start a Pyro name server.'
	)
	parser.add_option(
		'-d',
		'--no-dispatcher',
		dest='dispatcher',
		action='store_false',
		default=True,
		help='Do not start a LuxFire.Dispatcher.Server'
	)
	parser.add_option(
		'-r',
		'--no-renderer',
		dest='renderer',
		action='store_false',
		default=True,
		help='Do not start a LuxFire.Renderer.Server'
	)
	parser.add_option(
		'-v',
		'--verbose',
		action='store_true',
		dest='verbose',
		default=False,
		help='Show more output while running'
	)
	(options, args) = parser.parse_args()
	
	try:
		from LuxFire import LuxFireConfig, LuxFireLog
		cfg = LuxFireConfig.Instance()
		
		# Using multiprocess.Process prevents DB deadlocking when using SQLite
		# and running multiple servers.
		import multiprocessing
		LF_Servers = []
		
		if options.nameserver:
			import Pyro, threading
			
			def start_ns():
				try:
					import socket
					Pyro.naming.startNSloop(host=cfg.get('LuxFire', 'bind'), enableBroadcast=True)
				except socket.error as err:
					LuxFireLog('Error running nameserver: %s' % err)
			
			NS = threading.Thread(target=start_ns)
			NS.setDaemon(True)	# Won't join() on exit
			NS.start()
		
		from LuxFire.Server import Server
		
		LuxFireLog('Press CTRL-C to stop')
		
		if options.renderer:
			from LuxFire.Renderer import Renderer
			rs = Server(debug=options.verbose)
			rs_proc = multiprocessing.Process(
				target=rs.start,
				args=([Renderer],)
			)
			LF_Servers.append(rs_proc)
			rs_proc.start()
		
		if options.dispatcher:
			from LuxFire.Dispatcher import Dispatcher
			ds = Server(debug=options.verbose)
			ds_proc = multiprocessing.Process(
				target=ds.start,
				args=([Dispatcher],)
			)
			LF_Servers.append(ds_proc)
			ds_proc.start()
		
		# Wait for each child process to quit
		for server_process in LF_Servers:
			server_process.join()
		
	except ImportError as err:
		print('A required component of the LuxFire system was not found: %s' % err)
		print('In order to operate, LuxFire requires python3-sqlalchemy and PyLux.')
		print('The PyLux module pylux.so or pylux.pyd should be placed inside the')
		print('LuxRender folder. You can get a PyLux module from http://www.luxrender.net/')
	