from .OpenAIWhisper import OpenAIWhisper
import os 
import sys
import time 

"""

Ignore this file. All it does is generate subtitles recursively for a directory full of video files. 
I used this for my jellyfin server and decided to keep it in the repo in case anyone else wants to use it to
generate a bunch of srts for video files.
This file doesn't serve a purpose in the overall project though.

"""

def generate_subtitles(in_dir, out_dir, model="turbo"):

    # get all files and make new directories 
    files = get_files(in_dir, [".mp3",])
    error_files = []
    for f in files:
        out_file = os.path.join(out_dir, os.path.relpath(f, in_dir))
        out_file = os.path.splitext(out_file)[0]
        if not os.path.exists(out_file):
            os.makedirs(os.path.dirname(out_file),exist_ok=True)
        if os.path.exists(out_file + ".srt"):
            print(f"{out_file + '.srt'} already exists")
            continue
        try:
            sg = OpenAIWhisper(f, model_name=model, subtitle_interval=20)
            sg.generate_subtitles()
            sg.to_srt(out_file + ".srt")
            print("Subtitle File saved at: ", out_file + ".srt")
            print()
        except KeyboardInterrupt:
            print("Keyboard interrupt detected. Exiting program.")
            break
        except Exception as e:
            print(e)
            error_files.append(f)
            print("Error processing file: ", f)
            print()
        finally:
            clear_temp_files()
    if len(error_files) != 0:
        with open("error_files.txt", "w") as f:
            for fl in error_files:
                f.write(fl + "\n")
            print("Error files written to error_files.txt")
            print()
    clear_temp_files()

def clear_temp_files():
    for f in os.listdir("./"):
        if f.startswith(".tmp"):
            os.remove(os.path.join("./", f))
    if os.path.exists("/dev/shm"):
        for f in os.listdir("/dev/shm"):
            if f.startswith(".tmp"):
                os.remove(os.path.join("/dev/shm", f))

def get_files(in_dir, types=None):
    files = []
    for f in os.listdir(in_dir):
        f = os.path.join(in_dir, f)
        if os.path.isdir(f):
            files = [*files, *get_files(f, types)]
        elif os.path.basename(f).startswith("._"):
            continue
        else:
            if types:
                if os.path.splitext(f)[1] in types:
                    files.append(f)
            else:
                files.append(f)
    return files

if __name__ == "__main__":
    # models = ["medium.en","tiny.en", "small.en", "base.en",  "turbo", "large"]
    models = ["turbo"]
    with open("./subtitles/movies/model-times.txt", "w") as f:
        start = time.time()
        for model in models:
            generate_subtitles("./mp3/movies", f"./subtitles/movies/{model}", model=model)
        end = time.time()
        f.write(f"{model}:{end - start}\n")