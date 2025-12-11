import streamlit as st
from Ishihara_generator import generate_ishihara_with_text  # >>> CHANGED: updated import

st.set_page_config(
    page_title="VisionCraft: Custom Color Blindness Plates",
    layout="wide"
)

# --- Left column for title and main controls ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.title("VisionCraft: Empowering Experts to Create Custom Color Blindness Tests")
    st.markdown("Create simple Ishihara-style color vision test plates interactively.")
    
    # --- Choose Plate Mode below the title ---
    mode = st.selectbox("Choose Plate Mode", ["Create New Plate", "Use Ready Plate"])

    if mode == "Create New Plate":

        # >>> ADDED: Allow choosing between number or letter
        content_type = st.selectbox("Plate Content Type", ["Number", "Letter"])

        # >>> CHANGED: Input changes depending on content type
        if content_type == "Number":
            content = st.text_input("Enter Number", "12")
        else:
            content = st.text_input("Enter Letter", "A")

        size = st.slider("Image Size", 300, 1000, 500, 50)
        num_dots = st.slider("Number of Dots", 500, 5000, 2500, 100)
        min_r = st.slider("Min Dot Radius", 2, 10, 4)
        max_r = st.slider("Max Dot Radius", 4, 20, 8)

        generate = st.button("Generate Plate")

    elif mode == "Use Ready Plate":
        uploaded_file = st.file_uploader("Upload your Ishihara plate image", type=["png","jpg","jpeg"])

# --- Right column for color pickers ---
with right_col:
    if mode == "Create New Plate":
        st.subheader("Number / Letter Dot Colors")  # >>> CHANGED label
        num_number_colors = st.slider("How many Number/Letter Colors to use?", 1, 6, 3)
        number_colors = []
        for i in range(num_number_colors):
            default = ["#ff6666","#ff9999","#ff3333", "#d44444", "#cc7a7a", "#e60b0b"][i]
            color = st.color_picker(f"Text Color {i+1}", default)  # >>> CHANGED label
            number_colors.append(color)

        st.subheader("Background Dot Colors")
        num_bg_colors = st.slider("How many Background Colors to use?", 1, 6, 3)
        background_colors = []
        for i in range(num_bg_colors):
            default = ["#33cc33","#66ff66","#009933", "#0be66a", "#07a34a", "#237547"][i]
            color = st.color_picker(f"Background Color {i+1}", default)
            background_colors.append(color)

# --- Generate and display the plate ---
if mode == "Create New Plate" and generate:
    with st.spinner("Generating Ishihara plate..."):

        # Convert hex to RGB floats
        def hex_to_rgb_float(hex_color):
            hex_color = hex_color.lstrip('#')
            return [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)]

        number_colors_rgb = [hex_to_rgb_float(c) for c in number_colors]
        background_colors_rgb = [hex_to_rgb_float(c) for c in background_colors]

        # >>> CHANGED: Use new function and pass "content"
        buf = generate_ishihara_with_text(
            size=size,
            text=content,                     # >>> CHANGED
            radius_range=(min_r, max_r),
            num_dots=num_dots,
            number_colors=number_colors_rgb,
            background_colors=background_colors_rgb
        )

    # Display generated image on left side
    with left_col:
        st.image(buf, caption=f"Ishihara Plate: {content}", use_container_width=True)

    buf.seek(0)
    with right_col:
        st.download_button(
            "Download Plate",
            data=buf,
            file_name=f"ishihara_{content}.png",
            mime="image/png"
        )

# --- Display uploaded plate ---
if mode == "Use Ready Plate" and uploaded_file:
    with left_col:
        st.image(uploaded_file, caption="Uploaded Plate", use_container_width=True)
