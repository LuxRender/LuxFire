'''
Created on 23 Feb 2010

@author: doug
'''
import Pyro.errors


from Client import ServerLocator


def list_luxfire_components():
    try:
        LuxSlaves = ServerLocator.get_list(':Lux')
        print(LuxSlaves)
        return LuxSlaves
    except Pyro.errors.NamingError, err:
        print('Lux Pyro NS group not found - No LuxFire components are running ?')
        

if __name__ == '__main__':
    LuxSlaves = list_luxfire_components()
    l = ServerLocator.get_by_name(':Lux.%s' % LuxSlaves.pop()[0])
