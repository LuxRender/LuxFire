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
The User Model holds data about a user who is registered on the LuxFire system.
"""

from sqlalchemy import Table, Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import relationship

from .. import ModelBase

# Role is needed for relationship
from .Role import Role

roles_users = Table(
	'roles_users',
	ModelBase.metadata,
	Column('role_id', Integer(12), ForeignKey('roles.id')),
	Column('user_id', Integer(12), ForeignKey('users.id'))
)

class User(ModelBase):
	__tablename__ = 'users'
	
	id = Column(Integer(12), Sequence('user_id_seq'), primary_key=True)
	email = Column(String(128))
	password = Column(String(64))
	credits = Column(Integer(10))
	
	roles = relationship(Role, secondary=roles_users, backref='users')
	
	def __init__(self, email, password, credits):
		self.email = email
		self.password = password
		self.credits = credits
	
	def __repr__(self):
		return "<User('%s','%s')>" % (self.id, self.email)
