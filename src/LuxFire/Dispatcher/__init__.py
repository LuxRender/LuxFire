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
Dispatcher is a Render Queue/Job manager and dispatcher for Renderer.Servers.
"""

import datetime, glob, os, shutil, threading, time
from sqlalchemy.sql.expression import desc #@UnresolvedImport
from sqlalchemy.orm import eagerload #@UnresolvedImport

from LuxRender import LuxLog, TimerThread
import Pyro.errors

from .. import LuxFireConfig, clean_file_name
from ..Client import ClientException
from ..Database import Database, DatabaseSession
from ..Database.Models.Queue import Queue
from ..Database.Models.Result import Result
from ..Database.Models.UserSession import UserSession
from ..Renderer.Client import RendererGroup
from ..Server import ServerObject, ServerObjectThread

def DispatcherLog(message):
	LuxLog(message, module_name='LuxFire.Dispatcher')

class DispatcherDistributor(ServerObjectThread):
	_Service_Type = 'DispatcherDistributor'
	
	qi_id = None
	
	#@class var
	path_create_lock = threading.Lock()
	
	def __repr__(self):
		return '<DispatcherDistributor %s>' % self.qi_id
	
	def run(self):
		with DatabaseSession() as db:
			
			qi = db.query(Queue).filter(Queue.id==self.qi_id).one()
			
			cfg = LuxFireConfig.Instance()
			
			self.dbo('Distributing data')
			
			try:
				# At this point in time, qi.path is located in LocalStorage
				in_path = os.path.realpath( os.path.join( cfg.LocalStorage(), qi.path ) )
				if not os.path.exists( in_path ):
					raise Exception('Data not found for this item!')
				
				lxs_files = glob.glob( os.path.join(in_path, '*.lxs') )
				if len(lxs_files) == 0:
					raise Exception('No LXS file found in LocalStorage path %s' % in_path)
				
				self.dbo('in_path = "%s"' % in_path)
				
				# TODO: this copy mechanism will need to be swapped out depending
				# on the network storage technology used; eg. for cloud storage etc
				
				if cfg.get('NetworkStorage', 'type') == 'mounted_filesystem':
					if not os.path.exists( cfg.NetworkStorage() ):
						raise Exception('Network data path not valid!')
					
					out_path = os.path.join( cfg.NetworkStorage(), qi.path )
					self.dbo('out_path = "%s"' % out_path)
					
					# if writing to NetworkStorage is going to fail, lets find out here first
					network_user_dir = os.path.join( cfg.NetworkStorage(), '%i'%qi.user.id )
					
					# Using a lock here prevents thread race in makedirs()
					with DispatcherDistributor.path_create_lock:
						if not os.path.exists( network_user_dir ):
							os.makedirs(network_user_dir)
					
					if os.path.exists( out_path ):
						# copytree doesn't like the destination to exist, raise a
						# warning and remove it first
						self.log('Target path exists, removing and re-copying')
						shutil.rmtree( out_path )
					
					shutil.copytree(in_path, out_path)
				
				qi.status_data = os.path.basename(lxs_files[0])
			
				# Now self.qi.path refers to a scene file in NetworkStorage
				qi.status = 'READY'
				self.dbo('Data ready')
				
			except Exception as err:
				self.log('Data copy failed: %s' % err)
				qi.status = 'ERROR'
				qi.status_data = '%s'%err

class DispatcherWorker(ServerObjectThread):
	_Service_Type = 'DispatcherWorker'
	
	renderer_servers = None
	
	_render_start_threads = []
	_distributor_threads = []
	
	def __repr__(self):
		return '<DispatcherWorker>'
	
	def run(self):
		# Strategies for dealing with each Queue item in the queue table
		# according to its status field
		status_handlers = {
			# Handled by User/UI -> UPLOADING
			'NEW':			self.handler_NULL,
			
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
		
		try:
			# Discover Renderer servers. This will fail if the nameserver cannot
			# be found, in which case, we're not going to be able to Dispatch any
			# work!
			self.renderer_servers = RendererGroup()
		except (ClientException, Pyro.errors.PyroError) as err:
			self.renderer_servers = {}
			self.log('Cannot Dispatch any new work: %s' % err)
			# return # don't abort, we can still process/distribute some Queue items
		
		with DatabaseSession() as db:
			
			limit = LuxFireConfig.Instance().getint('Dispatcher', 'max_items_per_worker')
			
			# TODO: limit = min( len(self.renderer_servers), limit ) ?
			
			# Only grab a few records at a time
			self.dbo('Fetching %i items' % limit)
			aqi = db.query(Queue).order_by(Queue.date).limit(limit).all()
			
			self.dbo('Processing RENDERING items:')
			# Process the RENDERING items first, so that we can free up Renderer.Servers
			# Doing this separately is actually essential for proper resuming of Dispatcher
			# if it gets interrupted
			for rqi in aqi:
				if rqi.status != 'RENDERING': continue
				self.dbo(' %s' % rqi)
				status_handlers[rqi.status](rqi)
			
			db.flush()
			
			self.dbo('Processing OTHER items:')
			# Order by Queue.date ensures oldest items are rendered first
			for oqi in aqi:
				if oqi.status == 'RENDERING': continue
				self.dbo(' %s' % oqi)
				status_handlers[oqi.status](oqi)
			
			db.flush()
			
			# Now we can safely wait for child threads to complete
			for rst in self._render_start_threads:
				if rst.is_alive():
					rst.join()
			for ddt in self._distributor_threads:
				if ddt.is_alive():
					ddt.join()
			
			self.dbo('Finished')
	
	# Warning: do not call server.wait() in any of these handlers!
	# The Dispatcher should be mostly stateless such that if it is stopped and
	# restarted (or if there is more than one Dispatcher running on the network),
	# everything picks up where it left off.
	
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
		dd.qi_id = qi.id
		self._distributor_threads.append(dd)
		dd.start()
	
	def handler_READY(self, qi):
		"""READY action:
		Find an available rendering server and start the rendering process;
		change status to RENDERING.
		
		If there are no available servers, we can safely do nothing here, and
		wait for the next DispatcherTimer kick.
		"""
		for renderer_server_name, (RC, proxy) in self.renderer_servers.items():
			if RC.getAttribute('renderer', 'name') == 0:
				# This server is idle! Bag it!
				del self.renderer_servers[renderer_server_name]
				
				scene_path = '%s'%qi.path
				scene_name = '%s'%qi.status_data
				
				qi.status = 'RENDERING'
				qi.status_data = renderer_server_name
				
				# Set up the rendering in another thread, lets get these records
				# processed ASAP!
				rst = threading.Thread(
					target=self.start_server,
					args=(RC, renderer_server_name, proxy, scene_path, scene_name, qi.haltspp, qi)
				)
				self._render_start_threads.append(rst)
				rst.start()
				
				break
	
	def handler_RENDERING(self, qi):
		"""RENDERING action:
		Check up on the server which is rendering this scene and see if it
		has finished or not. If it has finished, remove the scene data from
		LocalStorage and NetworkStorage, and move the job to the Results table.
		"""
		self.dbo('RENDERING handler: %s' % qi)
		renderer_server_name = qi.status_data
		if renderer_server_name in self.renderer_servers.keys():
			RC, proxy = self.renderer_servers[renderer_server_name]	#@UnusedVariable
			if RC.getAttribute('renderer', 'name') == 0:
				# Rendering must have finished!
				with DatabaseSession() as db:
					ri = Result()
					ri.date = datetime.datetime.now()
					ri.jobname = qi.jobname
					ri.path = qi.path
					ri.status = 'RENDER_COMPLETE'
					ri.user_id = qi.user_id
					db.add(ri)
					db.delete(qi)
			else:
				# Renderer.Server is busy, print out what it's doing
				self.dbo('%s: %s' % (renderer_server_name, RC.printableStatistics(True)))
				# Make server unavailable for further actions
				del self.renderer_servers[renderer_server_name]
		else:
			qi.status = 'ERROR'
			qi.status_data = 'Renderer.Server disappeared?'
			self.dbo('Rendering error: %s' % qi)
	
	def start_server(self, server, server_name, proxy, net_path, scene_file, haltspp, qi):
		"""
		This method runs as a thread because of the while..sleep loop
		"""
		proxy.SetNetworkWD(net_path)
		server.parse(scene_file, True) # async parse
		
		while server.statistics('sceneIsReady') != 1.0:
			time.sleep(0.3)
			if not server.parseSuccessful():
				qi.status = 'ERROR'
				qi.status_data = 'Bad scene file (parse error)'
				self.log('%s' % qi) # str(qi) contains the error message
				return
		
		# Set termination criteria
		server.setHaltSamplesPerPixel(haltspp, False, True)
		
		# Get Server up to configured speed
		# 1 is subtracted from GetThreadCouny because parse() already created
		# a thread for us
		for i in range(proxy.GetThreadCount()-1):	#@UnusedVariable
			server.addThread()
		
		# StartMonitoringContext is essential so that the Renderer.Server can
		# monitor and clean itself up when the rendering completes
		proxy.StartMonitoringContext()
		self.log('Started %s/%s on render server %s' % (net_path, scene_file, server_name))

class DispatcherTimer(TimerThread, ServerObject):
	"""
	This Timer will spawn worker threads at regular intervals
	"""
	
	def __repr__(self):
		return '<DispatcherTimer>'
	
	KICK_PERIOD = LuxFireConfig.Instance().getint('Dispatcher', 'process_interval')
	
	_worker_pool = []
	
	def _purge_threads(self, join=False):
		for old_dwt in [t for t in self._worker_pool]: # copy the list or remove() might not work
			if join: old_dwt.join()
			if not old_dwt.is_alive():
				self._worker_pool.remove(old_dwt)
	
	def kick(self):
		self.dbo('Kick!')
		self._purge_threads()
		
		dwt = DispatcherWorker(debug=self.debug)
		self._worker_pool.append(dwt)
		dwt.start()
		self.dbo('Have %i DispatcherWorkers' % len(self._worker_pool))
	
	def stop(self):
		TimerThread.stop(self)
		self._purge_threads(join=True)

class Dispatcher(ServerObject):
	"""
	When running in Server mode, the Dispatcher will start a timer to spawn
	worker threads which will process the Queue.
	"""
	
	_Service_Type = 'Dispatcher'
	
	timer = DispatcherTimer()
	
	def _verify_user_key(self, user_id, d_key):
		"""
		Verify that a user request contains the correct
		key for authentication. Raises ClientException
		on failure.
		"""
		verified = False
		with DatabaseSession() as db:
			us = db.query(UserSession).filter(UserSession.user_id==user_id).all()
			for user_session in us:
				if 'dispatcher_key' in user_session.session_data.keys() and user_session.session_data['dispatcher_key']==d_key:
					verified = True
					
					# Remove the key from the session once found
					del user_session.session_data['dispatcher_key']
					db.add(user_session)
					break
		if not verified:
			raise ClientException('Dispatcher session authentication failure')
	
	# All dispatcher methods need to RETURN values, and not use *Log or print
	# so the the methods are servable over the network
	
	def add_queue(self, user_id, d_key, jobname, haltspp=-1, halttime=-1):
		self._verify_user_key(user_id, d_key)
		
		with DatabaseSession() as db:
			existing = db.query(Queue).filter(Queue.user_id==user_id).filter(Queue.jobname==jobname).count()
		if existing > 0:
			raise ClientException('Job with that name already exists')
		
		q = Queue()
		q.user_id = user_id
		q.path = os.path.join('%i'%user_id, clean_file_name(jobname))
		q.jobname = jobname
		q.haltspp = haltspp
		q.halttime = halttime
		q.date = datetime.datetime.now()
		q.status = 'NEW'
		with DatabaseSession() as db:
			db.add(q)
		return True
	
	def finalise_queue(self, user_id, d_key, jobname):
		self._verify_user_key(user_id, d_key)
		
		# TODO: check correct q.state and if any files have been uploaded !
		with DatabaseSession() as db:
			q = db.query(Queue).filter(Queue.user_id==user_id).filter(Queue.jobname==jobname).one()
			# If not exactly one q found, exception will be passed back to user
			q.status = 'PENDING'
			q.status_data = ''
		return True
	
	def abort_queue(self, user_id, d_key, jobname):
		"""Prevent an item from getting to RENDERING STATUS.
		Can only be done if current status is READY, by changing status back to NEW"""
		self._verify_user_key(user_id, d_key)
		
		with DatabaseSession() as db:
			q = db.query(Queue).filter(Queue.user_id==user_id).filter(Queue.jobname==jobname).one()
			# If not exactly one q found, exception will be passed back to user
			if q.status == 'READY':
				q.status = 'ERROR'
				q.status_data = 'Aborted'
		return True
	
	def reset_queue(self, user_id, d_key, jobname):
		"""Reset an item back to NEW status from ERROR for another go"""
		self._verify_user_key(user_id, d_key)
		
		with DatabaseSession() as db:
			q = db.query(Queue).filter(Queue.user_id==user_id).filter(Queue.jobname==jobname).one()
			# If not exactly one q found, exception will be passed back to user
			if q.status == 'ERROR':
				q.status = 'NEW'
				q.status_data = ''
		return True
	
	def add_file(self, user_id, d_key, jobname, filename, filedata):
		"""Receive file data for the Queue item"""
		self._verify_user_key(user_id, d_key)
		
		with DatabaseSession() as db:
			q = db.query(Queue).filter(Queue.user_id==user_id).filter(Queue.jobname==jobname).one()
			if q.status != 'NEW':
				raise Exception('Wrong queue status for file upload!')
			
			job_path = os.path.join( LuxFireConfig.Instance().LocalStorage(), q.path )
			if not os.path.exists(job_path):
				os.makedirs(job_path)
			file_path = os.path.join(job_path, filename)
			with open(file_path, 'wb') as file:
				file.write(filedata)
		
		return True
	
	def list_queue(self):
		return Database.Session().query(Queue).options(eagerload('user')).order_by(desc(Queue.id)).all()
	
	def list_results(self):
		return Database.Session().query(Result).options(eagerload('user')).order_by(desc(Result.id)).all()
	
	def _start(self):
		"""Start up the server loop thread"""
		self.timer.SetDebug(self.debug)
		self.timer.start()
	
	def _stop(self):
		"""Stop the server thread loop"""
		self.timer.stop()
		if self.timer.isAlive(): self.timer.join()
