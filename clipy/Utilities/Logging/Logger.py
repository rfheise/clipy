import sys
import torch 
import os
from ..Config.Config import Config

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

class Logger():
    default_logs = [PrintLog()]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    def init(logs=None):
        
        if logs is None:
            logs = Logger.default_logs
        Logger.logs = logs
        Logger.log(f"Using device {Config.device}")
        if Config.debug_mode:
            Logger.log(f"Debug mode is enabled")

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
        if not Config.debug_mode:
            return
        for log in Logger.logs:
            log.debug(message)



