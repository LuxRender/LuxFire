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
LuxFire.Database manages the database connection for persistent data storage.
"""
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from sqlalchemy.ext.declarative import declarative_base
ModelBase = declarative_base()

from .. import LuxFireConfig

class Database(object):
	_instance = None
	_sessionmaker = None
	
	@classmethod
	def CreateDatabase(cls, verbose):
		db = cls.Instance()
		db.echo = verbose
		ModelBase.metadata.create_all(db)
	
	@classmethod
	def Instance(cls, new=False):
		if cls._instance == None or new:
			cls._instance = create_engine(
				LuxFireConfig.Instance().get('LuxFire', 'database'),
				#poolclass=NullPool
			)
			
		return cls._instance
	
	@classmethod
	def Session(cls):
		if cls._sessionmaker == None:
			cls._sessionmaker = scoped_session(sessionmaker(
				bind=cls.Instance(),
				autocommit=True,
				autoflush=True
			))
		
		return cls._sessionmaker()

# Convenience contextmanager type session
class DatabaseSession(object):
	db = None
	def __enter__(self):
		#Log('Got DB Session')
		self.db = Database.Session()
		return self.db
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.db.flush()
		self.db.close()
		#Log('Release DB Session')
