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
#------------------------------------------------------------------------------ 
# System imports
import threading
#------------------------------------------------------------------------------ 

#------------------------------------------------------------------------------ 
# Non-system imports
import wx
import Pyro.EventService.Clients
#------------------------------------------------------------------------------ 

#------------------------------------------------------------------------------
# LuxFire imports
from Client.RendererGroup import RendererGroup  
#------------------------------------------------------------------------------ 

#------------------------------------------------------------------------------ 
# Module imports
from Views.Main import MasterControllerView
#------------------------------------------------------------------------------ 

#===============================================================================
# MasterControllerController - The MasterController application Controller (mvC)
#===============================================================================
class MasterControllerController(Pyro.EventService.Clients.Subscriber):
    
    RefreshInterval = 10
    
    RefreshMethods = {
        'Renderer': RendererGroup
    }
    Slaves = {
        'Renderer': {}
    }
    
    
#================================================================================
#   INITIALISATION
#================================================================================
    
    def __init__(self, app):
        Pyro.EventService.Clients.Subscriber.__init__(self)
        
        # Initialise the main view
        self.MasterControllerView = MasterControllerView(None)
        
        # Bind methods to view's controls
        ViewBindings = [
            #(self.MasterControllerView.btnAddThread,    wx.EVT_BUTTON,  self.AddThread),
            #(self.MasterControllerView.btnDelThread,    wx.EVT_BUTTON,  self.RemoveThread),
        ]
        for ctl, evt, method in ViewBindings:
            ctl.Bind(evt, method)
        
        # Show the main view
        self.MasterControllerView.Show()
        
        # Start the Pyro Events listener
        self.subscribe('Renderer')
        self.subscriber_thread = threading.Thread(target=self.listen)
        self.subscriber_thread.daemon = True
        self.subscriber_thread.start()
        
        # Start the Timer threads
        self.RefreshSlaves()
        
#===============================================================================
#   WX VIEW EVENT HANDLERS
#===============================================================================
    
    def AddThread(self, evt):
        pass
    
    def RemoveThread(self, evt):
        pass
        
#===============================================================================
#    PYRO EVENT HANDLERS
#===============================================================================

    def event(self, event):
        print('%25s %25s %25s' % (event.time, event.subject, event.msg))
        
#===============================================================================
#    TIMED THREADS
#===============================================================================
    
    def RefreshSlaves(self):
        for Group, GroupDict in self.Slaves.items():
            self.Slaves[Group] = self.RefreshMethods[Group]()
        print('Refresh Slaves: %s' % self.Slaves)
        
        # restart the Timer
        self.slaves_timer = threading.Timer(self.RefreshInterval, self.RefreshSlaves)
        self.slaves_timer.daemon = True
        self.slaves_timer.start()
    
#===============================================================================
#   END
#===============================================================================


#===============================================================================
# If run from command line, run the application
#===============================================================================
if __name__ == '__main__':
    MasterController = wx.App(False)
    MasterControllerController(MasterController)
    MasterController.MainLoop()
#===============================================================================
# END
#===============================================================================
