

class TimeStamps():

    def __init__(self, timestamps = []):
        self.timestamps = timestamps
    
    def from_ints(integer_timestamps):
        ts = TimeStamps()
        for t in integer_timestamps:
            ts.add_timestamp(Timestamp(t[0], t[1]))
    
    def from_times(start,end):
        return TimeStamps([Timestamp(start, end)])
        
    @property
    def start(self):
        return self.timestamps[0].start
    
    @property
    def end(self):
        return self.timestamps[-1].end

    def add_timestamp(self, timestamp):
        self.timestamps.append(timestamp) 
    
    def __str__(self):
        s = "[ "
        for timestamp in self.timestamps:
            s += str(timestamp) + ","
        s += " ]"
        return s
    
class Timestamp:

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __str__(self):
        return f"{self.start} --> {self.end}"