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
from sqlalchemy import Column, Integer, String, Sequence, Text, ForeignKey
from sqlalchemy.orm import relationship, backref

from Dispatcher.Database import Database, ModelBase
from Dispatcher.Models.User import User

class Queue(ModelBase):
	__tablename__ = 'queue'
	
	id = Column(Integer(12), Sequence('queue_id_seq'), primary_key=True)
	haltspp = Column(Integer(8), default=-1)
	halttime = Column(Integer(8), default=-1)
	path = Column(Text(), nullable=False)
	jobname = Column(String(128), nullable=False)
	date = Column(Integer(12), nullable=False)
	status = Column(String(32), nullable=False)
	user_id = Column(Integer(12), ForeignKey('users.id'))
	
	user = relationship(User, backref=backref('queue', order_by=id))
	
	def __repr__(self):
		return "<Queue('%s','%s')>" % (self.user.email, self.jobname)

ModelBase.metadata.create_all(Database.Instance())
