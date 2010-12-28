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
LuxFire is a distributed network rendering and rendering management system for
LuxRender.
"""
import configparser, platform

from LuxRender import LuxLog

def LuxFireLog(message):
	LuxLog(message, module_name='LuxFire')

DefaultConfig = {
	'LuxFire': {
		# Default bind address is localhost only, services will not be broadcast!
		'bind': '127.0.0.1',
		'database': 'sqlite:///db_luxfire.sqlite3',
	},
	'LocalStorage': {
		# Configurable per platform.system()
		'linux': '../incoming',
		'darwin': '../incoming',
		'windows': '../incoming'
	},
	'NetworkStorage': {
		'type': 'mounted_filesystem',
		
		# Configurable per platform.system()
		'linux': '/mnt/network_location/LuxFire',
		'darwin': '/Volumes/Network_Drive/LuxFire',
		'windows': 'N:/LuxFire'
	},
	'Dispatcher': {
		'process_interval': 5
	}
}

class LuxFireConfig(configparser.SafeConfigParser):
	_instance = None
	
	filename = 'luxfire.cfg'
	
	@classmethod
	def Instance(cls):
		if cls._instance == None:
			cls._instance = cls()
			cls._instance.read(cls.filename)
			# Populate with defaults
			for k_s, v_s in DefaultConfig.items():
				if not cls._instance.has_section(k_s):
					cls._instance.add_section(k_s)
				for k_i, v_i in v_s.items():
					if not cls._instance.has_option(k_s, k_i):
						cls._instance.set(k_s, k_i, v_i)
		
		return cls._instance
	
	def Save(self):
		with open(self.filename, 'w') as cf:
			self.write(cf)
	
	def NetworkStorage(self):
		"""Helper method to get NetworkStorage path applicable to this system"""
		
		return self.get('NetworkStorage', platform.system().lower())
	
	def LocalStorage(self):
		"""Helper method to get LocalStorage path applicable to this system"""
		
		return self.get('LocalStorage', platform.system().lower())
