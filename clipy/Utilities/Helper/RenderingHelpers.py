import cv2 
from PIL import Image, ImageDraw, ImageFont
import numpy as np 
import subprocess
from ..Logging.Logger import Logger
from ..Config.Config import Config
import io

#this whole file was made using ChatGPT
#I didn't actually want to learn how to use PILLOW or cv2
#Honestly doing this myself probably would have taken hours of looking through the docs
#I think it left pretty good descriptions about what each function does 

def draw_box_on_frame(frame, center, box_size=(100, 100), color=(0, 0, 0), thickness=2):
    """
    Draws a rectangle (box) on the frame with the center at 'center'.
    
    Parameters:
      frame (numpy.ndarray): The input image (frame).
      center (tuple): The (x, y) coordinates of the center of the box.
      box_size (tuple): The (width, height) of the box.
      color (tuple): The BGR color for the box.
      thickness (int): The thickness of the box lines.
    
    Returns:
      numpy.ndarray: The modified frame with the drawn box.
    """
    x, y = center
    width, height = box_size
    # Calculate top-left and bottom-right coordinates from the center point.
    top_left = (int(x - width / 2), int(y - height / 2))
    bottom_right = (int(x + width / 2), int(y + height / 2))
    # Make a copy so the original frame is not modified.
    # frame_with_box = frame.copy()
    frame_with_box = frame
    cv2.rectangle(frame_with_box, top_left, bottom_right, color, thickness)
    return frame_with_box

def to_rgb(frame):

    if len(frame.shape) == 2:
        return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    return frame
    

def write_video(frames, output_path, fps):
    """
    Writes a list of frames (numpy arrays) to a video file.
    
    Parameters:
      frames (list): List of frames (numpy arrays).
      output_path (str): Path to the output video file.
      fps (int): Frames per second for the output video.
    """
    # Get dimensions from the first frame.
    height, width = frames[0].render().shape[:2]

    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can choose another codec if desired.
    # video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    # for frame in frames:
    #     video_writer.write(frame)
    # video_writer.release()
    command = [
        'ffmpeg',
        '-y',                # Overwrite output file if it exists.
        '-f', 'rawvideo',    # Input format: raw video.
        '-pix_fmt', 'bgr24', # Pixel format of the raw data.
        '-flush_packets', str(1),
        '-s', f'{width}x{height}', # Frame size.
        '-r', str(fps),      # Frame rate.
        '-i', '-',           # Input comes from standard input.
        '-vf', f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
        '-c:v', 'libx264',# Use libx264rgb for lossless RGB encoding.
        '-crf', str(Config.args.ffmpeg_crf),         # CRF 0 for lossless quality.
        '-preset', Config.args.ffmpeg_preset, # Use a slower preset for optimal compression.
        output_path
    ]
    
    # Open a subprocess with FFmpeg.
    # command = str(" ").join(command)
    # print(str(" ").join(command))
    process = subprocess.Popen(command, stdin=subprocess.PIPE,   
                               stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, 
                                shell=False)
    
    # Write each frame's raw bytes to FFmpeg's stdin.

    for frame in frames:
        f = to_rgb(frame.render())
        process.stdin.write(f.tobytes())
        process.stdin.flush()
    # counter = 0
    # for frame in frames:
    #     if frame.cv2 is not None:
    #         counter += 1

    # Close stdin and wait for FFmpeg to finish.
    process.stdin.close()
    process.wait()

def write_video_raw(frames, output_path, fps):
    """
    Writes a list of frames (numpy arrays) to a video file.
    
    Parameters:
      frames (list): List of frames (numpy arrays).
      output_path (str): Path to the output video file.
      fps (int): Frames per second for the output video.
    """
    # Get dimensions from the first frame.
    height, width = frames[0].shape[:2]
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can choose another codec if desired.
    # video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    # for frame in frames:
    #     video_writer.write(frame)
    # video_writer.release()
    command = [
        'ffmpeg',
        '-y',                # Overwrite output file if it exists.
        '-f', 'rawvideo',    # Input format: raw video.
        '-pix_fmt', 'bgr24', # Pixel format of the raw data.
        '-s', f'{width}x{height}', # Frame size.
        '-r', str(fps),      # Frame rate.
        '-flush_packets', str(1),
        '-i', '-',           # Input comes from standard input.
        '-c:v', 'libx264',# Use libx264rgb for lossless RGB encoding.
        '-crf', str(Config.args.ffmpeg_crf),         # CRF 0 for lossless quality.
        '-preset', Config.args.ffmpeg_preset, # Use a slower preset for optimal compression.
        output_path
    ]
    
    # Open a subprocess with FFmpeg.
    command = str(" ").join(command)
    process = subprocess.Popen(command, stdin=subprocess.PIPE,   
                               stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, shell=True)
    
    # Write each frame's raw bytes to FFmpeg's stdin.

    for frame in frames:
        process.stdin.write(to_rgb(frame).tobytes())
        process.stdin.flush()
    # counter = 0
    # for frame in frames:
    #     if frame.cv2 is not None:
    #         counter += 1

    # Close stdin and wait for FFmpeg to finish.
    process.stdin.close()
    process.wait()

def get_text_size(text, font):
    """
    Returns the width and height of the text using the font's bounding box.
    """
    # getbbox returns (left, top, right, bottom)
    bbox = font.getbbox(text)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

def wrap_text_pil(text, font, max_width, padding=0):
    """
    Wraps text into a list of lines such that each line's width does not exceed max_width.
    """
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        line_width, _ = get_text_size(test_line, font)
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def draw_wrapped_text_save(frame, text, center, font_path, font_size, color,
                      max_width, scale=1, line_spacing=4,  border_thickness=1, border_color=(0, 0, 0)):
    """
    Draws wrapped text with a border (stroke) on the given OpenCV frame using a custom TrueType font.
    The text is wrapped so that no line exceeds max_width, and the text block is centered on the given center.
    The border is drawn around the letters using Pillow's stroke parameters.

    Parameters:
      frame: OpenCV image (BGR).
      text: Text string to draw.
      center: Tuple (x, y) that is the center of the text block.
      font_path: Path to the .ttf file for the custom font.
      font_size: Font size.
      color: Text color in RGB.
      max_width: Maximum width in pixels for wrapping text.
      line_spacing: Additional vertical spacing between lines.
      border_thickness: Thickness of the border (stroke).
      border_color: Color of the border in RGB.

    Returns:
      OpenCV image (BGR) with the outlined text drawn on it.
      
    Note:
      This function assumes helper functions `wrap_text_pil` (to wrap the text) and 
      `get_text_size` (to measure text size) are defined.
    """
    # Convert the OpenCV BGR image to a PIL RGB image.
    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    # Load the custom font.
    font = ImageFont.truetype(font_path, font_size)

    # Wrap the text.
    lines = wrap_text_pil(text, font, max_width)

    # Calculate dimensions of the text block.
    line_widths, line_heights = [], []
    total_height = 0
    for line in lines:
        w, h = get_text_size(line, font)
        line_widths.append(w)
        line_heights.append(h)
        total_height += h
    total_height += line_spacing * (len(lines) - 1)
    block_width = max(line_widths) if line_widths else 0

    # Compute top-left coordinate so that the text block is centered.
    top_left_x = int(center[0] - block_width / 2)
    top_left_y = int(center[1] - total_height / 2)

    # Draw each line with the border using stroke parameters.
    y = top_left_y
    for i, line in enumerate(lines):
        line_width = line_widths[i]
        x = int(center[0] - line_width / 2)
        # Draw the text with stroke (border).
        draw.text(
            (x, y),
            line,
            font=font,
            fill=color,
            stroke_width=max(round(border_thickness * scale),1),
            stroke_fill=border_color
        )
        y += line_heights[i] + line_spacing

    # Convert back to OpenCV BGR format.
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def draw_wrapped_text(frame, text, center, font_path, font_size, color,
                                  max_width, scale=1, line_spacing=4, border_thickness=1, border_color=(0, 0, 0),
                                  shadow_offset=(2, 2), shadow_color=(0, 0, 0)):
    """
    Draws wrapped text with a shadow and a border (stroke) on the given OpenCV frame using a custom TrueType font.
    The text is wrapped so that no line exceeds max_width, and the text block is centered on the given center.
    The shadow is drawn behind the text with the specified offset and color.

    Parameters:
      frame: OpenCV image (BGR).
      text: Text string to draw.
      center: Tuple (x, y) that is the center of the text block.
      font_path: Path to the .ttf file for the custom font.
      font_size: Font size.
      color: Text color in RGB.
      max_width: Maximum width in pixels for wrapping text.
      line_spacing: Additional vertical spacing between lines.
      border_thickness: Thickness of the border (stroke).
      border_color: Color of the border in RGB.
      shadow_offset: Tuple (x_offset, y_offset) for the shadow's position relative to the text.
      shadow_color: Color of the shadow in RGB.

    Returns:
      OpenCV image (BGR) with the shadowed and outlined text drawn on it.
    """
    # Convert the OpenCV BGR image to a PIL RGB image
    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    # Load the custom font
    font = ImageFont.truetype(font_path, font_size)
    shadow_offset = (shadow_offset[0] * scale, shadow_offset[1] * scale)
    # Wrap the text
    lines = wrap_text_pil(text, font, max_width)
    line_spacing *= scale
    # Calculate dimensions of the text block
    line_widths, line_heights = [], []
    total_height = 0
    for line in lines:
        w, h = get_text_size(line, font)
        line_widths.append(w)
        line_heights.append(h)
        total_height += h
    total_height += line_spacing * (len(lines) - 1)
    block_width = max(line_widths) if line_widths else 0

    # Compute top-left coordinate so that the text block is centered
    top_left_x = int(center[0] - block_width / 2)
    top_left_y = int(center[1] - total_height / 2)

    # Draw the shadow by rendering the text with an offset
    y = top_left_y
    for i, line in enumerate(lines):
        line_width = line_widths[i]
        x = int(center[0] - line_width / 2)
        # Draw the shadowed text
        draw.text(
            (x + shadow_offset[0], y + shadow_offset[1]),
            line,
            font=font,
            fill=shadow_color
        )
        y += line_heights[i] + line_spacing

    # Draw the text with border (stroke)
    y = top_left_y
    for i, line in enumerate(lines):
        line_width = line_widths[i]
        x = int(center[0] - line_width / 2)
        # Draw the text with stroke (border)
        draw.text(
            (x, y),
            line,
            font=font,
            fill=color,
            stroke_width=max(round(border_thickness * scale), 1),
            stroke_fill=border_color
        )
        y += line_heights[i] + line_spacing

    # Convert back to OpenCV BGR format
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)