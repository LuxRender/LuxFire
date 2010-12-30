#!/usr/bin/env python3


"""
THIS INTERFACE HAS NOT BEEN TESTED YET !
"""


"""
<VirtualHost *>
    ServerName luxfire.example.com

    WSGIDaemonProcess yourapp user=www-data group=www-data processes=1 threads=5
    WSGIScriptAlias / /path/to/LuxFire/Web/Server.wsgi

    <Directory /path/to/LuxFire/Web>
        WSGIProcessGroup LuxFire
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>
</VirtualHost>
"""

os.chdir(os.path.dirname(__file__))

from . import LuxFireWeb

application = LuxFireWeb
