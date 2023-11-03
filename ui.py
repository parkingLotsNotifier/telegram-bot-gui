from PIL import Image, ImageDraw
import xml.etree.ElementTree as ET
import json

def generate_parking_lot_image(data):
  
  # Load the background image
  background_image = Image.open("working-bg.png")

  # Load the XML file containing parking slot points
  tree = ET.parse("parking_lot.xml")
  root = tree.getroot()

  # Define the image assets for red and green flashing lights
  red_light = Image.open("red-indicator.png")
  green_light = Image.open("green-indicator.png")

  # Create a dictionary to store the label and light positions
  label_to_light_position = {}

  # Iterate through the XML to get parking slot points and states
  for points in root.findall(".//points"):
      label = points.get("label")
      points_str = points.get("points").split(",")
      x, y = float(points_str[0]), float(points_str[1])
      
      # Calculate the position to overlay the light image
      light_position = (int(x), int(y))
      
      # Store the label and light position in the dictionary
      label_to_light_position[label] = light_position

    # Create a blank image with the same size as the background image
  drawing_image = Image.new("RGBA", background_image.size, (0, 0, 0, 0))
  draw = ImageDraw.Draw(drawing_image)
  
  if "slots" in data:
      slots = data["slots"]
      for slot in slots:
          lot_name = slot["lot_name"]
          status = slot["prediction"]["class"]
          # Select the appropriate flashing light image based on the state
          if status == "occupied":
           light_image = red_light
          else:
           light_image = green_light
          
          # Get the corresponding light position using the label
          light_pos = label_to_light_position[lot_name]
          # Calculate the center of the light image
          light_image_center = (light_image.width // 2, light_image.height // 2)

          # Add the light image center to the light position to place the center of the light image at the desired location
          final_light_pos = (light_pos[0] - light_image_center[0], light_pos[1] - light_image_center[1]+9)

          # Draw the light image onto the blank image at the calculated position
          drawing_image.paste(light_image, final_light_pos, mask=light_image)
          
  # Combine the drawing image with the background image
  final_image = Image.alpha_composite(background_image, drawing_image)

  # Save the final image with flashing light indicators
  final_image.save("background_image.png")          
      
def generate_image(data):
    generate_parking_lot_image(json.loads(data)["fullDocument"])