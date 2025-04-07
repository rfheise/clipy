import os 

class VideoProcessor:
    def __init__(self, videos):
        self.videos = videos
        self.pizzazz_list = []

    def process_video(self):
        # Placeholder for video processing logic
        print(f"Processing video: {self.video_path}")
        # Simulate processing and set processed video path
        self.processed_video_path = f"processed_{self.video_path}"
        print(f"Processed video saved at: {self.processed_video_path}")

    def add_pizzazz(self, pizzazz):
        self.pizzazz_list.add(pizzazz)
    
    def save_to_file(fname, frames, audio):
        #TODO save frames and audio to fname 
        pass

    def render(self):
        os.makedirs("clips", exist_ok=True)
        for video in self.videos:
            frames,audio = video.render()
            for pizzazz in self.pizzazz_list:
                frames, audio = pizzazz.render(frames, audio, video.get_timestamp())
            self.save_to_file(frames, audio)