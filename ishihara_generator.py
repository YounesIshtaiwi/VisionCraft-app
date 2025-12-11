import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io


def generate_number_mask(size, number):
    img = Image.new('L', (size, size), color=255)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("fonts/arial.ttf", size * 2 // 3)
    except IOError:
        font = ImageFont.load_default()

    temp_img = Image.new('L', (size, size), color=255)
    temp_draw = ImageDraw.Draw(temp_img)
    temp_draw.text((0, 0), number, fill=0, font=font)
    temp_np = np.array(temp_img)
    ys, xs = np.where(temp_np < 128)
    if len(xs) == 0 or len(ys) == 0:
        return np.zeros((size, size), dtype=bool)
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    text_width = x_max - x_min
    text_height = y_max - y_min
    text_x = (size - text_width) // 2 - x_min
    text_y = (size - text_height) // 2 - y_min
    img = Image.new('L', (size, size), color=255)
    draw = ImageDraw.Draw(img)
    draw.text((text_x, text_y), number, fill=0, font=font)
    mask = np.array(img) < 128
    return mask


def generate_ishihara_with_number(
        size=500,
        number='69',
        radius_range=(4, 8),
        num_dots=2500,
        spacing_factor=1,
        number_colors=None,  # list of RGB floats
        background_colors=None  # list of RGB floats
):
    number_mask = generate_number_mask(size, number)
    center_x, center_y = size // 2, size // 2
    max_radius = max(radius_range)
    radius_limit = size // 2 - max_radius

    # Default palettes if no colors provided
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

        if dx ** 2 + dy ** 2 > radius_limit ** 2:
            attempts += 1
            continue

        too_close = any(
            (x - px) ** 2 + (y - py) ** 2 < (spacing_factor * (r + pr)) ** 2 for (px, py, pr) in placed_dots)
        if too_close:
            attempts += 1
            continue

        placed_dots.append((x, y, r))

        color_palette = number_palette if number_mask[y, x] else background_palette
        color = color_palette[np.random.randint(len(color_palette))]
        ax.add_patch(plt.Circle((x, y), r, color=color, linewidth=0))

    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.invert_yaxis()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf
