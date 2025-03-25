from .SubtitleGenerator import SubtitleGenerator, Subtitle
from .Timestamps import Timestamp
import subprocess
import torch
import whisper 
from pydub import AudioSegment
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

class OpenAIWhisper(SubtitleGenerator):
    def __init__(self, fname, model_name="tiny.en", no_speech_prob_threshold=0.5):
        super().__init__(fname)
        self.__model = None
        self.model_name = model_name
        self.no_speech_prob_threshold = no_speech_prob_threshold
    
    @property
    def model(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # if torch.mps.is_available():
        #     self.device = torch.device("mps")
        if self.__model is None:
            self.__model = whisper.load_model(self.model_name).to(self.device)
        return self.__model

    def generate_subtitle_segment(self, timestamp, overlap=5):
        audio = AudioSegment.from_mp3(self.audio_file)
        start = timestamp.start - overlap 
        end = timestamp.end + overlap
        if start < 0:
            start = 0
        if end > audio.duration_seconds:
            end = audio.duration_seconds
        clip = audio[start * 1000:end * 1000]
        clip.export(self.temp_buffer, format="mp3")
        transcript = self.model.transcribe(self.temp_buffer)
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
    sg = OpenAIWhisper("./videos/shows/batman_beyond.mp4")
    sg.generate_subtitles()
    sg.to_srt("tmp.srt")
    # print(str(sg))