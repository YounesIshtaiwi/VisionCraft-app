import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io

# --------------------------------------------------------------
#  TEXT MASK GENERATOR (robust for deployment)
# --------------------------------------------------------------

def generate_text_mask(size, text):
    """
    Generates a centered boolean mask using PIL's default font (always available)
    and a large canvas for quality scaling.
    """
    # Use a large temporary canvas for quality, relative to desired final size
    canvas = size * 4
    temp_img = Image.new("L", (canvas, canvas), 255) # 255 = White background
    draw = ImageDraw.Draw(temp_img)

    # Use default font, which is guaranteed to be available
    # We rely on the large canvas and final resizing for quality.
    font = ImageFont.load_default()
    
    fill_color = 0 # Text is drawn with fill=0 (Black foreground)

    # --- Robust Text Sizing and Centering ---
    # We rely on a system font (if available) for better measuring, otherwise estimate.
    
    # Placeholder font size for measurement
    font_size_guess = canvas // 2
    
    try:
        # Measure bounding box with a system font (if available)
        # Use a huge size to ensure the text fills the canvas for measurement
        temp_font_measure = ImageFont.truetype("arial.ttf", font_size_guess)
        bbox = draw.textbbox((0, 0), text, font=temp_font_measure)
    except IOError:
        # Fallback for measuring if no system font is found (less accurate but robust)
        # Estimate the text bounding box to be about 60% of the canvas
        bbox = [0, 0, canvas * 0.6, canvas * 0.6] 
        
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Center text manually on the large canvas
    x = (canvas - w) // 2 - bbox[0]
    y = (canvas - h) // 2 - bbox[1]
    
    # Draw text using the universal default font
    draw.text((x, y), text, fill=fill_color, font=font)


    # Downscale to final plate size
    final = temp_img.resize((size, size), Image.LANCZOS)
    
    # Create the mask: Pixels < 128 are the dark text pixels (True)
    mask = np.array(final) < 128

    return mask

# --------------------------------------------------------------
#  ISHIHARA PLATE GENERATOR
# --------------------------------------------------------------

def generate_ishihara_with_text(
    size=500,
    text='69',
    radius_range=(4, 8),
    num_dots=2500,
    spacing_factor=1.15,
    number_colors=None,
    background_colors=None
):
    """
    Generates an Ishihara-style plate as a PNG in a BytesIO buffer.
    """
    number_mask = generate_text_mask(size, text)

    # Circle boundary geometry
    center_x = center_y = size // 2
    max_r = max(radius_range)
    radius_limit = size // 2 - max_r

    # Default palettes
    background_palette = background_colors or [
        [0.2, 0.8, 0.2],
        [0.3, 0.7, 0.3],
        [0.4, 0.9, 0.4],
    ]
    number_palette = number_colors or [
        [1.0, 0.4, 0.4],
        [1.0, 0.6, 0.6],
        [0.9, 0.3, 0.3],
    ]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect("equal")
    ax.axis("off")

    placed = []
    attempts = 0
    max_attempts = num_dots * 10

    # Dot placement loop
    while len(placed) < num_dots and attempts < max_attempts:
        r = np.random.uniform(*radius_range)
        x = np.random.randint(int(r), size - int(r))
        y = np.random.randint(int(r), size - int(r))

        # Respect circular plate boundary
        if (x - center_x)**2 + (y - center_y)**2 > radius_limit**2:
            attempts += 1
            continue

        # Prevent overlapping dots
        if any((x - px)**2 + (y - py)**2 < (spacing_factor * (r + pr))**2
               for px, py, pr in placed):
            attempts += 1
            continue

        placed.append((x, y, r))

        # Select palette based on mask
        # FIX: The color logic is inverted to resolve the "invisible number" issue
        palette = background_palette if number_mask[y, x] else number_palette

        # FIX: Define 'color' by randomly selecting from the chosen palette
        color = palette[np.random.randint(len(palette))]

        # Add circle patch
        ax.add_patch(plt.Circle((x, y), r, color=color))

    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.invert_yaxis()

    # Export to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close()
    buf.seek(0)

    return buf

# --------------------------------------------------------------
#  HEX COLOR → RGB CONVERSION
# --------------------------------------------------------------

def hex_to_rgb_float(hex_color):
    """
    Converts a hex string to an RGB float list [0-1].
    """
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4)]
