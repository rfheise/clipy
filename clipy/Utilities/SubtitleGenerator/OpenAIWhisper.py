from .SubtitleGenerator import SubtitleGenerator, Subtitle
from .Timestamps import Timestamp
import subprocess
import torch
from pydub import AudioSegment
import os
import warnings
import numpy as np
import io 
import torchaudio
import whisper
from ..Logging.Logger import Logger 
from ..Config.Config import Config

warnings.filterwarnings("ignore", category=UserWarning)

class OpenAIWhisper(SubtitleGenerator):
    def __init__(self, fname, model_name="turbo", no_speech_prob_threshold=0.5,
                 subtitle_interval=20,sample_rate=16000):
        super().__init__(fname,subtitle_interval)
        self.__model = None
        self.model_name = model_name
        self.no_speech_prob_threshold = no_speech_prob_threshold
        self.audio_segment = None
        self.device = Config.device
        self.sample_rate = sample_rate

    @property
    def model(self):
        # if torch.mps.is_available():
        #     self.device = torch.device("mps")
        if self.__model is None:
            self.__model = whisper.load_model(self.model_name, self.device)
        return self.__model
        
    def generate_subtitle_segment(self, timestamp, overlap=5):
        if self.audio_segment is None:
            self.audio_segment = whisper.load_audio(self.audio_file,sr=self.sample_rate)
            
        start = timestamp.start - overlap 
        end = timestamp.end + overlap
        if start < 0:
            start = 0
        if end > self.duration:
            end = self.duration

        clip = self.audio_segment[start *self.sample_rate: int(end*self.sample_rate)]
        transcript = self.model.transcribe(clip)
        return self.process_segments(start, transcript, timestamp)
    
    def process_segments(self, start,transcript,  timestamp):
        result = [item for item in transcript["segments"] if item["no_speech_prob"] < self.no_speech_prob_threshold]
        ret = []
        #loop over result only keep non duplicate speech
        prev_item = None
        for item in result:
            #remove if exists in overlap window 
            if item["start"] + start > timestamp.end or item["end"] + start < timestamp.start:
                continue
            if not prev_item or prev_item["text"] != item["text"]:  
                ret.append(Subtitle(item["text"], Timestamp(item["start"]+ start, item["end"] + start)))
            prev_item = item
        return ret
        

if __name__ == "__main__":
    sg = OpenAIWhisper("./videos/films/red_river.mp4",model_name="turbo")
    sg.generate_subtitles()
    # sg.to_srt(".cache/Episode S1E9.turbo.en.srt")
    sg.format_for_llm(".cache/red_river.llm.sub")
    # print(str(sg))