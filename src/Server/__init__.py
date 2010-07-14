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
# Non-System imports
# import Pyro.EventService.Clients
#------------------------------------------------------------------------------ 

class ServerObject(object): #Pyro.EventService.Clients.Publisher):
    '''
    Base Class for all Server Processes. Provides:
    def SetDebug(bool)        - Change debug on/off
    def Ping()                - Ping the object
    def dbo(str, bool)        - DeBugOutput - threadsafe print to stdout (bool==always, regardless of self.debug)
    def log(str)              - Shortcut for self.dbo(str, True)
    '''
    
#===============================================================================
#   CLASS - STATIC - ATTRIBUTES
#===============================================================================
    
    print_lock = threading.Lock()
    
#===============================================================================
#   ATTRIBUTES
#===============================================================================
    
    debug = False
    _pingval = 0
    name = ''
    
#===============================================================================
#   INITIALISATION
#===============================================================================

    def __init__(self, debug=False, name=''):
        '''
        Constructor
        '''
        #Pyro.EventService.Clients.Publisher.__init__(self)
        
        self.SetDebug(debug)
        self.SetName(name)
    
#================================================================================
#   METHODS
#================================================================================
    
    def SetName(self, name):
        self.name = name
    
    def SetDebug(self, debug):
        self.debug = bool(debug)
        
    def Ping(self):
        self._pingval+=1
        return self._pingval
    
    def dbo(self, str, always=False):
        import time
        with ServerObject.print_lock:
            if self.debug or always: print('[%s] %s %s' %(time.strftime("%Y-%m-%d %H:%M:%S"), self, str))
        
    def log(self, str):
        self.dbo(str, True)
#================================================================================
#   END
#================================================================================

class ServerThread(threading.Thread, ServerObject):
    '''
    Pyro service thread
    
    All services are started in Pyro NS with prefix Lux.*
    'service' should be instance of class to serve
    'name' is service name to register with Pyro NS
    '''
    
#===============================================================================
#   ATTRIBUTES
#===============================================================================

    service     = None  # Object to Serve (Proxy)
    name        = None  # Proxy Name
    so          = None  # Pyro Proxy URI
    daemon      = None
    
#================================================================================
#   METHODS
#================================================================================
    
    def __repr__(self):
        return '<ServerThread %s>' % self.name
    
    def setup(self, service, name):
        self.service = service
        self.name = name
        import Pyro.core
        self.daemon=Pyro.core.Daemon()
        self.so=self.daemon.register(service)
    
    def run(self):
        import Pyro.naming
        ns = Pyro.naming.locateNS()
        #try:
        #    ns.createGroup(':Lux')
        #    ns.createGroup(':Lux.Renderer')
        #except: pass
        
        #self.daemon = Pyro.core.Daemon()
        #self.daemon.useNameServer(ns)
        created = False
        while not created:
            try:
                #self.daemon.connect(self.so, self.name)
                ns.register(self.name, self.so)
                created = True
            except:
                self.log('Deleting stale NS entry: %s' % self.name)
                ns.remove(self.name)
        self.log('Serving LuxRender Context version %s' % self.service.version())
        self.daemon.requestLoop()       # Blocks until stopped externally
        
        try:
            ns.remove(self.name)
        except: pass
        finally:
            del self.so
            del self.service
            del self.daemon
            del ns
        
        self.log('Stopped')
#================================================================================
#    END
#================================================================================

    
class Server(ServerObject):
    '''
    The actual main server process that starts and stops all other services
    configured to run in this instance
    '''
    
#===============================================================================
#   ATTRIBUTES
#===============================================================================

    r_id = None
    
    # CLI_Args object containing.... CLI args
    args = None
    
    # Settings from config file
    config = None
    
    # Dict of server threads
    server_threads = {}
    
    # Server run flag (threading.Event)
    run = None
    
    # Local hostname or IP addr to use for Pyro services
    bind = None
    
#================================================================================
#   INITIALISATION
#================================================================================
    
    def __init__(self, args, config, debug=False):
        self.SetDebug(debug)
        self.args = args
        self.config = config
        
        import random
        self.r_id = '%05x' % (random.random()*9999)
    
    def __repr__(self):
        return '<Server %s~%s>' % (self.bind, self.r_id)
    
#================================================================================
#   METHODS
#================================================================================
    
    def new_server_thread(self, service, name):
        st = ServerThread()
        st.setup(service, name)
        self.server_threads[name] = st
        st.start()
    
    def start(self):
        # First set up bind address
        import Pyro
        #self.bind = self.config.get('server','bind')
        Pyro.config.PYRO_HOST = '192.168.0.164' #self.bind
        
        self.log('Server starting...')
        
        
        #===============================================================================
        #       ACTUAL SERVER OBJECT INSTATIATION HAPPENS HERE
        #===============================================================================
        if True: #self.config.getboolean('RenderServer', 'start'):
            from Server.Renderer import RendererServer
            debug = True #self.debug and self.config.getboolean('RenderServer', 'debug')
            r = RendererServer(debug=debug)
            self.new_server_thread(r, r.name)
        #------------------------------------------------------------------------------ 
        
        
        try:
            import threading
            self.run = threading.Event()
            while not self.run.is_set():
                self.run.wait(10)
        except KeyboardInterrupt:
            self.run.set()
        finally:
            self.log('Server Shutdown')
            
            # first signal shutdowns, and then attempt thread join in reverse order
            # we do this to help prevent exceptions at shutdown time from services
            # calling others that are no longer present
            thread_list = list(self.server_threads.items())
            thread_list.reverse()
            for serv, thread in thread_list:
                thread.daemon.shutdown()
                
            #import time
            #time.sleep(2)
            for serv, thread in thread_list:
                thread.join()
            self.log('...finished')
    
#===============================================================================
#   END
#===============================================================================
