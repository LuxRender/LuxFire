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

import datetime
from sqlalchemy.sql.expression import desc

from ..Database import Database
from ..Database.Models.Queue import Queue
from ..Database.Models.Result import Result

from ..Server import ServerObject

from LuxRender import LuxLog

def DispatcherLog(message):
	LuxLog(message, module_name='LuxFire.Dispatcher')

class Dispatcher(ServerObject):
	_Service_Type = 'Dispatcher'
	
	db = Database.Session()
	
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
