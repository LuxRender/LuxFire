class ClientException(Exception):
    pass

class ServerLocator(object):
    '''
    Locate a remote pyro service by name using a pyro NS
    '''
    
    # Pyro Name server
    ns = None
    
    def __init__(self):
        '''
        Locate the NS
        '''
        
        import Pyro.core
        import Pyro.naming
        locator = Pyro.naming.NameServerLocator()
        try:
            self.ns = locator.getNS()
        except Pyro.errors.NamingError, err:
            raise ClientException('FATAL ERROR: Cannot find Pyro NameServer')
    
    def get_by_name(self, name):
        '''
        Get a remote service by name
        '''
        
        if self.ns is not None:
            uri = self.ns.resolve(name)
            return uri.getAttrProxy()
    
    def get_list(self, group):
        '''
        Get the list of all found services
        '''
        
        if self.ns is not None:
            return self.ns.list(group)

ServerLocator = ServerLocator()

class RemoteCallable(object):
    remote_method   = None
    def __init__(self, RemoteRenderer, remote_method):
        self.RemoteRenderer = RemoteRenderer
        self.remote_method = remote_method
    
    def __call__(self, *a, **k):
        return self.RemoteRenderer.luxcall(self.remote_method, *a, **k)

class RemoteLuxWrapper(object):
    RemoteMethod = None
    
    def __init__(self, RemoteRenderer):
        self.RemoteRenderer = RemoteRenderer
        
    def __getattr__(self, m):
        return RemoteCallable(self.RemoteRenderer, m)