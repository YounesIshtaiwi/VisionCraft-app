import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io
import streamlit as st

import os
st.write("Current directory:", os.getcwd())
st.write("Files in streamlit folder:", os.listdir("streamlit"))
st.write("Font exists?", os.path.isfile("streamlit/OpenSans-Regular.ttf"))

# -----------------------------
# FONT SETUP
# -----------------------------
FONT_PATH = "streamlit/OpenSans-Regular.ttf"

def load_font(size):
    try:
        font = ImageFont.truetype(FONT_PATH, size)
        st.write("✔ Font loaded:", FONT_PATH, "size:", size)
        return font
    except Exception as e:
        st.write("❌ FONT FAILED:", e)
        return ImageFont.load_default()

# --------------------------------------------------------------
#  TEXT MASK GENERATOR
# --------------------------------------------------------------
def generate_text_mask(size, text):
    """
    Generates a boolean mask with the text centered.
    """
    target_ratio = 2 / 3
    safety_scale = 3.5
    target_size = int(size * target_ratio * safety_scale)

    canvas = size * 4
    temp_img = Image.new("L", (canvas, canvas), 255)
    draw = ImageDraw.Draw(temp_img)

    font = load_font(canvas)

    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    scale = target_size / max(w, h)
    font_size = max(10, int(canvas * scale))

    font = load_font(font_size)

    temp_img = Image.new("L", (canvas, canvas), 255)
    draw = ImageDraw.Draw(temp_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = (canvas - w) // 2 - bbox[0]
    y = (canvas - h) // 2 - bbox[1]
    draw.text((x, y), text, fill=0, font=font)

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
    number_mask = generate_text_mask(size, text)

    center_x = center_y = size // 2
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
    ax.set_aspect("equal")
    ax.axis("off")

    placed = []
    attempts = 0
    max_attempts = num_dots * 10

    while len(placed) < num_dots and attempts < max_attempts:
        r = np.random.uniform(*radius_range)
        x = np.random.randint(int(r), size - int(r))
        y = np.random.randint(int(r), size - int(r))

        if (x - center_x)**2 + (y - center_y)**2 > radius_limit**2:
            attempts += 1
            continue

        if any((x - px)**2 + (y - py)**2 < (spacing_factor * (r + pr))**2
               for px, py, pr in placed):
            attempts += 1
            continue

        placed.append((x, y, r))

        palette = number_palette if number_mask[y, x] else background_palette
        color = palette[np.random.randint(len(palette))]

        ax.add_patch(plt.Circle((x, y), r, color=color))

    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.invert_yaxis()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close()
    buf.seek(0)

    return buf

# --------------------------------------------------------------
# HEX → RGB FLOAT
# --------------------------------------------------------------
def hex_to_rgb_float(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4)]


