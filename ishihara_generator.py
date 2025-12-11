import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io

# --------------------------------------------------------------
#  TEXT MASK GENERATOR (large but safe letter/number)
# --------------------------------------------------------------

def generate_text_mask(size, text):
    """
    Generates a centered boolean mask where the text fills approx 80–85%
    of the 2/3 plate diameter—large, readable, but never touching edges.
    """
    target_ratio = 2 / 3                # target portion of plate
    safety_scale = 3.5                 # adjust to make letter bigger/smaller

    target_size = int(size * target_ratio * safety_scale)

    # Large temporary canvas for quality
    canvas = size * 4
    temp_img = Image.new("L", (canvas, canvas), 255)
    draw = ImageDraw.Draw(temp_img)

    # Start with huge font
    try:
        font = ImageFont.truetype("arial.ttf", canvas)
    except:
        font = ImageFont.load_default()

    # Measure bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Compute scale based on max dimension
    scale = target_size / max(w, h)
    font_size = max(10, int(canvas * scale))

    # Reload font with correct size
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Draw again with scaled font
    temp_img = Image.new("L", (canvas, canvas), 255)
    draw = ImageDraw.Draw(temp_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Center text
    x = (canvas - w) // 2 - bbox[0]
    y = (canvas - h) // 2 - bbox[1]
    draw.text((x, y), text, fill=0, font=font)

    # Downscale to final plate size
    final = temp_img.resize((size, size), Image.LANCZOS)
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
        palette = number_palette if number_mask[y, x] else background_palette
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
#  HEX COLOR → RGB CONVERSION
# --------------------------------------------------------------

def hex_to_rgb_float(hex_color):
    """
    Converts a hex string to an RGB float list [0-1].
    """
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4)]
