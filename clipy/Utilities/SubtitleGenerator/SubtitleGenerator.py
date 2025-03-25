import os
import subprocess
from ..Logging import Logger 
from pydub import AudioSegment
from .Timestamps import Timestamp, TimeStamps
from tqdm import tqdm
import json 
import random

class SubtitleGenerator():

    def __init__(self, fname, subtitle_interval=30):
        self.subtitles = []
        self.fname = fname 
        self.type = os.path.splitext(fname)[1]
        self.subtitle_interval = subtitle_interval
        self.__audio_file = None
        self.__temp_buffer = None
        self.in_segments = True
    
    @property
    def temp_buffer(self):
        if self.__temp_buffer is None:
            self.__temp_buffer = f".tmp_audio_clip-{random.randint(0,10**9)}.mp3"
            if os.path.exists("/dev/shm"):
                self.__temp_buffer = f"/dev/shm/{self.__temp_buffer}"
        return self.__temp_buffer
    def transcribe_entire_audio_file(self):
        #TODO transcribe the entire audio file
        pass
    def generate_subtitles(self):        
        Logger.log(f"Generating subtitles for {self.fname}")
        audio = AudioSegment.from_file(self.audio_file)
        self.duration = audio.duration_seconds
        timestamps = [[i, i+self.subtitle_interval] for i in range(0, int(self.duration), self.subtitle_interval)]
        timestamps[-1][1] = self.duration
        timestamps = TimeStamps.from_ints(timestamps) 
        #generate segments 
        if self.in_segments:
            for t in tqdm(timestamps, total=len(timestamps)):
                out = self.generate_subtitle_segment(t)
                self.add_subtitles(out)
        else:
            out = self.transcribe_entire_audio_file()
            self.add_subtitles(out)
        self.subtitles.sort(key=lambda x: x.timestamp.start)
        if Logger.debug_mode:
            self.save("tmp.json")
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
        with open(in_file, "r") as f:
            json_format = json.load(f)
        for sub in json_format:
            self.add_subtitle(Subtitle(sub["text"], Timestamp(sub["start"], sub["end"])))
    @property
    def audio_file(self):
        #lazy init audio file 
        if self.__audio_file is None:
            if self.is_video():
                self.__audio_file = self.generate_audio_from_video()
            else:
                self.__audio_file = self.fname
        return self.__audio_file
    
    def get_subtitles(self):
        return self.subtitles
    
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
                       Logger.debug(f"\nDeleting subtitle: {str(self.subtitles[i+1])}")
                       Logger.debug(f"Keeping subtitle: {str(self.subtitles[i])}\n")
                       del self.subtitles[i+1] 
                    else:
                        Logger.debug(f"\nDeleting subtitle: {str(self.subtitles[i])}")
                        Logger.debug(f"Keeping subtitle: {str(self.subtitles[i + 1])}\n")
                        del self.subtitles[i]
                    continue 
                else:
                    # keep both 
                    Logger.debug(f"\nKeeping subtitle: {str(self.subtitles[i])}\n")
                    Logger.debug(f"Keeping subtitle: {str(self.subtitles[i + 1])}\n")
                    self.subtitles[i].timestamp.end = self.subtitles[i+1].timestamp.start
            i += 1


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

            start_hours, start_minutes, start_seconds, start_miliseconds = int(start_time // 3600), int((start_time % 3600) // 60), int(start_time % 60), format(int((start_time % 1) * 1000), "03d")
            end_hours, end_minutes, end_seconds, end_miliseconds = int(end_time // 3600), int((end_time % 3600) // 60), int(end_time % 60), format(int((end_time % 1) * 1000), "03d")

            start_timestamp = f"{start_hours:02}:{start_minutes:02}:{start_seconds:02},{start_miliseconds}"
            end_timestamp = f"{end_hours:02}:{end_minutes:02}:{end_seconds:02},{end_miliseconds}"

            segment_text = "".join(segment.text)

            lines.append(f"{i + 1}\n{start_timestamp} --> {end_timestamp}\n{segment_text}\n\n\n")

        with open(srt_path, "w") as srt_file:
            srt_file.writelines(lines)
        print(f"SRT file saved as {srt_path}")

    def is_video(self):
        return self.type in [".mp4", ".avi", ".m4v",".webm",".mov"]

    def generate_audio_from_video(self):
        Logger.log("Generating audio from video")
        if os.path.exists("/dev/shm"):
            tmp_file = "/dev/shm/.tmp_audio_file-"+str(random.randint(0,10**9))
        else:
            tmp_file = ".tmp_audio_file-"+str(random.randint(0,10**9))
        audio_file = tmp_file + ".mp3"
        result = subprocess.run(['ffmpeg', '-i', self.fname, tmp_file + ".wav"],capture_output=True,text=True)
        result = subprocess.run(['lame', '-b', "128",tmp_file + ".wav",audio_file],capture_output=True,text=True)
        os.remove(tmp_file + ".wav")
        Logger.log("Audio generated from video")
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

