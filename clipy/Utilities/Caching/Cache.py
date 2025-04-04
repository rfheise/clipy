import pickle 
import os 
from ..Logging.Logger import Logger

class Cache():

    cache_levels = ["basic", "dev", "debug"]
    def __init__(self, *args, **kwargs):

        for level in Cache.cache_levels:
            setattr(self, level, False)

        for kwarg in kwargs.keys():
            #sets all previous levels to true if current level is true
            if kwargs[kwarg]:
                try:
                    idx = Cache.cache_levels.index(kwarg)
                    for i in range(idx + 1):
                        setattr(self, Cache.cache_levels[i], True)
                except ValueError:
                    pass 
        
        self.init_cache()
        
    def get_item(self, key):

        if self.cache is None:
            return None
        
        return self.cache.get(key)

    def set_item(self, key, val, level='basic'):

        if not getattr(self, level) or self.cache is None:
            return
        self.cache[key] = val
        
    def exists(self, key):
        return self.cache is not None and key in self.cache and self.cache[key] is not None
    
    def init_cache(self):

        if self.basic:
            self.cache = {}
        else:
            self.cache = None

    def load(self, fname):

        #should work for now but need to improve later 
        if not os.path.exists(fname):
            Logger.log_warning("Cache File Does Not Exist Skipping Initialization")
            return 
        
        with open(fname, 'rb') as f:
            self.cache = pickle.load(f)
        
        if self.cache is None:
            Logger.log_warning("Cache set to None after load")
        
    def save(self, fname):

        with open(fname, 'wb') as f:
            pickle.dump(self.cache, f)
    
    def clear(self, key = None):
        
        if key is None:
            self.init_cache()
        else:
            self.set_item(key, None)

class GhostCache(Cache):

    def __init__(self):
        pass 

    def get_item(self, key):
        return None 
    
    def set_item(self, key, val):
        pass 

    def exists(self, key):
        return False
    
    def load(self, fname):
        Logger.log_warning("Loading Ghost Cache")

    def save(self, fname):
        Logger.log_warning("Saving Ghost Cache")
        pass