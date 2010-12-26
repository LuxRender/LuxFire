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
The Result Model holds information about rendering jobs that have been processed
by the Dispatcher.
"""

from sqlalchemy import Column, DateTime, Enum, Integer, String, Sequence, Text, ForeignKey
from sqlalchemy.orm import relationship, backref

from ..Database import Database, ModelBase, AUTO_TABLE_CREATE
from .User import User

ResultStatuses = [
	'RENDER_COMPLETE',		# Render completed without an error
	'OFFLINE',				# Job render failed because LuxFire system is offline
	'SLAVE_FAILURE',		# Job render failed because of a slave error
	'SCENE_FAILURE',		# Job render failed because of a scene error
	'NO_CREDIT'				# Job render failed due to lack of credit
]

class Result(ModelBase):
	__tablename__ = 'results'
	
	id = Column(Integer(12), Sequence('result_id_seq'), primary_key=True)
	path = Column(Text(), nullable=False)
	jobname = Column(String(128), nullable=False)
	date = Column(DateTime(), nullable=False)
	status = Column(Enum(*ResultStatuses), nullable=False)
	user_id = Column(Integer(12), ForeignKey('users.id'))
	
	user = relationship(User, backref=backref('results', order_by=id))
	
	def __repr__(self):
		return "<Queue('%s','%s')>" % (self.user.email, self.jobname)

if AUTO_TABLE_CREATE: ModelBase.metadata.create_all(Database.Instance())
