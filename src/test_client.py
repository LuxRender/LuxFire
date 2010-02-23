'''
Created on 23 Feb 2010

@author: doug
'''
import Pyro.errors


from Client import ServerLocator, RemoteLuxWrapper


def list_luxfire_components():
    try:
        LuxSlaves = ServerLocator.get_list(':Lux')
        print(LuxSlaves)
        return LuxSlaves
    except Pyro.errors.NamingError, err:
        print('Lux Pyro NS group not found - No LuxFire components are running ?')
        return []
        

if __name__ == '__main__':
    LuxSlavesNames = list_luxfire_components()
    
    if len(LuxSlavesNames) > 0:
        slaves = []
        for LN, i in LuxSlavesNames:
            if LN.startswith('Renderer'):
                slaves.append( RemoteLuxWrapper(ServerLocator.get_by_name(':Lux.%s' % LN)) )
    else:
        print('No remote Lux components available')
