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
The Server package contains methods and objects useful for proxying and Serving
objects across the network.
"""

# System imports
import threading, time

# Non-System imports
import Pyro

# LuxFire imports
from .. import LuxFireConfig

class ServerObject(object): #Pyro.EventService.Clients.Publisher):
	'''
	Base Class for all Server Processes. Provides:
	def SetDebug(bool)		- Change debug on/off
	def Ping()				- Ping the object
	def dbo(str, bool)		- DeBugOutput - threadsafe print to stdout (bool==always, regardless of self.debug)
	def log(str)			- Shortcut for self.dbo(str, True)
	'''
	
	_Service_Type = 'Unknown'
	
	print_lock = threading.Lock()
	
	debug = False
	_pingval = 0
	name = ''
	
	def __init__(self, debug=False, name=None):
		'''
		Constructor
		'''
		#Pyro.EventService.Clients.Publisher.__init__(self)
		
		self.SetDebug(debug)
		if name != None:
			self.SetName(name)
		else:
			self.SetName('LuxFire.%s.%08x' % (self._Service_Type, id(self)))
	
	def __repr__(self):
		return '<%s>' % self.name
	
	def SetName(self, name):
		self.name = name
	
	def SetDebug(self, debug):
		self.debug = bool(debug)
		
	def Ping(self):
		self._pingval+=1
		return self._pingval
	
	def dbo(self, str, always=False):
		with ServerObject.print_lock:
			if self.debug or always: print('[%s] %s %s' %(time.strftime("%Y-%m-%d %H:%M:%S"), self, str))
		
	def log(self, str):
		self.dbo(str, True)

class ServerThread(threading.Thread, ServerObject):
	'''
	Pyro service thread
	
	All services are started in Pyro NS with prefix Lux.*
	'service' should be instance of class to serve
	'name' is service name to register with Pyro NS
	'''
	
	service		= None  # Object to Serve (Proxy)
	name		= None  # Proxy Name
	so			= None  # Pyro Proxy URI
	daemon		= None
	
	def __repr__(self):
		return '<ServerThread %s>' % self.service
	
	def setup(self, service, name):
		self.service = service
		self.name = name
		self.daemon = Pyro.core.Daemon()
		self.so = self.daemon.register(self.service)
	
	def run(self):
		ns = Pyro.naming.locateNS()
		#try:
		#	ns.createGroup(':Lux')
		#	ns.createGroup(':Lux.Renderer')
		#except: pass
		
		#self.daemon = Pyro.core.Daemon()
		#self.daemon.useNameServer(ns)
		create_attempts = 10 # Max attempts to register in NS
		while create_attempts > 0:
			try:
				#self.daemon.connect(self.so, self.name)
				#print(self.name)
				#print(self.so)
				ns.register(self.name, self.so)
				create_attempts = -1
			except Exception as err:
				self.log(err)
				#self.log('Deleting stale NS entry: %s' % self.name)
				ns.remove(self.name)
				create_attempts -= 1
				time.sleep(1)
		
		if create_attempts == 0:
			self.log('Cannot register service with Pyro NS')
		else:
			self.log('Started')
			self.daemon.requestLoop()	# Blocks until stopped externally
		
		try:
			ns.remove(self.name)
		except: pass
		finally:
			if self.so: del self.so
			self.service = '%s' % self.service # replace service object with id string
			if self.daemon: del self.daemon
			if ns: del ns
		
		self.log('Stopped')

class Server(ServerObject):
	'''
	The actual main server process that starts and stops all other services
	passed in a list to the start method (_so).
	'''
	
	# Dict of server threads
	server_threads = {}
	
	# Server run flag (threading.Event)
	run = None
	
	# Local hostname or IP addr to use for Pyro services
	bind = LuxFireConfig.Instance().get('LuxFire', 'bind')
	
	def __init__(self, debug=False):
		self.SetDebug(debug)
	
	def __repr__(self):
		return '<Server %s~%x>' % (self.bind, id(self))
	
	def new_server_thread(self, service, name):
		st = ServerThread()
		st.setup(service, name)
		self.server_threads[name] = st
		st.start()
	
	def start(self, _so):
		# First set up bind address
		Pyro.config.PYRO_HOST = self.bind
		
		self.log('Server starting...')
		
		for server in _so:
			r = server(debug=self.debug)
			self.new_server_thread(r, r.name)
		
		try:
			self.run = threading.Event()
			while not self.run.is_set():
				self.run.wait(10)
		except KeyboardInterrupt:
			self.run.set()
		finally:
			self.log('Server Shutdown')
			
			# first signal shutdowns, and then attempt thread join in reverse order
			# we do this to help prevent exceptions at shutdown time from services
			# calling others that are no longer present
			thread_list = list(self.server_threads.items())
			thread_list.reverse()
			for serv, thread in thread_list:
				if thread.daemon:
					thread.daemon.shutdown()
			
			for serv, thread in thread_list:
				thread.join()
			self.log('...finished')
