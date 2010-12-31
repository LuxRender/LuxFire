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
Web.Server runs the http server to run the web interface to LuxFire
"""

from .. import LuxFireConfig
from .bottle import run
from . import LuxFireWeb, WebLog

WebLog('Using static document root: %s' % LuxFireWeb._static_root)

cfg = LuxFireConfig.Instance()

LuxFireWebRunArgs = {
	'app': LuxFireWeb,
	'host': cfg.get('LuxFire', 'bind'),
	'port': cfg.getint('Web', 'port'),
}

if __name__ == '__main__':
	import optparse
	parser = optparse.OptionParser(
		prog='LuxFire.Web.Server',
		description='Run the LuxFire.Web.Server for LuxFire system administration'
	)
	parser.add_option(
		'-v',
		'--verbose',
		action='store_true',
		dest='verbose',
		default=False,
		help='Show more output'
	)
	(options, args) = parser.parse_args()
	LuxFireWebRunArgs['quiet'] = not options.verbose
	
	# This adds bottle to the sys path so that default error pages work
	import sys, os
	sys.path.insert(0, os.path.join(LuxFireWeb._data_root, os.path.pardir))
	
	run(**LuxFireWebRunArgs)