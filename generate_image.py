import os
from PIL import Image, ImageFont, ImageDraw
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_ADDR = os.getenv("API_ADDR")
API_TOKEN = os.getenv("ACCESS_TOKEN_SECRET")

def create_blank_image(width, height, background_color):
    return Image.new("RGB", (width, height), background_color)

def draw_rectangle(draw, x1, y1, x2, y2, outline_color, width, fill_color):
    draw.rectangle(
        [x1, y1, x2, y2], outline=outline_color, width=width, fill=fill_color
    )

def draw_circle_with_text(
    draw, x, y, text, color, parking_lot_width, parking_lot_height
):
    circle_radius = min(parking_lot_width, parking_lot_height) // 2
    circle_center = (x + circle_radius, y + circle_radius)

    # Draw the circle with the specified color
    draw.ellipse(
        [x + 5, y, x + 2 * (circle_radius - 4), y + 2 * circle_radius - 4],
        outline=(237, 255, 0),  # Circle outline color
        width=2,  # Circle outline width
        fill=color,  # Circle fill color
    )

    # Check if the "Arial.ttf" font file is available, else fall back to a default font
    try:
        font = ImageFont.truetype("Arial.ttf", 10)
    except IOError:
        font = ImageFont.load_default()

    # Get the bounding box of the text
    bbox = font.getbbox(text)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # Calculate text position to center it in the circle
    text_position = (
        circle_center[0] - text_width // 2,
        circle_center[1] - text_height // 2,
    )

    # Draw the text inside the circle
    draw.text(text_position, text, fill=(0, 0, 0))  # Text color: black


def generate_parking_lot_image(data):
    # Define the image dimensions and background color
    width, height = 490, 170
    background_color = (128, 128, 128)  # RGB value for white

    # Create a blank white image
    image = create_blank_image(width, height, background_color)

    # Create a drawing context
    draw = ImageDraw.Draw(image)

    # Define the parameters for the parking lots
    parking_lot_width = 40
    parking_lot_height = 80
    spacing = 10
   
    # Process the parking lot data and draw circles with colors
    if "slots" in data:
        slots = data["slots"]
        for i, slot in enumerate(slots):
            # Calculate the row and column based on the lot_name
            lot_name = slot["lot_name"]
            row = 1 if lot_name[0] == "A" else 2
            col = int(lot_name[1:])
            x1 = (col - 1) * (parking_lot_width + spacing)
            y1 = (row - 1) * (parking_lot_height + spacing)
            x2 = x1 + parking_lot_width
            y2 = y1 + parking_lot_height

            draw_rectangle(draw, x1, y1, x2, y2, (237, 255, 0), 2, "white")
            status = slot["prediction"]["class"]
            color = "red" if status == "occupied" else "green"
            draw_circle_with_text(
                draw,
                x1 + 1,
                y1 + 20,
                lot_name,
                color,
                parking_lot_width,
                parking_lot_height,
            )

    # Save the image with parking lots and circles as a JPG file
    image.save("parking_lots.jpg")

def generate_parking_lot_image(data):
    # Define the image dimensions and background color
    width, height = 490, 170
    background_color = (128, 128, 128)  # RGB value for white

    # Create a blank white image
    image = create_blank_image(width, height, background_color)

    # Create a drawing context
    draw = ImageDraw.Draw(image)

    # Define the parameters for the parking lots
    parking_lot_width = 40
    parking_lot_height = 80
    spacing = 10

    # Process the parking lot data and draw circles with colors
    if "slots" in data:
        slots = data["slots"]
        for i, slot in enumerate(slots):
            # Calculate the row and column based on the lot_name
            lot_name = slot["lot_name"]
            row = 1 if lot_name[0] == "A" else 2
            col = int(lot_name[1:])

            x1 = (col - 1) * (parking_lot_width + spacing)
            y1 = (row - 1) * (parking_lot_height + spacing)
            x2 = x1 + parking_lot_width
            y2 = y1 + parking_lot_height

            draw_rectangle(draw, x1, y1, x2, y2, (237, 255, 0), 2, "white")
            status = slot["prediction"]["class"]
            color = "red" if status == "occupied" else "green"
            draw_circle_with_text(
                draw,
                x1 + 1,
                y1 + 20,
                lot_name,
                color,
                parking_lot_width,
                parking_lot_height,
            )

    # Save the image with parking lots and circles as a JPG file
    image.save("parking_lots.jpg")
    print(data)
    


def generate_image(data):
    print(data)
    generate_parking_lot_image(json.loads(data)["fullDocument"])
    
        
    