import pickle 
import os 
from ..Logging.Logger import Logger
from ..Profiler.Profiler import Profiler

class Cache():

    cache_levels = ["basic", "dev", "debug"]

    def __init__(self, level="basic", *args, **kwargs):

        if level not in Cache.cache_levels:
            Logger.log_error(f"Cache Level {level} not in {Cache.cache_levels}")
            exit(1)

        for lvl in Cache.cache_levels:
            setattr(self, lvl, False)

        idx = Cache.cache_levels.index(level)
        for i in range(idx + 1):
            setattr(self, Cache.cache_levels[i], True)
        
        self.init_cache()
        self.save_file = None
        
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

    def load(self, fname=None):
        Profiler.start("caching")
        if self.save_file is not None:
            fname = self.save_file
        Logger.debug("Loading Cache")
        #should work for now but need to improve later 
        if fname is None or not os.path.exists(fname):
            Logger.log_warning("Cache File Does Not Exist Skipping Initialization")
            return 
        
        with open(fname, 'rb') as f:
            self.cache = pickle.load(f)
        
        if self.cache is None:
            Logger.log_warning("Cache set to None after load")
        Profiler.stop("caching")
        
    def save(self, fname=None):
        if self.save_file is None:
            Logger.debug("Cache file not set skipping save")
            return
        Profiler.start("caching")
        fname = self.save_file
        if fname is None:
            Logger.log_warning("Cache File Not Specified")
            return
        Logger.debug("Saving Cache")
        with open(fname, 'wb') as f:
            pickle.dump(self.cache, f)
        Profiler.stop("caching")
    
    def clear(self, key = None):
        
        if key is None:
            self.init_cache()
        else:
            self.set_item(key, None)

    def set_save_file(self, fname):
        self.save_file = fname

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