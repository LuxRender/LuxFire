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