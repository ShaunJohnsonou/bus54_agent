"""Generate a placeholder logo for Bus 54."""

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os

def generate_bus54_logo(save_path="images/bus54_logo.png"):
    """
    Generate a simple Bus 54 logo and save it to the specified path.
    
    Args:
        save_path: Path where to save the generated logo
    """
    # Create a new image with a white background
    width, height = 800, 300
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a blue rectangle for the background
    draw.rectangle([(50, 50), (width-50, height-50)], fill=(0, 102, 204, 255), outline=(0, 51, 153, 255), width=3)
    
    # Draw a stylized bus shape
    # Bus body
    draw.rectangle([(120, 100), (680, 200)], fill=(255, 255, 255, 255), outline=(0, 51, 153, 255), width=3)
    
    # Bus windows
    window_positions = [(180, 110, 220, 140), (240, 110, 280, 140), (300, 110, 340, 140), 
                        (360, 110, 400, 140), (420, 110, 460, 140), (480, 110, 520, 140),
                        (540, 110, 580, 140), (600, 110, 640, 140)]
    for window in window_positions:
        draw.rectangle(window, fill=(153, 204, 255, 255), outline=(0, 51, 153, 255), width=2)
    
    # Bus wheels
    draw.ellipse([(180, 180), (240, 240)], fill=(51, 51, 51, 255), outline=(0, 0, 0, 255), width=2)
    draw.ellipse([(560, 180), (620, 240)], fill=(51, 51, 51, 255), outline=(0, 0, 0, 255), width=2)
    
    # Bus door
    draw.rectangle([(120, 120), (160, 190)], fill=(153, 204, 255, 255), outline=(0, 51, 153, 255), width=2)
    
    # Add text "BUS 54"
    try:
        # Try to load a font, fall back to default if not available
        font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "arial_bold.ttf")
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 80)
        else:
            font = ImageFont.load_default()
        draw.text((350, 220), "BUS 54", fill=(0, 102, 204, 255), font=font, anchor="mm")
    except Exception:
        # If there's any issue with the font, use a simple rectangle with text
        draw.rectangle([(250, 220), (550, 280)], fill=(0, 102, 204, 255))
        draw.text((400, 250), "BUS 54", fill=(255, 255, 255, 255), anchor="mm")
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # Save the image
    image.save(save_path)
    return save_path

if __name__ == "__main__":
    generate_bus54_logo()
