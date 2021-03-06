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
The Web package contains the web app user interfaces used to manage the LuxFire
system, and the built in http server to run it.
"""
import sys, os
import jinja2	#@UnresolvedImport

from LuxRender import LuxLog

from ..Database import Database

if sys.version >= '3.0':
	from .bottle import bottle3 as bottle
else:
	from .bottle import bottle2 as bottle
	
def WebLog(message):
	LuxLog(message, module_name='LuxFire.Web')

LuxFireWeb = bottle.Bottle()
LuxFireWeb._data_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
LuxFireWeb._static_root = os.path.join(LuxFireWeb._data_root, 'static')
LuxFireWeb._templates_root = os.path.join(LuxFireWeb._data_root, 'templates')
LuxFireWeb._db = Database.Session()

LuxFireWeb._templater = jinja2.Environment(
	loader=jinja2.FileSystemLoader(LuxFireWeb._templates_root)
)

# Import routes from sub packages
from . import Dispatcher, Error, Renderer, User #@UnresolvedImport

@LuxFireWeb.route('/static/:path#.+#')
def server_static(path):
	return bottle.static_file(path, root=LuxFireWeb._static_root)

@LuxFireWeb.route('/favicon.ico')
def server_favicon():
	return bottle.static_file('img/favicon.ico', root=LuxFireWeb._static_root)

@LuxFireWeb.route('/')
@User.protected()
def server_index():
	return LuxFireWeb._templater.get_template('main.html').render()
