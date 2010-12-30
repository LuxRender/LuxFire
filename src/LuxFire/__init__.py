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
		'process_interval': '5',
		'max_items_per_worker': '10',
	},
	'Renderer': {
		'threads_per_server': '4'
	},
	'Web': {
		'port': '9080'
	},
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

def clean_file_name(name, replace="_"):
	"""
	Returns a name with characters replaced that may cause problems under
	various circumstances, such as writing to a file. All characters besides
	A-Z/a-z, 0-9 are replaced with "_" or the replace argument if defined.
	
	'Borrowed' from the Blender source tree
	"""

	unclean_chars = \
		"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\
		\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\
		\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\
		\x2e\x2f\x3a\x3b\x3c\x3d\x3e\x3f\x40\x5b\x5c\x5d\x5e\x60\x7b\
		\x7c\x7d\x7e\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\
		\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\
		\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\
		\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\
		\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\
		\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\
		\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\
		\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\
		\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe"
	
	for ch in unclean_chars:
		name = name.replace(ch, replace)
	
	return name
