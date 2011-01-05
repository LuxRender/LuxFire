#!/usr/bin/env python3

"""
<VirtualHost *>
	ServerName luxfire.example.com

	WSGIDaemonProcess LuxFire user=www-data group=www-data processes=1 threads=5
	WSGIScriptAlias / /path/to/LuxFire/src/LuxFire/Web/Server.wsgi

	<Directory /path/to/LuxFire/src>
		WSGIProcessGroup LuxFire
		WSGIApplicationGroup %{GLOBAL}
		Order deny,allow
		Allow from all
	</Directory>
</VirtualHost>
"""

import sys, os
path_dirs = []
this_dir = os.path.dirname(__file__)
path_dirs.append(this_dir)
lf_src_dir = os.path.join( this_dir, os.path.pardir, os.path.pardir )
os.chdir( lf_src_dir )
path_dirs.append(lf_src_dir)
for p in path_dirs:
	if p not in sys.path:
		sys.path.append(p)

from LuxFire.Web import LuxFireWeb as application
