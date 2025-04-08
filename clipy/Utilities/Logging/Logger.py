import sys
import torch 
import os

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
        print(f"Debug: {message}")
    
    def new_line(self):
        return print()

class Logger():
    logs = [PrintLog()]
    debug_mode = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # debug_mode = False
    def __init__(self):
        pass 

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
        if not Logger.debug_mode:
            return
        for log in Logger.logs:
            log.debug(message)

Logger.log(f"Using device {Logger.device}")

if Logger.debug_mode:
    Logger.log_warning("Debug mode is enabled")
    os.makedirs("debug", exist_ok=True)