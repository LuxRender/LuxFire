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
by LuxFire.Dispatcher.
"""
import datetime

from sqlalchemy import Column, DateTime, Integer, PickleType, Sequence, Text, ForeignKey
from sqlalchemy.orm import relationship, backref

from .. import DatabaseSession, ModelBase
from .User import User

class UserSession(ModelBase):
	__tablename__ = 'user_sessions'
	
	id = Column(Integer(12), Sequence('user_sessions_id_seq'), primary_key=True)
	sess_id = Column(Text(32))
	user_id = Column(Integer(12), ForeignKey('users.id'))
	expiry = Column(DateTime(), nullable=False)
	session_data = Column(PickleType())
	
	user = relationship(User, backref=backref('user_sessions', order_by=id))
	
	def __repr__(self):
		if self.user:
			return "<UserSession('%s'(%s))>" % (self.user.email, len(self.session_data))
		else:
			return "<UserSession()>"
	
	@staticmethod
	def delete_old_sessions():
		with DatabaseSession() as db:
			db.query(UserSession).filter(UserSession.expiry<datetime.datetime.now()).delete()
