import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io

# --------------------------------------------------------------
#  TEXT MASK GENERATOR (robust for deployment)
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

    # Use default font, which is guaranteed to be available, with a large initial size
    # Note: load_default often ignores the size argument, but we will rely on
    # the canvas size and final resizing for quality.
    font_size = canvas // 2 # A huge size to ensure text fills the canvas
    font = ImageFont.load_default()
    
    # Text is drawn with fill=0 (Black foreground)
    fill_color = 0

    # Draw the text at the center of the large canvas (approximation, requires a large canvas)
    # Get the bounding box of the text to center it accurately
    # Since load_default might not support textbbox, we must estimate.
    # For robustness, we will use a simpler text size based on an arbitrary ratio
    
    # We use a placeholder font measurement to calculate size for centering
    try:
        # Measure bounding box with a system font (if available) for better centering
        temp_font_measure = ImageFont.truetype("arial.ttf", canvas // 2)
        bbox = draw.textbbox((0, 0), text, font=temp_font_measure)
    except IOError:
        # Fallback for measuring if no system font is found (less accurate)
        bbox = [0, 0, canvas * 0.5, canvas * 0.5] # Estimate half the canvas size
        
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Center text manually using the large canvas
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
#  ISHIHARA PLATE GENERATOR
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
        # >>> FIX: INVERTED COLOR LOGIC <<<
        # If number_mask[y, x] is TRUE (part of the number), use number_palette.
        # This is the original logic. If the number is invisible, the logic must be wrong 
        # due to how the mask is created/read. We use background_palette if True.
        # This reverses the colors, fixing the "invisible number" issue.
        palette = background_palette if number_mask[y, x] else number_palette

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
#  HEX COLOR → RGB CONVERSION (KEEP FOR COMPLETENESS, though unused here)
# --------------------------------------------------------------

def hex_to_rgb_float(hex_color):
    """
    Converts a hex string to an RGB float list [0-1].
    """
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4)]
