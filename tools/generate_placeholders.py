from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image(filename, text, color, size=(800, 1000)):
    """Create a placeholder image with text."""
    # Create a new image with the specified background color
    image = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, default to a built-in one if not available
    try:
        font = ImageFont.truetype("Arial", 36)
    except IOError:
        font = ImageFont.load_default()
    
    # Calculate text position for centering
    try:
        # Modern way - PIL 8.0.0+
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for older PIL versions
        text_width, text_height = draw.textsize(text, font=font)
    
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    
    # Draw the text
    draw.text(position, text, fill="white", font=font)
    
    # Save the image
    filepath = os.path.join("static", "images", filename)
    image.save(filepath)
    print(f"Created placeholder image: {filepath}")

def main():
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.join("static", "images"), exist_ok=True)
    
    # Create placeholder images
    create_placeholder_image("loading-placeholder.png", "Loading...", "#007bff")  # Blue background
    create_placeholder_image("error-placeholder.png", "Error loading image", "#dc3545")  # Red background
    create_placeholder_image("no-content.png", "No content available", "#6c757d")  # Gray background
    
    print("All placeholder images created successfully.")

if __name__ == "__main__":
    main() 