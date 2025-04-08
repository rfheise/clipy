import os
import subprocess
from ..Logging import Logger 
from pydub import AudioSegment
from .Timestamps import Timestamp, TimeStamps
from tqdm import tqdm
import json 
import random

class FileNotFormattedProperly(Exception):
    def __init__(self, f_path, f_type):
        self.message = f"{f_path} not formatted as proper {f_type}"
        super().__init__(self.message)

class SubtitleGenerator():

    def __init__(self, fname, subtitle_interval=20):
        self.subtitles = []
        self.fname = fname 
        self.type = os.path.splitext(fname)[1]
        self.subtitle_interval = subtitle_interval
        self.__audio_file = None
        self.__temp_buffer = None
    
    @property
    def temp_buffer(self):
        if self.__temp_buffer is None:
            self.__temp_buffer = f".tmp_audio_clip-{random.randint(0,10**9)}.mp3"
            if os.path.exists("/dev/shm"):
                self.__temp_buffer = f"/dev/shm/{self.__temp_buffer}"
        return self.__temp_buffer
    
    def generate_subtitles(self):        

        audio = AudioSegment.from_file(self.audio_file)
        self.duration = audio.duration_seconds
        timestamps = [[i, i+self.subtitle_interval] for i in range(0, int(self.duration), self.subtitle_interval)]
        timestamps[-1][1] = self.duration
        timestamps = TimeStamps.from_nums(timestamps) 
        #generate segments 
        Logger.log(f"Generating subtitles for {self.fname}")
        for t in tqdm(timestamps, total=len(timestamps)):
            out = self.generate_subtitle_segment(t)
            self.add_subtitles(out)
        self.subtitles.sort(key=lambda x: x.timestamp.start)
        Logger.log(f"Finished Generating Subtitles for {self.fname}")
        self.merge()
        self.cleanup()

    def generate_subtitle_segment(self, timestamp):
        #TODO generate subtitle for the given timestamp
        pass

    def save(self, out_file):
        json_format = []
        for sub in self.subtitles:
            json_format.append({"text": sub.text, "start": sub.timestamp.start, "end":sub.timestamp.end})
        with open(out_file, "w") as f:
            json.dump(json_format, f)

    def load(self, in_file):
        if os.path.splitext(in_file)[1] == ".json":
            self.load_from_json(in_file)
        elif os.path.splitext(in_file)[1] == ".srt":
            self.load_from_srt(in_file)
        else:
            Logger.log_error("File type not supported")

    @classmethod 
    def init_from_file(cls, f):
        sub = cls(f)
        sub.load(f)
        return sub
    
    def load_from_json(self, in_file):
        with open(in_file, "r") as f:
            json_format = json.load(f)
        for sub in json_format:
            self.add_subtitle(Subtitle(sub["text"], Timestamp(sub["start"], sub["end"])))
    
    def load_from_srt(self, in_file):

        with open(in_file, "r") as srt:
            lines = iter(srt)
            while True:
                line = next(lines, None)
                if line == None:
                    return
                line = line.strip("\n")
                #read until 
                while line.isdigit() is False:
                    line = next(lines, None)
                    if line == None:
                        return
                    line = line.strip()
                #read srt segment 
                #process timestamps 
                timestamp = next(lines, None)
                if timestamp is None:
                    raise FileNotFormattedProperly(in_file, "srt")
                try:
                    timestamp = Timestamp.from_srt(timestamp.strip())
                except:
                    raise FileNotFormattedProperly(in_file, "srt")
                text = next(lines,None)
                if text is None:
                    raise FileNotFormattedProperly(in_file, "srt")
                text = text.strip()
                self.subtitles.append(Subtitle(text, timestamp))
                
    @property
    def audio_file(self):
        #lazy init audio file 
        if self.__audio_file is None:
            if self.is_video():
                self.__audio_file = self.generate_audio_from_video()
            else:
                self.__audio_file = self.fname
        return self.__audio_file
    
    def get_subtitles(self, timestamp = None):
        if timestamp is None:
            return self.subtitles
        ret= []
        for subtitle in self.subtitles:
            if subtitle.timestamp.start > timestamp.start:
                ret.append(subtitle)
            if subtitle.timestamp.start > timestamp.end:
                break
        return ret 
    
    def add_subtitle(self, subtitle):
        self.subtitles.append(subtitle)
    
    def add_subtitles(self, subtitles):
        for sub in subtitles:
            self.add_subtitle(sub) 
    
    def merge(self):
        #merges subtitles over competing timestamps
        # right now just uses heuristic that a longer window is better if more than 30% of the words overlap
        #should probably update later though
        i = 0
        while i < len(self.subtitles) - 1:
            if self.subtitles[i].timestamp.end > self.subtitles[i+1].timestamp.start:
                #if overlap is similar 30% remove the shorter one
                # or if overlap is miniscule keep the longer one
                overlap_time = abs(self.subtitles[i+1].timestamp.start - self.subtitles[i].timestamp.start) + abs(self.subtitles[i+1].timestamp.end - self.subtitles[i].timestamp.end)
                overlap_sentence = self.subtitles[i].compute_overlap(self.subtitles[i+1])
                if  overlap_time < 1 or overlap_sentence >= .5:
                    #keep the longer one
                    
                    if self.subtitles[i].duration > self.subtitles[i+1].duration:
                       del self.subtitles[i+1] 
                    else:
                        del self.subtitles[i]
                    continue 
                else:
                    self.subtitles[i].timestamp.end = self.subtitles[i+1].timestamp.start
            i += 1


    @staticmethod
    def timestamp_to_srt_time(start_time):
        start_hours, start_minutes, start_seconds, start_miliseconds = int(start_time // 3600), int((start_time % 3600) // 60), int(start_time % 60), format(int((start_time % 1) * 1000), "03d")
        return f"{start_hours:02}:{start_minutes:02}:{start_seconds:02},{start_miliseconds}"
    
    def to_srt(self, srt_path, sub_duration=5):
        """Write the transcript to an SRT file based on the video's duration."""
        lines = []
        # Use tqdm to display progress for segment processing
        for i in range(len(self.subtitles)):
            segment = self.subtitles[i]
            start_time = segment.timestamp.start
            end_time = segment.timestamp.end

            if i != len(self.subtitles) - 1:
                cand = min(end_time + sub_duration, self.subtitles[i + 1].timestamp.start)
                end_time = cand

            segment_text = "".join(segment.text)

            lines.append(f"{i + 1}\n{self.timestamp_to_srt_time(start_time)} --> {self.timestamp_to_srt_time(end_time)}\n{segment_text}\n\n\n")

        with open(srt_path, "w") as srt_file:
            srt_file.writelines(lines)


    def is_video(self):
        return self.type in [".mp4", ".avi", ".m4v",".webm",".mov"]

    def generate_audio_from_video(self):
        Logger.log("Splitting audio from video")
        if os.path.exists("/dev/shm"):
            tmp_file = "/dev/shm/.tmp_audio_file-"+str(random.randint(0,10**9))
        else:
            tmp_file = ".tmp_audio_file-"+str(random.randint(0,10**9))
        audio_file = tmp_file + ".mp3"
        result = subprocess.run(['ffmpeg', '-i', self.fname, tmp_file + ".wav"],capture_output=True,text=True)
        result = subprocess.run(['lame', '-b', "128",tmp_file + ".wav",audio_file],capture_output=True,text=True)
        os.remove(tmp_file + ".wav")
        return audio_file

    def cleanup(self):
        if self.__audio_file is not None and self.__audio_file != self.fname and os.path.exists(self.__audio_file):
            os.remove(self.__audio_file)
        if self.__temp_buffer is not None and os.path.exists(self.__temp_buffer):
            os.remove(self.__temp_buffer)
    
    def __str__(self):
        s = "[\n"
        for sub in self.subtitles:
            s += "\t"+ str(sub) + "\n" 
        return s + "]"
    
    def format_for_llm(self, fname=None):
        count = iter(range(len(self.subtitles)))
        txt = "\n".join([f"{next(count, 0)}: {s.text}" for s in self.subtitles])
        if  fname:
            with open(fname, "w") as f:
                f.write(txt)
        return txt
    

    
class Subtitle():
    
    def __init__(self, text, timestamp):
        self.text = text
        self.timestamp = timestamp
    
    def __str__(self):
        return f"{self.timestamp}: {self.text}"
    
    def compute_overlap(self, other):
        #compute the overlap between two subtitles
        # return the ratio of words in common 
        s1 = set(self.text.split(" "))
        s2 = set(other.text.split(" "))
        return len(s1.intersection(s2)) / len(s1.union(s2))
    
    @property
    def duration(self):
        return self.timestamp.end - self.timestamp.start

if __name__ == "__main__":
    # subs = SubtitleGenerator.init_from_file("./subtitles/onlyFilms/turbo/red_river.srt")
    subs = SubtitleGenerator
    print(subs.format_for_llm("out.llm_sub"))