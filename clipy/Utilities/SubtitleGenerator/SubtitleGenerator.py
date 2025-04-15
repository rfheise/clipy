import os
import subprocess
from ..Logging import Logger 
from pydub import AudioSegment
from .Timestamps import Timestamp, TimeStamps
from tqdm import tqdm
import json 
import random

"""
This module initializes the SubtitleGenerator class and Subtitle class. 
The SubtitleGenerator is an abstract class that is made to be implemented by various Subtitle Generation algorithms.

For example the default for most of the project is the OpenAIWhisper generator but there are others that can be implemented. 

Usage:

    sg = SubtitleGenerator("./movie.mp4")
    sg.generate_subtitles()
    sg.to_srt("movie.srt")

"""

class FileNotFormattedProperly(Exception):
    def __init__(self, f_path, f_type):
        self.message = f"{f_path} not formatted as proper {f_type}"
        super().__init__(self.message)

class SubtitleGenerator():

    def __init__(self, fname, subtitle_interval=20):
        
        #list of subtitles
        self.subtitles = []

        #input video/audio filename
        self.fname = fname 

        #input file type
        self.type = os.path.splitext(fname)[1]
        
        #denotes size of chunk in seconds to split the input audio into 
        #i.e. use chunks of size 20 seconds
        self.subtitle_interval = subtitle_interval

        #private variables implemented in corresponding property function
        self.__audio_file = None
        self.__temp_buffer = None
    
    @property
    def temp_buffer(self):
        
        #generates a temporary file to use as a buffer
        if self.__temp_buffer is None:
            self.__temp_buffer = f".tmp_audio_clip-{random.randint(0,10**9)}.mp3"

            #uses /dev/shm on linux to keep buffer in memory
            if os.path.exists("/dev/shm"):
                self.__temp_buffer = f"/dev/shm/{self.__temp_buffer}"

        return self.__temp_buffer
    
    def generate_subtitles(self):        
        """
        This method generates the subtitles for the input file by splitting it into various chunks
        It uses the overloaded method of the subtitle engine to process these chunks
        It then merges the processed chunks into a single subtitle list 
        """

        #loads audio file
        audio = AudioSegment.from_file(self.audio_file)
        self.duration = audio.duration_seconds
        
        #generates timestamps for each chunk in the input clip
        timestamps = [[i, i+self.subtitle_interval] for i in range(0, int(self.duration), self.subtitle_interval)]
        timestamps[-1][1] = self.duration
        timestamps = TimeStamps.from_nums(timestamps) 
        
        #processes subtitles for each segment
        Logger.log(f"Generating subtitles for {self.fname}")
        for t in tqdm(timestamps, total=len(timestamps)):
            #calls overloaded method
            out = self.generate_subtitle_segment(t)
            self.add_subtitles(out)
        self.subtitles.sort(key=lambda x: x.timestamp.start)
        Logger.log(f"Finished Generating Subtitles for {self.fname}")
        self.merge()
        self.cleanup()

    def generate_subtitle_segment(self, timestamp):
        
        """

        This method is to be implemented by the inheriting subtitle engine
        By overloading this method you can create another subtitle engine
        
        It takes in a timestamp and generates the video subtitles between the start and ending positions in the timestamp

        """

    def save(self, out_file):
        #saves subtitles in json format
        json_format = []
        for sub in self.subtitles:
            json_format.append({"text": sub.text, "start": sub.timestamp.start, "end":sub.timestamp.end})
        with open(out_file, "w") as f:
            json.dump(json_format, f)

    def load(self, in_file):

        #supports initializing subtitles from json and srt files
        if os.path.splitext(in_file)[1] == ".json":
            self.load_from_json(in_file)
        elif os.path.splitext(in_file)[1] == ".srt":
            self.load_from_srt(in_file)
        else:
            Logger.log_error("File type not supported")

    @classmethod 
    def init_from_file(cls, f):

        #loads subtitles from saved subtitles
        sub = cls(f)
        sub.load(f)
        return sub
    
    def load_from_json(self, in_file):
        with open(in_file, "r") as f:
            json_format = json.load(f)
        for sub in json_format:
            self.add_subtitle(Subtitle(sub["text"], Timestamp(sub["start"], sub["end"])))
    
    def load_from_srt(self, in_file):
        
        #initializes subtitle generator with srt file 

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
            #if input is video file split audio and video
            if self.is_video():
                self.__audio_file = self.generate_audio_from_video()
            #otherwise just load the audio directly from the input file
            else:
                self.__audio_file = self.fname
        return self.__audio_file
    
    def get_subtitles(self, timestamp = None):
        #gets subtitles that are within the timestamp

        #if no timestamp specified return all subtitles
        if timestamp is None:
            return self.subtitles
        
        #otherwise return all subtitles within timestamp
        ret= []
        for subtitle in self.subtitles:
            if subtitle.timestamp.start > timestamp.start:
                ret.append(subtitle)
            if subtitle.timestamp.start > timestamp.end:
                break
        return ret 
    
    def add_subtitle(self, subtitle):
        #add subtitle to subtitle list
        self.subtitles.append(subtitle)
    
    def add_subtitles(self, subtitles):
        #merge subtitle lists
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

        #converts time in seconds to hour:minute:seconds,milliseconds format for srt
    
        start_hours, start_minutes, start_seconds, start_miliseconds = int(start_time // 3600), int((start_time % 3600) // 60), int(start_time % 60), format(int((start_time % 1) * 1000), "03d")
        return f"{start_hours:02}:{start_minutes:02}:{start_seconds:02},{start_miliseconds}"
    
    def to_srt(self, srt_path, sub_duration=1):
        
        #writes the generated subtitles to srt_path in an srt format 

        lines = []
        for i in range(len(self.subtitles)):
            segment = self.subtitles[i]
            start_time = segment.timestamp.start
            end_time = segment.timestamp.end

            #ensures subtitle duration is at least sub_duration unless another 
            #subtitle comes within that timeframe
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
        #uses ffmpeg to generate audio file from video 

        Logger.log("Splitting audio from video")
        if os.path.exists("/dev/shm"):
            tmp_file = "/dev/shm/.tmp_audio_file-"+str(random.randint(0,10**9))
        else:
            tmp_file = ".tmp_audio_file-"+str(random.randint(0,10**9))
        audio_file = tmp_file + ".mp3"
        result = subprocess.run(['ffmpeg', '-i', self.fname, '-b:a', '128k', tmp_file + ".mp3"],capture_output=True,text=True)
        # result = subprocess.run(['lame', '-b', "128",tmp_file + ".wav",audio_file],capture_output=True,text=True)
        return audio_file

    def cleanup(self):
        #removes temp files 

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
        #converts subtitles to format that is sent to llm 
    
        txt = "\n".join([f"{round(s.timestamp.start)}:{s.text.strip()}" for s in self.subtitles])
        if  fname:
            with open(fname, "w") as f:
                f.write(txt)
        return txt
    

"""
Subtitle class

Stores basic information about a subtitle (text, (start, end) timestamp)
"""
class Subtitle():
    
    def __init__(self, text, timestamp):
        self.text = text
        self.timestamp = timestamp
    
    def __str__(self):
        return f"{self.timestamp}: {self.text}"
    
    #determines subtitle similarity 
    #used to determine whether or not to merge two subtitle objects
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