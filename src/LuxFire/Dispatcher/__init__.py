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
Dispatcher is a Render Queue/Job manager and dispatcher for Renderer Slaves.
"""

import datetime, os, shutil
from sqlalchemy.sql.expression import desc

from .. import LuxFireConfig
from ..Database import Database
from ..Database.Models.Queue import Queue
from ..Database.Models.Result import Result

from ..Server import ServerObject, ServerObjectThread

from LuxRender import LuxLog, TimerThread

def DispatcherLog(message):
	LuxLog(message, module_name='LuxFire.Dispatcher')

class DispatcherDistributor(ServerObjectThread):
	_Service_Type = 'DispatcherDistributor'
	
	qi = None
	
	def __repr__(self):
		return '<DispatcherDistributor %s>' % self.qi
	
	def run(self):
		cfg = LuxFireConfig.Instance()
		
		self.dbo('Distributing data')
		
		try:
			# At this point in time, self.qi.path is located in LocalStorage
			in_path = os.path.realpath( os.path.join( cfg.LocalStorage(), self.qi.path ) )
			if not os.path.exists( in_path ):
				raise Exception('Data for this item not found on this machine!')
			
			self.dbo('in_path = "%s"' % in_path)
			
			# TODO: this copy mechanism will need to be swapped out depending
			# on the network storage technology used; eg. for cloud storage etc
			
			if cfg.get('NetworkStorage', 'type') == 'mounted_filesystem':
				if not os.path.exists( cfg.NetworkStorage() ):
					raise Exception('Network data path not valid!')
				
				out_path = os.path.join( cfg.NetworkStorage(), self.qi.path )
				self.dbo('out_path = "%s"' % out_path)
				
				# if writing to NetworkStorage is going to fail, lets find out here first
				network_user_dir = os.path.join( cfg.NetworkStorage(), '%i'%self.qi.user.id )
				if not os.path.exists( network_user_dir ):
					os.makedirs(network_user_dir)
				
				if os.path.exists( out_path ):
					# copytree doesn't like the destination to exist, raise a
					# warning and remove it first
					self.log('Target path exists, removing and re-copying')
					shutil.rmtree( out_path )
				
				shutil.copytree(in_path, out_path)
		
		except Exception as err:
			self.log('Data copy failed: %s' % err)
			self.qi.status = 'ERROR'
			return
		
		# Now self.qi.path refers to a point in NetworkStorage
		self.qi.status = 'READY'
		self.dbo('Data ready')

class DispatcherWorker(ServerObjectThread):
	_Service_Type = 'DispatcherWorker'
	
	db = Database.Session()
	
	def __repr__(self):
		return '<DispatcherWorker>'
	
	def run(self):
		# Strategies for dealing with each Queue item in the queue table
		# according to its status field
		status_handlers = {
			# Handled by User/UI -> UPLOADING
			'NEW':			self.handler_PENDING, #,	# TODO: TESTING
			
			# Handled by User/UI -> PENDING
			'UPLOADING':	self.handler_NULL,
			
			# Change to DISTRIBUTING and pass to a DispatcherDistributor
			'PENDING':		self.handler_PENDING,
			
			# item is being handled by a DispatcherDistributor, no action needed
			'DISTRIBUTING': self.handler_NULL,
			
			# item ready for rendering
			'READY':		self.handler_READY,
			
			# item is rendering
			'RENDERING':	self.handler_RENDERING,
			
			# fault with item
			'ERROR':		self.handler_NULL,
		}
		
		for qi in self.db.query(Queue).order_by(desc(Queue.id)).all():
			status_handlers[qi.status](qi)
	
	def handler_NULL(self, qi):
		"""NULL action, do nothing with this item"""
		self.dbo('Nothing to do for %s' % qi)
	
	def handler_PENDING(self, qi):
		"""PENDING action:
		Change status to DISTRIBUTING and copy the scene to NetworkStorage
		"""
		self.dbo('PENDING handler for %s' % qi)
		qi.status = 'DISTRIBUTING'
		dd = DispatcherDistributor(debug=self.debug)
		dd.qi = qi
		dd.start()
	
	def handler_READY(self, qi):
		"""READY action:
		Find an available rendering slave and start the rendering process.
		If there are no available slaves, we can safely do nothing here, and
		wait for the next DispatcherTimer kick.
		"""
		pass
	
	def handler_RENDERING(self, qi):
		"""RENDERING action:
		Check up on the slave which is rendering this scene and see if it
		has finished or not. If it has finished, remove the scene data from
		LocalStorage and NetworkStorage, and move the job to the Results table.
		"""
		pass

class DispatcherTimer(TimerThread, ServerObject):
	"""
	This Timer will spawn worker threads at regular intervals
	"""
	
	def __repr__(self):
		return '<DispatcherTimer>'
	
	KICK_PERIOD = 5
	
	def kick(self):
		self.dbo('Kick!')
		DispatcherWorker(debug=self.debug).start()

class Dispatcher(ServerObject):
	"""
	When running in Server mode, the Dispatcher will start a timer to spawn
	worker threads which will process the Queue.
	"""
	
	_Service_Type = 'Dispatcher'
	
	db = Database.Session()
	
	timer = DispatcherTimer()
	
	# All dispatcher methods need to RETURN values, and not use *Log or print
	# so the the methods are servable over the network
	
	def add_queue(self, user_id, path, jobname, haltspp=-1, halttime=-1):
		q = Queue()
		q.user_id = user_id
		q.path = path
		q.jobname = jobname
		q.haltspp = haltspp
		q.halttime = halttime
		q.date = datetime.datetime.now()
		q.status = 'NEW'
		return self.db.add(q)
	
	def list_queue(self):
		return self.db.query(Queue).order_by(desc(Queue.id)).all()
	
	def list_results(self):
		return self.db.query(Result).order_by(desc(Result.id)).all()
	
	def _start(self):
		"""Start up the server loop thread"""
		self.timer.SetDebug(self.debug)
		self.timer.start()
	
	def _stop(self):
		"""Stop the server thread loop"""
		self.timer.stop()
		if self.timer.isAlive(): self.timer.join()
