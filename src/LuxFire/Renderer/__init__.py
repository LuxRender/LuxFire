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
Renderer represents an instance of the LuxRender Renderer Context.
"""
import os, threading, time

# LuxRender imports
from LuxRender import LuxLog

# LuxFire imports 
from ..Server import ServerObject
from .. import LuxFireConfig

def RendererLog(message):
	LuxLog(message, module_name='LuxFire.Renderer')

class Renderer(ServerObject):
	'''
	A Pyro server for a pylux.Context object. Access to the Context
	is via the luxcall() method, other methods in this class provide
	information about the Context
	'''
	_Service_Type = 'Renderer'
	
	# The Lux Rendering Context
	_lux_context = None
	
	# Methods available in Rendering Context
	_context_methods = []
	
	def __init__(self, debug, name=None):
		'''
		Set up this server for debug mode, configure its service name and then
		create a Context and ask it what methods it has.
		'''
		ServerObject.__init__(self, debug=debug, name=name)
		
		from LuxRender import pylux	#@UnresolvedImport
		self._lux_context = pylux.Context( '%x' % id(self) )
		self._context_methods = dir(self._lux_context)
	
	def __del__(self):
		self._cleanup()
	
	def _cleanup(self):
		'''
		If this server is killed, make sure the Context ends cleanly
		'''
		self.dbo('Lux Context exit/wait/cleanup')
		if self._lux_context is not None:
			self._lux_context.exit()
			self._lux_context.wait()
			self._lux_context.cleanup()
	
	def SetNetworkWD(self, path):
		# We need to start the server in the NetworkStorage location, if possible
		cfg = LuxFireConfig.Instance()
		
		if cfg.get('NetworkStorage', 'type') == 'mounted_filesystem':
			os.chdir( os.path.join(cfg.NetworkStorage(), path) )
			self.dbo('Set working directory: %s' % cfg.NetworkStorage())
	
	def GetThreadCount(self):
		return LuxFireConfig.Instance().getint('Renderer', 'threads_per_server')
	
	def StartMonitoringContext(self):
		threading.Thread(target=self._context_monitor).start()
	
	def _context_monitor(self):
		rendering = True
		while rendering:
			if self._lux_context.statistics('filmIsReady') == 1.0 or \
			   self._lux_context.statistics('terminated') == 1.0 or \
			   self._lux_context.statistics('enoughSamples') == 1.0:
				self._lux_context.exit()
				self._lux_context.wait()
				self._lux_context.cleanup()
				rendering = False
				self.log('Rendering finished!')
			else:
				time.sleep(5)
	
	def get_context_methods(self):
		'''
		Return the Context's methods and attributes to the client
		'''
		return self._context_methods
	
	def version(self):
		return pylux.version() #@UndefinedVariable
	
	def luxcall(self, m, *a, **k):
		'''
		Pass method calls from client to the rendering context.
		Exceptions raised by getattr() or the Context call will
		be passed down to the client.
		'''
		
		if hasattr(self._lux_context, m):
			f = getattr(self._lux_context, m)
			try:
				return f(*a, **k)
			except Exception as err:
				return str(err)
		else:
			raise NotImplementedError('Method or attribute not found')
