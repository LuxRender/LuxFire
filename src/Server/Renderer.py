'''
Created on 23 Feb 2010

@author: doug
'''

from Server import ServerObject
import pylux

class Renderer(ServerObject):
    def __init__(self, debug):
        self.SetDebug(debug)
        
        self.lux_context = pylux.Context('%08x'%id(self))
        
    def luxcall(self, method, *args, **kwargs):
        if hasattr(self.lux_context, method):
            f = getattr(self.lux_context, method)
            self.dbo('Calling %s' % method)
            try:
                return f(*args, **kwargs)
            except Exception, err:
                return str(err)
        else:
            self.dbo('Lux context has no method %s' % method)
            return False
