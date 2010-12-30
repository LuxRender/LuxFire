#!/usr/bin/env python3
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
Python setup/installer script for LuxFire suite.
"""

from distutils.core import setup
import os

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

luxfire_packages = find_packages('src')

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
	packages=luxfire_packages.keys()
)