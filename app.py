import streamlit as st
from ishihara_generator import generate_ishihara_with_number

st.set_page_config(
    page_title="VisionCraft: Custom Color Blindness Plates",
    layout="wide"
)

# --- Layout columns ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.title("VisionCraft: Custom Ishihara Plate Creator")
    st.markdown("Interactively generate Ishihara-style color blindness test plates.")

    # Mode selection
    mode = st.selectbox("Choose Plate Mode", ["Create New Plate", "Use Ready Plate"])

    if mode == "Create New Plate":
        number = st.text_input("Number", "12")
        size = st.slider("Image Size", 300, 1000, 500, 50)
        num_dots = st.slider("Number of Dots", 500, 5000, 2500, 100)
        min_r = st.slider("Min Dot Radius", 2, 10, 4)
        max_r = st.slider("Max Dot Radius", 4, 20, 8)

        generate = st.button("Generate Plate")

    elif mode == "Use Ready Plate":
        uploaded_file = st.file_uploader(
            "Upload your Ishihara plate image",
            type=["png", "jpg", "jpeg"]
        )

# --- Right column for color pickers ---
with right_col:
    if mode == "Create New Plate":
        st.subheader("Number Dot Colors")
        number_colors = []
        for i in range(3):
            defaults = ["#ff6666", "#ff9999", "#ff3333"]
            color = st.color_picker(f"Number Color {i + 1}", defaults[i])
            number_colors.append(color)

        st.subheader("Background Dot Colors")
        background_colors = []
        for i in range(3):
            defaults = ["#33cc33", "#66ff66", "#009933"]
            color = st.color_picker(f"Background Color {i + 1}", defaults[i])
            background_colors.append(color)

# --- Generate and display ---
if mode == "Create New Plate" and generate:
    with st.spinner("Generating Ishihara plate..."):

        def hex_to_rgb_float(h):
            h = h.lstrip("#")
            return [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]

        number_colors_rgb = [hex_to_rgb_float(c) for c in number_colors]
        background_colors_rgb = [hex_to_rgb_float(c) for c in background_colors]

        buf = generate_ishihara_with_number(
            size=size,
            number=number,
            radius_range=(min_r, max_r),
            num_dots=num_dots,
            number_colors=number_colors_rgb,
            background_colors=background_colors_rgb
        )

    with left_col:
        st.image(buf, caption=f"Ishihara Plate: {number}", use_container_width=True)

    buf.seek(0)
    with right_col:
        st.download_button(
            "Download Plate",
            data=buf,
            file_name=f"ishihara_{number}.png",
            mime="image/png"
        )

# --- Display uploaded ---
if mode == "Use Ready Plate" and uploaded_file:
    with left_col:
        st.image(uploaded_file, caption="Uploaded Plate", use_container_width=True)

