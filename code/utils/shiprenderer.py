import PIL
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import base64
import textwrap
from utils.logger import bot_log

# Configuration
BG_PATH = r"bg.png" # Make sure this path is correct relative to your bot execution
FONT_PATH = r"poppins.bold.ttf" # REPLACE THIS with path to Poppins-Bold.ttf for better looks
OUTPUT_FILE = "ship_result.png"

def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        # Fallback if custom font not found
        return ImageFont.load_default()

def circular_crop(image, size=(130, 130)):
    """Crops an image to a circle and adds a border, similar to CSS border-radius: 50%"""
    # Resize
    image = image.resize(size, Image.Resampling.LANCZOS)
    
    # Create circular mask
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    # Apply mask
    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    
    # Add Border (5px solid white) - CSS: border: 5px solid rgba(255,255,255,0.9);
    border_thickness = 5
    border_color = (255, 255, 255, 230) # 230 is alpha (~0.9)
    
    # Draw border ring on top
    draw_overlay = ImageDraw.Draw(output)
    draw_overlay.ellipse((0, 0, size[0]-1, size[1]-1), outline=border_color, width=border_thickness)
    
    return output

def generateimage(avatar1_b64, avatar2_b64, name1, name2, percent, comment):
    try:
        # 1. Setup Canvas
        # Load background or create black if missing
        try:
            base = Image.open(BG_PATH).convert("RGBA")
            base = base.resize((900, 350))
        except Exception:
            base = Image.new("RGBA", (900, 350), (0, 0, 0, 255))

        # Create a transparent overlay for drawing semi-transparent boxes
        overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # 2. Process Avatars
        # ship.py sends "data:image/png;base64,....." -> we need to strip header
        def process_avatar_data(b64_string):
            if "base64," in b64_string:
                b64_string = b64_string.split("base64,")[1]
            img_data = base64.b64decode(b64_string)
            return Image.open(io.BytesIO(img_data)).convert("RGBA")

        pfp1 = circular_crop(process_avatar_data(avatar1_b64))
        pfp2 = circular_crop(process_avatar_data(avatar2_b64))

        # 3. Positioning Logic (The "Flexbox" simulation)
        # Y positions
        avatar_y = 50
        name_y = 190
        
        # X positions
        center_x = 450
        pfp1_x = 100
        pfp2_x = 900 - 100 - 130 # Right side aligned

        # Paste Avatars
        base.paste(pfp1, (pfp1_x, avatar_y), pfp1)
        base.paste(pfp2, (pfp2_x, avatar_y), pfp2)

        # 4. Draw Names (with dark background pills)
        font_name = load_font(20)
        
        def draw_name_tag(text, center_x, top_y):
            # Calculate text size
            bbox = font_name.getbbox(text)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            padding = 10
            
            # Background pill (Black 60% opacity)
            # x0, y0, x1, y1
            shape = [center_x - w/2 - padding, top_y, center_x + w/2 + padding, top_y + h + padding*2]
            draw.rounded_rectangle(shape, radius=10, fill=(0, 0, 0, 150))
            
            # Text
            # We draw text on the 'overlay' but it needs to be fully opaque
            # Actually, standard PIL draw is easier for text on top of the overlay
            pass 

        # Draw backgrounds for names first
        draw_name_tag(name1, pfp1_x + 65, name_y) # 65 is half of avatar width
        draw_name_tag(name2, pfp2_x + 65, name_y)

        # Composite the semi-transparent backgrounds now
        base = Image.alpha_composite(base, overlay)
        
        # Now draw the solid white text on top
        draw_final = ImageDraw.Draw(base)
        
        # Helper to center text
        def draw_centered_text(text, x, y, font, color=(255,255,255)):
            bbox = font.getbbox(text)
            w = bbox[2] - bbox[0]
            draw_final.text((x - w/2, y), text, font=font, fill=color)

        draw_centered_text(name1, pfp1_x + 65, name_y + 5, font_name)
        draw_centered_text(name2, pfp2_x + 65, name_y + 5, font_name)

        # 5. Draw Center Score
        font_score = load_font(80) # Big text
        draw_centered_text(f"{percent}%", center_x, 70, font_score)

        # Status text below score (e.g. "MATCH")
        font_status = load_font(16)
        # White box with red text
        status_text = "COMPATIBILITY"
        bbox = font_status.getbbox(status_text)
        sw = bbox[2] - bbox[0]
        # Draw white box behind status
        draw_final.rectangle([center_x - sw/2 - 10, 155, center_x + sw/2 + 10, 180], fill="white")
        draw_final.text((center_x - sw/2, 158), status_text, font=font_status, fill="#b30000")

        # 6. Comment Box (Bottom Section)
        # Draw the rounded white container
        # CSS: width: 700px; padding: 15px 30px;
        box_w, box_h = 700, 80
        box_x = (900 - box_w) // 2
        box_y = 240
        
        # New overlay for the white box (95% opacity)
        overlay2 = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw2 = ImageDraw.Draw(overlay2)
        draw2.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=20, fill=(255, 255, 255, 240))
        base = Image.alpha_composite(base, overlay2)
        draw_final = ImageDraw.Draw(base) # Update drawer

        # Text Wrap Logic
        font_comment = load_font(18)
        # Approx chars per line depends on font size. 
        wrapper = textwrap.TextWrapper(width=60)
        if comment:
            wrapped_lines = wrapper.wrap(comment)
        else:
            wrapped_lines = ""
        
        text_start_y = box_y + 20
        line_height = 24
        
        for i, line in enumerate(wrapped_lines[:3]): # Limit to 3 lines
            draw_centered_text(line, center_x, text_start_y + (i * line_height), font_comment, color="#555")

        # 7. Quote Mark
        font_quote = load_font(60)
        draw_final.text((box_x + 10, box_y - 20), "“", font=font_quote, fill="#b30000")

        # 8. Save
        base.save(OUTPUT_FILE)
        return OUTPUT_FILE

    except Exception as e:
        bot_log(f"Error generating ship image: {e}", level="error")
        import traceback
        traceback.print_exc() # Print full error to console for debugging
        return None