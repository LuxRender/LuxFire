'''
Created on 23 Feb 2010

@author: doug
'''

from Server import ServerObject
from LuxRender import pylux

class Renderer(ServerObject):
    
    def __init__(self, debug):
        self.SetDebug(debug)
        
        self.context_id = '%x' % id(self) # hex address of self
        self.lux_context = pylux.Context( self.context_id )

    def luxcall(self, m, *a, **k):
        try:
            f = getattr(self.lux_context, m)
            return f(*a, **k)
        except Exception, err:
            return err