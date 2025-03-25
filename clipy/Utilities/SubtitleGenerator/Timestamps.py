

class TimeStamps():

    def __init__(self, timestamps = None):
        if timestamps is None:
            self.timestamps = []
        else:
            self.timestamps = timestamps

    @classmethod
    def from_nums(cls,integer_timestamps):
        ts = cls()
        for t in integer_timestamps:
            ts.add_timestamp(Timestamp(t[0], t[1]))
        return ts
    @classmethod
    def from_times(cls,start,end):
        return cls([Timestamp(start, end)])
    def __len__(self):
        return len(self.timestamps)
    @property
    def start(self):
        return self.timestamps[0].start
    
    def __iter__(self):
        return iter(self.timestamps)
    
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