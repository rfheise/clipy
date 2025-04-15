import sys
import torch 
import os
from ..Config.Config import Config

"""
Logger.py
\
This module is used to create a global logger.
The global logger consists of several Logs that the program will log to.
Currently, the only logger in use is the PrintLog that just prints to stdout,stderr. 
However, you could imagine this being useful for multiple loggers.

In order to create a new log you just need to implement the functions in the Log interface and then 
add the new Log class to the list of global logs. 

"""

#Log Interface
class Log():

    def __init__(self):
        pass 
    
    def new_line(self):
        pass

    def log_error(self, message):
        pass 

    def log(self, message):
        pass 

    def log_warning(self, message):
        pass 

    def debug(self, message):
        pass

#Print Log
#Just logs everything to stdout/stderr depending on the log type
class PrintLog(Log):

    def __init__(self):
        pass 

    def log_error(self, message):
        print(f"ERROR: {message}",file=sys.stderr)

    def log(self, message):
        print(f"INFO: {message}")

    def log_warning(self, message):
        print(f"WARNING: {message}", file=sys.stderr)

    def debug(self, message):
        print(f"DEBUG: {message}")
    
    def new_line(self):
        return print()

#global logger
class Logger():
    #global logs
    default_logs = [PrintLog()]

    #initializes logs
    def init(logs=None):
        
        if logs is None:
            logs = Logger.default_logs
        Logger.logs = logs
        Logger.log(f"Using device {Config.device}")
        if Config.debug_mode:
            Logger.log(f"Debug mode is enabled")

    # the following functions just call the 
    # proper log function in each of the global logs 

    def new_line():
        
        for log in Logger.logs:
            log.new_line()

    def log_error(message):

        for log in Logger.logs:
            log.log_error(message)

    def log(message):

        for log in Logger.logs:
            log.log(message)

    def log_warning(message):

        for log in Logger.logs:
            log.log_warning(message)
    
    def debug(message):

        #only print debug logs in debug mode
        if not Config.debug_mode:
            return
        
        for log in Logger.logs:
            log.debug(message)



