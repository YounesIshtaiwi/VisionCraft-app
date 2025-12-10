import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io


# ---------------------------------------------------------
# FONT LOADING (works on Streamlit Cloud + your 'fonts/arial.ttf')
# ---------------------------------------------------------
def load_font(size):
    try:
        return ImageFont.truetype("fonts/arial.ttf", size)
    except:
        # Fallback to system font
        try:
            return ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                size
            )
        except:
            return ImageFont.load_default()


# ---------------------------------------------------------
# BETTER NUMBER MASK (fixes the 'one red dot' issue)
# ---------------------------------------------------------
def generate_number_mask(size, number):
    # Initial font size estimate
    font_size = int(size * 0.6)
    font = load_font(font_size)

    # Temporary image to measure bounding box
    temp_img = Image.new("L", (size, size), 255)
    temp_draw = ImageDraw.Draw(temp_img)

    # Measure bounding box
    bbox = font.getbbox(number)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # If too big, scale down
    if text_w > size * 0.85:
        scale_factor = (size * 0.85) / text_w
        font_size = int(font_size * scale_factor)
        font = load_font(font_size)
        bbox = font.getbbox(number)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

    # Center the text
    x = (size - text_w) // 2
    y = (size - text_h) // 2

    # Final mask image
    mask_img = Image.new("L", (size, size), 255)
    mask_draw = ImageDraw.Draw(mask_img)
    mask_draw.text((x, y), number, font=font, fill=0)

    mask_np = np.array(mask_img) < 128
    return mask_np


# ---------------------------------------------------------
# MAIN GENERATOR
# ---------------------------------------------------------
def generate_ishihara_with_number(
        size=500,
        number='12',
        radius_range=(4, 8),
        num_dots=2500,
        number_colors=None,
        background_colors=None
):
    number_mask = generate_number_mask(size, number)

    center_x, center_y = size // 2, size // 2
    max_r = max(radius_range)
    radius_limit = size // 2 - max_r

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
    ax.set_aspect('equal')
    ax.axis('off')

    placed_dots = []
    attempts = 0
    max_attempts = num_dots * 10

    while len(placed_dots) < num_dots and attempts < max_attempts:
        r = np.random.uniform(*radius_range)
        x = np.random.randint(int(r), size - int(r))
        y = np.random.randint(int(r), size - int(r))

        dx = x - center_x
        dy = y - center_y

        if dx*dx + dy*dy > radius_limit * radius_limit:
            attempts += 1
            continue

        too_close = any((x - px)**2 + (y - py)**2 < (r + pr)**2
                        for (px, py, pr) in placed_dots)
        if too_close:
            attempts += 1
            continue

        placed_dots.append((x, y, r))

        color_palette = number_palette if number_mask[y, x] else background_palette
        color = color_palette[np.random.randint(len(color_palette))]

        ax.add_patch(plt.Circle((x, y), r, color=color))

    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.invert_yaxis()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf
