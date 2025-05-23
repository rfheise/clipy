from .SubtitleHighlighter import SubtitleHighlighter
from openai import OpenAI
import json
from ..Utilities import Logger, GhostCache, Cache
from ..Utilities import Timestamp, TimeStamps, OpenAIWhisper, Profiler
from scenedetect import detect, ContentDetector
import math

"""This module highlights the most interesting moments in a video using ChatGPT.
It converts the subtitles into a format that ChatGPT can understand and then uses ChatGPT to highlight the most interesting moments in the video.
It takes the direct output from chatgpt and converts it into a list of timestamps.

TLDR;
Input Video -> Subtitle Generator -> ChatGPT -> Formatted Clip Timestamps
"""

class ChatGPTHighlighter(SubtitleHighlighter):

    def __init__(self, video_file,approx_length=45, model="gpt-4o-mini", sys_prompt=None, cache=GhostCache, sub_model="tiny", num_clips=None):

        sub_gen = OpenAIWhisper(video_file, model_name=sub_model)
        self.num_clips = num_clips
        super().__init__(video_file, approx_length, cache=cache,sub_gen=sub_gen)
        self.model = model 
        self.sys_prompt = sys_prompt
        self.client = OpenAI()
        self.output_format = {
        "format": {
            "type": "json_schema",
            "name": "top_moments",
            "schema": {
                "type": "object",
                "properties": {
                    "moments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "score": {
                                    "type": "integer",
                                    "description": "Virality score of moment from 0 - 100"
                                },
                                "start": {
                                    "type": "integer",
                                    "description": "The starting timestamp of the moment"
                                },
                                "end": {
                                    "type": "integer",
                                    "description": "The end timestamp of the moment"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "A short description of the moment"
                                }
                            },
                            "required": ["score", "start", "end", "title"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["moments"],
                "additionalProperties": False
            }
        }
        }

    @property
    def default_sys_prompt(self):
        return f"""
    Analyze the provided video transcripts, formatted as start timestamp in seconds:text. 
    Identify {self.num_clips} segments with the MOST potential for engaging, viral-ready video clips, each approximately 45 seconds.
    Each clip should be AT MOST 60 seconds long and AT LEAST 30 seconds long.
    The segments should be interesting, funny, or engaging, and suitable for sharing on social media platforms like TikTok, Instagram, or YouTube Shorts.
    The opening moment of each segment should hook the audience, offering an intriguing glimpse into the content while leaving certain elements unresolved, thereby piquing curiosity and encouraging viewers to continue watching.
    As the clip progresses please try to answer the the questions posed during the hook.
    Make sure to carefully analyze the ENTIRE VIDEO before selecting the most interesting moments. 
    For each selected segment, indicate start and end timestamps, a viral hook score, and a descriptive title. Present findings in JSON format.
    """

    def highlight_subtitles(self):
        
        # in order for these default values to be initialized the subtitles
        # have to be generated first
        # that is why they are initialized here
        if self.num_clips is None:
            dur = self.sub_gen.subtitles[-1].timestamp.end
            #generate a clip for every 5 minutes of video
            self.num_clips = int(math.ceil(dur / (5 * 60)))

        if self.sys_prompt is None:
            self.sys_prompt = self.default_sys_prompt

        #chatgpt outputs json so it loads it into a python dict
        output_json = json.loads(self.call_api())

        #processes output json
        subtitle_list = self.get_list_from_json(output_json["moments"])

        return subtitle_list
    
    def get_list_from_json(self, moments):
        """
        Takes the json output from chatgpt and converts it into a list of timestamps

        Args:
            moments (see self.output_format): timestamps chatgpt thinks are good clips

        Returns:
            TimeStamps: processed timestamps of video clips
        """
        timestamps = []
        titles = []

        # sorts moments by "virality" score
        moments.sort(key=lambda x: x["score"], reverse=True)

        for moment in moments:
            
            #get start and end timestamps
            # if chatgpt did it right they should correspond to video seconds
            start = int(moment["start"])
            end = int(moment["end"]) + 1

            if end <= start:
                Logger.log_warning("Start time is greater than end time in gpt query. Skipping")
                continue

            for subtitle in self.sub_gen.subtitles:
                # if start/end in middle of dialogue wait until the end
                if start >= subtitle.timestamp.start and start <= subtitle.timestamp.end:
                    start = subtitle.timestamp.start 
                if end >= subtitle.timestamp.start and end <= subtitle.timestamp.end:
                    end = subtitle.timestamp.end
            timestamps.append((start,end))

        return TimeStamps.from_nums(timestamps)


    def call_api(self):

        """Formats the chatgpt api call and sends subtitles to chatgpt

        Returns:
            raw json: raw json output from chatgpt
        """

        Profiler.start("gpt")

        if self.cache.exists("chatgpt"):
            return self.cache.get_item("chatgpt")
        
        Logger.log("Calling ChatGPT To Highlight Interesting Moments")

        response = self.client.responses.create(
            model=self.model,
            input=self.get_model_input(),
            # tools=tools,
            text=self.output_format
            
        )

        Logger.debug(response.output)

        self.cache.set_item("chatgpt", response.output_text, "dev")
        Profiler.stop("gpt")

        return response.output_text

    def get_model_input(self):

        #Formats the input for chatgpt

        model_input = [
            {
            "role": "system",
            "content": [
                {
                "type": "input_text",
                "text": self.sys_prompt
                }
            ]
            },
            {
            "role": "user",
            "content": [
                {
                "type": "input_text",
                "text": self.sub_gen.format_for_llm()
                }
            ]
            },

        ]
        return model_input
    
if __name__ == "__main__":
    
    #used for debugging highlighter
    video_file = "./videos/films/red_river.mp4"
    cache_file = "./.cache/tmp.sav"
    cache = Cache(dev=True)
    cache.load(cache_file)
    cache.clear('highlight')
    cache.clear("scenes")
    highlighter = ChatGPTHighlighter(video_file,model="gpt-4o-mini", cache=cache)
    timestamps = highlighter.highlight_intervals()
    cache.save(cache_file)
    
    

    