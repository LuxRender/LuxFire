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
# LuxFire imports 
from Server import ServerObject
#------------------------------------------------------------------------------ 
# LuxRender imports
from LuxRender import pylux
#------------------------------------------------------------------------------ 


#------------------------------------------------------------------------------
# Utility function for stats gatherer
import datetime
def format_elapsed_time(t):
    '''
    Format a number representing seconds into an HH:MM:SS elapsed timestamp
    '''
    
    td = datetime.timedelta(seconds=t)
    min = td.days*1440  + td.seconds/60.0
    hrs = td.days*24    + td.seconds/3600.0
    
    return '%i:%02i:%02i' % (hrs, min%60, td.seconds%60)
#------------------------------------------------------------------------------ 


class RendererServer(ServerObject):
    '''
    A Pyro server for a pylux.Context object. Access to the Context
    is via the luxcall() method, other methods in this class provide
    information about the Context
    '''
    
#===============================================================================
#   SERVER ATTRIBUTES
#===============================================================================
    
    # The Lux Rendering Context
    lux_context = None
    
    # Methods available in Rendering Context
    context_methods = []
    
    # Keep a track of rendering context threads
    maxthreads  = 0
    threadcount = 1
    
#================================================================================
#   SERVER STARTUP AND SHUTDOWN
#================================================================================
    
    def __init__(self, debug, maxthreads = 0):
        '''
        Set up this server for debug mode and maxthreads limit, then
        create a Context and ask it what methods it has.
        '''
        self.SetDebug(debug)
        
        self.maxthreads = maxthreads
        self.context_id = '%x' % id(self) # hex address of self
        self.lux_context = pylux.Context( self.context_id )
        self.context_methods = dir(self.lux_context)
        
    def __del__(self):
        '''
        If this server is killed, make sure the Context ends cleanly
        '''
        self.dbo('Lux Context exit/wait/cleanup')
        self.lux_context.exit()
        self.lux_context.wait()
        self.lux_context.cleanup() 

    def get_context_methods(self):
        '''
        Return the Context's methods and attributes to the client
        '''
        return self.context_methods
    
#===============================================================================
#   SERVER IMPOSED CONTEXT LIMITS
#===============================================================================

    # Control the max number of rendering threads this server may start

    def decrease_threads(self):
        '''
        If maxthreads limit is in effect, then decrease our internal
        thread count
        '''
        if self.maxthreads > 0 and self.threadcount > 0:
            self.threadcount -= 1
            
    def increase_threads(self):
        '''
        If maxthreads limit is in effect, check that the limit has not
        been reached. If it has, return False otherwise return True
        '''
        if self.maxthreads > 0:
            if self.threadcount == self.maxthreads:
                return False
            else:
                self.threadcount += 1
                return True
    
#================================================================================
#   CONTEXT INVOCATION
#================================================================================
    
    def luxcall(self, m, *a, **k):
        '''
        Pass method calls from client to the rendering context.
        Exceptions raised by getattr() or the Context call will
        be passed down to the client.
        '''
        
        f = getattr(self.lux_context, m)
        if m == 'removeThread': self.decrease_threads()
        if m == 'addThread' and not self.increase_threads():
            return False
        return f(*a, **k)
    
#===============================================================================
#   CONTEXT STATISTICS
#===============================================================================

    # Which stats to gather from the Context ? ...
    stats_dict = {
        'secElapsed':       0.0,
        'samplesSec':       0.0,
        'samplesTotSec':    0.0,
        'samplesPx':        0.0,
        'efficiency':       0.0,
        #'filmXres':         0.0,
        #'filmYres':         0.0,
        #'displayInterval':  0.0,
        'filmEV':           0.0,
        #'sceneIsReady':     0.0,
        #'filmIsReady':      0.0,
        #'terminated':       0.0,
    }
    
    # ... and how to format them for reading ?
    stats_format = {
        'secElapsed':       format_elapsed_time,
        'samplesSec':       lambda x: 'Samples/Sec: %0.2f'%x,
        'samplesTotSec':    lambda x: 'Total Samples/Sec: %0.2f'%x,
        'samplesPx':        lambda x: 'Samples/Px: %0.2f'%x,
        'efficiency':       lambda x: 'Efficiency: %0.2f %%'%x,
        'filmEV':           lambda x: 'EV: %0.2f'%x,
    }
    
    # The formatted stats string
    stats_string = ''
    
    def compute_stats(self):
        '''
        Gather and format stats from the rendering context
        '''
        for k in self.stats_dict.keys():
            self.stats_dict[k] = self.lux_context.statistics(k)
        
        self.stats_string = ' | '.join(['%s'%self.stats_format[k](v) for k,v in self.stats_dict.items()])
        
    def get_stats_dict(self):
        '''
        Return the raw stats dict to the client 
        '''
        self.compute_stats()
        return self.stats_dict
        
    def get_stats_string(self):
        '''
        Return the formatted stats string to the client
        '''
        self.compute_stats()
        return self.stats_string
    
#===============================================================================
#   END
#===============================================================================
