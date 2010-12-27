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
import time, threading

def LuxLog(str, module_name='Lux'):
	"""Print a message to the console, prefixed with the module_name
	and the current time.
	"""
	print("[%s %s] %s" % (time.strftime('%Y-%b-%d %H:%M:%S'), module_name, str))

class TimerThread(threading.Thread):
	"""Periodically call self.kick(). The period of time in seconds
	between calling is given by self.KICK_PERIOD, and the first call
	may be delayed by setting self.STARTUP_DELAY, also in seconds.
	self.kick() will continue to be called at regular intervals until
	self.stop() is called. Since this is a thread, calling self.join()
	may be wise after calling self.stop() if self.kick() is performing
	a task necessary for the continuation of the program.
	The object that creates this TimerThread may pass into it data
	needed during self.kick() as a dict LocalStorage in __init__().
	
	"""
	STARTUP_DELAY = 0
	KICK_PERIOD = 8
	
	active = True
	timer = None
	
	LocalStorage = None
	
	def __init__(self, LocalStorage=dict()):
		threading.Thread.__init__(self)
		self.LocalStorage = LocalStorage
	
	def set_kick_period(self, period):
		"""Adjust the KICK_PERIOD between __init__() and start()"""
		self.KICK_PERIOD = period + self.STARTUP_DELAY
	
	def stop(self):
		"""Stop this timer. This method does not join()"""
		self.active = False
		if self.timer is not None:
			self.timer.cancel()
			
	def run(self):
		"""Timed Thread loop"""
		while self.active:
			self.timer = threading.Timer(self.KICK_PERIOD, self.kick_caller)
			self.timer.start()
			if self.timer.isAlive(): self.timer.join()
	
	def kick_caller(self):
		"""Intermediary between the kick-wait-loop and kick to allow
		adjustment of the first KICK_PERIOD by STARTUP_DELAY
		
		"""
		if self.STARTUP_DELAY > 0:
			self.KICK_PERIOD -= self.STARTUP_DELAY
			self.STARTUP_DELAY = 0
		
		self.kick()
	
	def kick(self):
		"""Sub-classes do their work here"""
		pass