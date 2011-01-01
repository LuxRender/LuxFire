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
The Queue Model holds data about rendering jobs that are yet to be processed by
LuxFire.Dispatcher.
"""

from sqlalchemy import Column, DateTime, Enum, Integer, String, Sequence, Text, ForeignKey, UniqueConstraint #@UnresolvedImport
from sqlalchemy.orm import relationship, backref #@UnresolvedImport

from .. import ModelBase
from .User import User

QueueStatuses = [
	'NEW',				# User has just created the job
	'UPLOADING',		# User is uploading the scene
	'PENDING',			# User has uploaded, scene is pending processing
	'DISTRIBUTING',		# Dispatcher is transferring scene to network storage
	'READY',			# Scene is ready to render
	'RENDERING',		# Scene is rendering
	# There's no 'completed' status since the job will be moved to Results table
	'ERROR'				# An error occurred while processing the job
]

class Queue(ModelBase):
	__tablename__ = 'queue'
	__table_args__ = (
		UniqueConstraint('user_id', 'jobname'),
		{}
	)
	
	id = Column(Integer(12), Sequence('queue_id_seq'), primary_key=True)
	haltspp = Column(Integer(8), default=-1)
	halttime = Column(Integer(8), default=-1)
	path = Column(Text(), nullable=False)
	jobname = Column(String(128), nullable=False)
	date = Column(DateTime(), nullable=False)
	status = Column(Enum(*QueueStatuses), nullable=False)
	status_data = Column(Text(), nullable=True)
	user_id = Column(Integer(12), ForeignKey('users.id'))
	
	user = relationship(User, backref=backref('queue', order_by=id))
	
	def __repr__(self):
		return "<Queue('%s','%s', %s:%s)>" % (self.user.email, self.jobname, self.status, self.status_data)
