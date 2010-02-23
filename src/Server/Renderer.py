'''
Created on 23 Feb 2010

@author: doug
'''

from Server import ServerObject
from LuxRender import pylux

import datetime
def format_elapsed_time(t):
    td = datetime.timedelta(seconds=t)
    min = td.days*1440  + td.seconds/60.0
    hrs = td.days*24    + td.seconds/3600.0
    
    return '%i:%02i:%02i' % (hrs, min%60, td.seconds%60)

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
    
    stats_format = {
        'secElapsed':       format_elapsed_time,
        'samplesSec':       lambda x: 'Samples/Sec: %0.2f'%x,
        'samplesTotSec':    lambda x: 'Total Samples/Sec: %0.2f'%x,
        'samplesPx':        lambda x: 'Samples/Px: %0.2f'%x,
        'efficiency':       lambda x: 'Efficiency: %0.2f %%'%x,
        'filmEV':           lambda x: 'EV: %0.2f'%x,
    }
    
    stats_string = ''
    
    def stop(self):
        self.active = False
        if self.timer is not None:
            self.timer.cancel()
            
    def compute_stats(self):
        for k in self.stats_dict.keys():
            self.stats_dict[k] = self.lux_context.statistics(k)
        
        self.stats_string = ' | '.join(['%s'%self.stats_format[k](v) for k,v in self.stats_dict.items()])
        
    def get_stats_dict(self):
        self.compute_stats()
        return self.stats_dict
        
    def get_stats_string(self):
        self.compute_stats()
        return self.stats_string