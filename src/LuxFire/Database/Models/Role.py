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
The Role Model is a description of a permission that may be granted to a User.
"""

from sqlalchemy import Column, Integer, String, Sequence

from .. import ModelBase

class Role(ModelBase):
	__tablename__ = 'roles'
	
	id = Column(Integer(12), Sequence('role_id_seq'), primary_key=True)
	name = Column(String(32))
	description = Column(String(128))
	
	def __init__(self, name, description):
		self.name = name
		self.description = description
	
	def __repr__(self):
		return "<Role('%s')>" % (self.name)
