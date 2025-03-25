from .SubtitleGenerator import SubtitleGenerator, Subtitle
from .Timestamps import Timestamp
import subprocess
import torch
import whisper 
from pydub import AudioSegment
import os
import warnings
import numpy as np
import io 
import torchaudio

warnings.filterwarnings("ignore", category=UserWarning)

class OpenAIWhisper(SubtitleGenerator):
    def __init__(self, fname, model_name="tiny.en", no_speech_prob_threshold=0.5,subtitle_interval=30):
        super().__init__(fname,subtitle_interval)
        self.__model = None
        self.model_name = model_name
        self.no_speech_prob_threshold = no_speech_prob_threshold
        self.sound = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    @property
    def model(self):
        # if torch.mps.is_available():
        #     self.device = torch.device("mps")
        if self.__model is None:
            self.__model = whisper.load_model(self.model_name).to(self.device)
        return self.__model

    # @staticmethod
    # def segment_to_array(segment):
    #     """
    #     ~Vibe Coded Function~
    #     Convert a pydub AudioSegment to a normalized NumPy array.
    #     Assumes sample width of 2 bytes (16-bit audio).
    #     """
    #     # Get raw audio data as a NumPy array of type int16
    #     samples = np.array(segment.get_array_of_samples())
    #     # If stereo, reshape and average the channels to get mono
    #     if segment.channels > 1:
    #         samples = samples.reshape((-1, segment.channels))
    #         samples = samples.mean(axis=1)
    #     # Convert to float32 and normalize between -1 and 1
    #     samples = samples.astype(np.float32) / (1 << (8 * segment.sample_width - 1))
    #     return samples
    def segment_to_tensor(self, segment):
        """
        Convert a pydub AudioSegment to a torch tensor using torchaudio.
        This avoids the overhead of manual conversion in Python.
        """
        # Create a BytesIO object from the segment's raw data.
        buffer = io.BytesIO(segment.raw_data)
        # torchaudio.load will read from the buffer. 
        # Make sure to specify the format if needed (e.g., format="mp3")
        waveform, sample_rate = torchaudio.load(buffer, format="mp3")
        waveform = waveform.to(self.device)
        # waveform is of shape [channels, num_samples]
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0)
        return waveform

    def get_clip_tensor(self, start, end):
        audio = self.sound
        start = int(start * audio["sample_rate"])
        end = min(int(end * audio["sample_rate"]), audio["waveform"].numel())
        return audio["waveform"][start:end]
    
    def generate_subtitle_segment(self, timestamp, overlap=5):
        if self.sound is None:
            waveform, sample_rate = torchaudio.load(self.audio_file, normalize=True)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0)
            self.sound = {
                "waveform": waveform,
                "sample_rate": sample_rate
            }
            
        start = timestamp.start - overlap 
        end = timestamp.end + overlap
        if start < 0:
            start = 0
        if end > self.duration:
            end = self.duration
        clip = self.get_clip_tensor(start, end)
        # clip.export(self.temp_buffer, format="mp3")
        transcript = self.model.transcribe(clip)
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
    sg = OpenAIWhisper("./linus.mp3")
    sg.generate_subtitles()
    sg.to_srt("tmp.srt")
    # print(str(sg))