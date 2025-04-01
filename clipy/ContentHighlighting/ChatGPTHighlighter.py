from .SubtitleHighlighter import SubtitleHighlighter
from openai import OpenAI
import json
from ..Utilities import Logger, GhostCache, Cache
from ..Utilities import Timestamp, TimeStamps
from scenedetect import detect, ContentDetector

class ChatGPTHighlighter(SubtitleHighlighter):

    default_sys_prompt = """
    The following represents transcripts from a video represented as a timestamp: text pair. 
    Please select the most interesting 5 - 10 moments and provide a timestamp and score for each and output in a json format. 
    """

    def __init__(self, video_file,approx_length=45, model="gpt-4o-mini", sys_prompt=None, cache=GhostCache):
        super().__init__(video_file, approx_length, cache=cache)
        self.model = model 
        self.sys_prompt = sys_prompt
        if self.sys_prompt is None:
            self.sys_prompt = ChatGPTHighlighter.default_sys_prompt
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
                                "timestamp": {
                                    "type": "integer",
                                    "description": "The timestamp of the moment"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "The description of the moment"
                                }
                            },
                            "required": ["score", "timestamp", "description"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["moments"],
                "additionalProperties": False
            }
        }
        }


    def highlight_subtitles(self):
        output_json = json.loads(self.call_api())
        subtitle_list = self.get_list_from_json(output_json["moments"])
        return subtitle_list
    
    def get_list_from_json(self, moments):

        timestamps = []
        for moment in moments:
            sub_id = int(moment["timestamp"])
            if sub_id >= len(self.sub_gen.subtitles):
                continue
            sub_timestamp = self.sub_gen.subtitles[sub_id].timestamp
            start = sub_timestamp.start - self.approx_length/2
            end = sub_timestamp.start + self.approx_length/2
            for subtitle in self.sub_gen.subtitles:
                # if start/end in middle of dialogue wait until the end
                if start > subtitle.timestamp.start and start < subtitle.timestamp.end:
                    start = subtitle.timestamp.start 
                if end > subtitle.timestamp.start and end < subtitle.timestamp.end:
                    end = subtitle.timestamp.end
            timestamps.append((start,end))
        
        return TimeStamps.from_nums(timestamps)


    def call_api(self):

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

        return response.output_text

    def get_model_input(self):
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
                "text": self.sub_gen.format_for_llm(".cache/.tmp_llm_out.sub")
                }
            ]
            },

        ]
        return model_input
    
if __name__ == "__main__":
    video_file = "./videos/Episode S2E8.mp4"
    cache_file = "./.cache/tmp.sav"
    cache = Cache(dev=True)
    cache.load(cache_file)
    cache.clear('highlighter')
    highlighter = ChatGPTHighlighter(video_file,model="gpt-4o-mini", cache=cache)
    timestamps = highlighter.highlight_intervals()
    cache.save(cache_file)
    
    

    