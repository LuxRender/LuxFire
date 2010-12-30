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
import signal, threading, time

# Non-System imports
import Pyro

# LuxRender imports
from LuxRender import LuxLog

# LuxFire imports
from .. import LuxFireConfig

class ServerObject(object):
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
		
		self.SetDebug(debug)
		if name != None:
			self.SetName(name)
		else:
			self.SetName('LuxFire.%s.%08x' % (self._Service_Type, id(self)))
	
	def __repr__(self):
		return '<%s>' % self.name
	
	def SetName(self, name):
		self.name = name
	
	def GetName(self):
		return self.name
	
	def SetDebug(self, debug):
		self.debug = bool(debug)
		
	def Ping(self):
		self._pingval+=1
		return self._pingval
	
	def dbo(self, str, always=False):
		with ServerObject.print_lock:
			if self.debug or always:
				#print('[%s] %s %s' %(time.strftime("%Y-%m-%d %H:%M:%S"), self, str))
				LuxLog(str, module_name=self)
		
	def log(self, str):
		self.dbo(str, True)
	
	def _cleanup(self):
		"""
		This method is called when the ServerThread holding this object ends.
		This method is called after _stop() in the shutdown process.
		"""
		pass
	
	def _start(self):
		"""
		If the service object needs to start its own threads/timers etc, it
		should do so in this method.
		"""
		pass
	
	def _stop(self):
		"""
		If the service object needs to stop/join its own threads/timers etc, it
		should do so in this method.
		"""
		pass

class ServerObjectThread(threading.Thread, ServerObject):
	"""
	This is a convenience mixin which allows using a ServerObject as a thread
	"""
	
	def __init__(self, debug = False):
		threading.Thread.__init__(self)
		ServerObject.__init__(self, debug)

class ServerThread(ServerObjectThread):
	'''
	Pyro service thread
	
	All services are started in Pyro NS with prefix Lux.*
	'service' should be instance of class to serve
	'name' is service name to register with Pyro NS
	'''
	
	service		= None  # Object to Serve (Proxy)
	name		= None  # Proxy Name
	so			= None  # Pyro Proxy URI
	daemon		= None  # Pyro service daemon
	
	def __repr__(self):
		return '<ServerThread %s>' % self.service
	
	def setup(self, bind_addr, service, name):
		self.service = service
		self.name = name
		self.daemon = Pyro.core.Daemon( bind_addr )
		self.so = self.daemon.register(self.service)
	
	def run(self):
		# Max attempts to register in NS
		create_attempts = 10
		try:
			ns = Pyro.naming.locateNS()
		except Exception as err:
			self.log('Service publication error: %s' % err)
			create_attempts = 0
		
		while create_attempts > 0:
			try:
				ns.register(self.name, self.so)
				create_attempts = -1
			except Exception as err:
				self.log(err)
				try:
					ns.remove(self.name)
				except: pass
				create_attempts -= 1
				time.sleep(1)
		
		self.service._start()
		self.log('Started: Pyro URL: %s' % self.so)
		self.log('Discoverable in Pyro nameserver: %s' % (create_attempts!=0))
		
		# Blocks until stopped externally
		self.daemon.requestLoop()
		
		try:
			ns.remove(self.name)
		except: pass
		finally:
			if self.so: del self.so
			self.service._stop()
			self.service._cleanup()
			self.service = '%s' % self.service # replace service object with id string
			if self.daemon: del self.daemon
			if 'ns' in locals(): del ns
		
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
		signal.signal(signal.SIGINT, self._sighandler_INT)
	
	def _sighandler_INT(self, sig, frame):
		self.run.set()
	
	def __repr__(self):
		return '<Server %s~%x>' % (self.bind, id(self))
	
	def new_server_thread(self, service, name):
		st = ServerThread()
		st.setup(self.bind, service, name)
		self.server_threads[name] = st
		st.start()
	
	def start(self, _so):
		# First set up bind address
		Pyro.config.HOST = self.bind
		
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
			for serv, thread in thread_list:	#@UnusedVariable
				if thread.daemon:
					thread.daemon.shutdown()
			
			for serv, thread in thread_list:	#@UnusedVariable
				thread.join()
			self.log('...finished')
