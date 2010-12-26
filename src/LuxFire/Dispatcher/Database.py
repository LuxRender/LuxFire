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
Dispatcher.Database manages the database connection for Dispatcher's persistent
data storage.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .. import LuxFireConfig

DATABASE_VERBOSE = LuxFireConfig.Instance().getboolean('Dispatcher', 'database_verbose')
AUTO_TABLE_CREATE = LuxFireConfig.Instance().getboolean('Dispatcher', 'auto_table_create')

class Database(object):
	_instance = None
	_session = None
	
	@classmethod
	def Instance(cls):
		if cls._instance == None:
			# TODO: read database configuration from file
			cls._instance = create_engine(
				LuxFireConfig.Instance().get('Dispatcher', 'database'),
				echo=DATABASE_VERBOSE
			)
			
		return cls._instance
	
	@classmethod
	def Session(cls):
		if cls._session == None:
			cls._session = sessionmaker(bind=cls.Instance())
			
		return cls._session()

ModelBase = declarative_base()