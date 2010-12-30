#!/usr/bin/env python3
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

from distutils.core import setup
from distutils.command.install_data import install_data
import imp, os

#------------------------------------------------------------------------------ 
# Helper functions
#------------------------------------------------------------------------------
def is_package(path):
	return (
		os.path.isdir(path) and
		os.path.isfile(os.path.join(path, '__init__.py'))
		)

def find_packages(path, base="" ):
	""" Find all packages in path """
	packages = {}
	for item in os.listdir(path):
		dir = os.path.join(path, item)
		if is_package( dir ):
			if base:
				module_name = "%(base)s.%(item)s" % vars()
			else:
				module_name = item
			packages[module_name] = dir
			packages.update(find_packages(dir, module_name))
	return packages

class smart_install_data(install_data):
	def run(self):
		#need to change self.install_dir to the library dir
		install_cmd = self.get_finalized_command('install')
		self.install_dir = getattr(install_cmd, 'install_lib')
		return install_data.run(self)

def non_python_files(path):
	""" Return all non-python-file filenames in path """
	result = []
	all_results = []
	module_suffixes = [info[0] for info in imp.get_suffixes()]
	ignore_dirs = ['cvs']
	for item in os.listdir(path):
		name = os.path.join(path, item)
		if (
			os.path.isfile(name) and
			os.path.splitext(item)[1] not in module_suffixes
			):
			result.append(name)
		elif os.path.isdir(name) and item.lower() not in ignore_dirs:
			all_results.extend(non_python_files(name))
	if result:
		all_results.append((path, result))
	return all_results


#------------------------------------------------------------------------------ 
# LuxFire Setup description
#------------------------------------------------------------------------------ 
luxfire_packages = find_packages('src')
luxfire_data = non_python_files('./src/LuxFire/Web/data')

desc="""
LuxFire Distributed Rendering System
------------------------------------

LuxFire is a multi-component distributed network rendering system for the LuxRender
rendering engine. The primary components are the Renderer interface for the
rendering engine and the Dispatcher rendering queue manager.
"""

setup(
	name='LuxFire',
	version='0.1',
	url='http://www.luxrender.net/',
	maintainer='Doug Hammond',
	maintainer_email='doughammond NOSPAM -AT- NOSPAM blueyonder.co.uk',
	long_description=desc,
	
	requires = ['sqlalchemy (>= 0.6)', 'jinja2 (>=2.5)'],
	provides = ['luxfire'],
	
	package_dir={'': 'src'},
	py_modules=['luxfire_standalone'],
	packages=luxfire_packages.keys(),
	
	data_files=luxfire_data,
	cmdclass={'install_data':smart_install_data}
)