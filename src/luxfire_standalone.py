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
The luxfire_standalone script will start a local Pyro NS, Renderer.Server,
Dispatcher.Server and Web.Server in order to have a complete running system
with one command.
"""

if __name__=='__main__':
	import optparse
	parser = optparse.OptionParser(
		description='All-in-one launcher script for a standalone render queue. '
		'By default, this script will start a Pyro name server, a '
		'LuxFire.Dispatcher.Server, LuxFire.Renderer.Server and a LuxFire.Web.Server. '
		'You can disable any of these with the options below.'
	)
	parser.add_option(
		'-n',
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
		'-w',
		'--no-webserver',
		dest='webserver',
		action='store_false',
		default=True,
		help='Do not start a LuxFire.Web.Server'
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
		# and running multiple servers, also makes better use of multicore CPUs.
		import multiprocessing, os, threading, signal
		LF_Servers = []
		
		LuxFireLog('Press CTRL-C to stop')
		
		if options.nameserver:
			from LuxFire.Server import pyro_ns_serve
			ns_proc = multiprocessing.Process(target=pyro_ns_serve)
			ns_proc.start()
			LF_Servers.append(ns_proc)
		
		if options.renderer:
			from LuxFire.Renderer.Server import renderer_serve
			rs_proc = multiprocessing.Process(target=renderer_serve)
			rs_proc.start()
			LF_Servers.append(rs_proc)
		
		if options.dispatcher:
			from LuxFire.Dispatcher.Server import dispatcher_serve
			ds_proc = multiprocessing.Process(target=dispatcher_serve)
			ds_proc.start()
			LF_Servers.append(ds_proc)
		
		if options.webserver:
			from LuxFire.Web.Server import web_serve
			ws_proc = multiprocessing.Process(target=web_serve)
			ws_proc.start()
			LF_Servers.append(ws_proc)
		
		evt = threading.Event()
		def sighandler_INT(sig, frame):
			evt.set()
		signal.signal(signal.SIGINT, sighandler_INT)
		try:
			while not evt.is_set():
				evt.wait(10)
		except KeyboardInterrupt:
			evt.set()
		finally:
			for server_process in LF_Servers:
				if server_process.is_alive():
					if os.name != 'nt':
						# Windows doesn't have kill(), but seems to
						# terminate the children forcefully instead :(
						os.kill(server_process.pid, signal.SIGINT)
					server_process.join()
		
	except ImportError as err:
		print('A required component of the LuxFire system was not found: %s' % err)
		print('In order to operate, LuxFire requires python3-sqlalchemy and PyLux.')
		print('The PyLux module pylux.so or pylux.pyd should be placed inside the')
		print('LuxRender folder. You can get a PyLux module from http://www.luxrender.net/')
	