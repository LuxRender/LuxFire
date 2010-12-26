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
Renderer.Server exposes a LuxRender Context on the network.
"""

# LuxFire imports 
from Server import ServerObject

# LuxRender imports
from LuxRender import pylux

# Utility function for stats gatherer
import datetime
def format_elapsed_time(t):
	'''
	Format a number representing seconds into an HH:MM:SS elapsed timestamp
	'''
	
	td = datetime.timedelta(seconds=t)
	min = td.days*1440  + td.seconds/60.0
	hrs = td.days*24	+ td.seconds/3600.0
	
	return '%i:%02i:%02i' % (hrs, min%60, td.seconds%60)

class RendererServer(ServerObject):
	'''
	A Pyro server for a pylux.Context object. Access to the Context
	is via the luxcall() method, other methods in this class provide
	information about the Context
	'''
	
	# The Lux Rendering Context
	_lux_context = None
	
	# Methods available in Rendering Context
	_context_id = None
	_context_methods = []
	
	# Keep a track of rendering context threads
	_maxthreads  = 0
	_threadcount = 1
	
	def __init__(self, debug, name='', maxthreads = 0):
		'''
		Set up this server for debug mode and maxthreads limit, then
		create a Context and ask it what methods it has.
		'''
		ServerObject.__init__(self, debug=debug, name='Lux.Renderer.%08x'%id(self)) 
		
		self._maxthreads = maxthreads
		self._context_id = '%x' % id(self) # hex address of self
		self._lux_context = pylux.Context( self._context_id )
		self._context_methods = dir(self._lux_context)
	
	def __del__(self):
		'''
		If this server is killed, make sure the Context ends cleanly
		'''
		self.dbo('Lux Context exit/wait/cleanup')
		self._lux_context.exit()
		self._lux_context.wait()
		self._lux_context.cleanup() 
	
	def get_context_methods(self):
		'''
		Return the Context's methods and attributes to the client
		'''
		return self._context_methods
	
	def _PublishThreadChange(self):
		#self.publish('Renderer', ('ThreadsChange', self.name, self.threadcount))
		pass
	
	# Control the max number of rendering threads this server may start
	def _decrease_threads(self):
		'''
		If maxthreads limit is in effect, then decrease our internal
		thread count
		'''
		if self._threadcount > 1:	# do not remove the last thread, will have trouble restarting
			self._threadcount -= 1
			self._PublishThreadChange()
			return True
		else:
			return False
	
	def _increase_threads(self):
		'''
		If maxthreads limit is in effect, check that the limit has not
		been reached. If it has, return False otherwise return True
		'''
		if self._maxthreads > 0 and self._threadcount == self._maxthreads:
			return False
		
		self._threadcount += 1
		self._PublishThreadChange()
		return True
	
	def version(self):
		return pylux.version()
	
	def luxcall(self, m, *a, **k):
		'''
		Pass method calls from client to the rendering context.
		Exceptions raised by getattr() or the Context call will
		be passed down to the client.
		'''
		
		
		if m == 'removeThread': return self._decrease_threads()
		if m == 'addThread': return self._increase_threads()
		
		if hasattr(self._lux_context, m):
			f = getattr(self._lux_context, m)
			try:
				return f(*a, **k)
			except Exception as err:
				return str(err)
		else:
			raise NotImplementedError('Method or attribute not found')
	
	# Which stats to gather from the Context ? ...
	_stats_dict = {
		'secElapsed':	   0.0,
		'samplesSec':	   0.0,
		'samplesTotSec':	0.0,
		'samplesPx':		0.0,
		'efficiency':	   0.0,
		#'filmXres':		 0.0,
		#'filmYres':		 0.0,
		#'displayInterval':  0.0,
		'filmEV':		   0.0,
		#'sceneIsReady':	 0.0,
		#'filmIsReady':	  0.0,
		#'terminated':	   0.0,
	}
	
	# ... and how to format them for reading ?
	_stats_format = {
		'secElapsed':	   format_elapsed_time,
		'samplesSec':	   lambda x: 'Samples/Sec: %0.2f'%x,
		'samplesTotSec':	lambda x: 'Total Samples/Sec: %0.2f'%x,
		'samplesPx':		lambda x: 'Samples/Px: %0.2f'%x,
		'efficiency':	   lambda x: 'Efficiency: %0.2f %%'%x,
		'filmEV':		   lambda x: 'EV: %0.2f'%x,
	}
	
	# The formatted stats string
	_stats_string = ''
	
	def _compute_stats(self):
		'''
		Gather and format stats from the rendering context
		'''
		for k in self._stats_dict.keys():
			self._stats_dict[k] = self._lux_context.statistics(k)
		
		self._stats_string = ' | '.join(['%s'%self._stats_format[k](v) for k,v in self._stats_dict.items()])
		
	def get_stats_dict(self):
		'''
		Return the raw stats dict to the client 
		'''
		self._compute_stats()
		return self._stats_dict
		
	def get_stats_string(self):
		'''
		Return the formatted stats string to the client
		'''
		self._compute_stats()
		return self._stats_string
