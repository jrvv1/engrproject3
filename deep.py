import streamlit as st
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import io
import csv
import os

# Set page layout
st.set_page_config(layout="wide")

# --- Load Body Image (with fallback) ---
def load_body_image():
    image_files = [f for f in os.listdir() if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    body_images = [f for f in image_files if "human" in f.lower() or "body" in f.lower()]
    if body_images:
        try:
            return Image.open(body_images[0]).convert("RGBA")
        except Exception as e:
            st.error(f"Error loading image '{body_images[0]}': {e}")
    else:
        st.warning("No body outline image found. Using a blank placeholder.")
        return Image.new("RGBA", (500, 800), "white")

base_image = load_body_image()

# Initialize session state
if "dots" not in st.session_state:
    st.session_state.dots = []
if "entries" not in st.session_state:
    st.session_state.entries = []

# --- Function: Draw dots on the image ---
def get_image_with_dots(dots, current_dot=None, dot_size=6):
    img = base_image.copy()
    draw = ImageDraw.Draw(img)
    r = dot_size // 2
    for x, y in dots:
        draw.ellipse((x - r, y - r, x + r, y + r), fill="red")
    if current_dot:
        cx, cy = current_dot
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="blue")  # Show current slider position in blue
    return img

# --- Sidebar: Label input and actions ---
with st.sidebar:
    st.header("Add Entry")
    label = st.text_input("Label for current dots")
    dot_size = st.slider("Dot Size", min_value=2, max_value=30, value=6)

    if st.button("Save Entry"):
        if label and st.session_state.dots:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Save image with permanent dots
            entry_image = get_image_with_dots(st.session_state.dots.copy(), dot_size=dot_size)
            img_io = io.BytesIO()
            entry_image.save(img_io, format="PNG")
            img_bytes = img_io.getvalue()

            # Store image bytes instead of dot coordinates
            st.session_state.entries.append((date, label, img_bytes, dot_size))
            st.session_state.dots = []
            st.success("Entry saved.")
        else:
            st.warning("Please add at least one dot and a label.")

    if st.button("Undo Last Dot"):
        if st.session_state.dots:
            st.session_state.dots.pop()

    if st.button("Clear All Dots"):
        st.session_state.dots.clear()

# --- Main area: Title and instructions ---
st.title("🧍 Body Marking Tool (Web App)")
st.markdown("Use the sliders to position a blue dot, then click 'Add Dot'.")

# --- Resize image to fit display ---
display_width = 350
if base_image.width > 0:
    w_percent = display_width / base_image.width
    display_height = int(base_image.height * w_percent)
else:
    display_height = 800

# --- Manual dot input ---
st.subheader("🔵 Position Dot")
x = st.slider("X coordinate", 0, base_image.width - 1 if base_image.width > 0 else 499, base_image.width // 2 if base_image.width > 0 else 250)
y = st.slider("Y coordinate", 0, base_image.height - 1 if base_image.height > 0 else 799, base_image.height // 2 if base_image.height > 0 else 400)

# --- Render image with existing dots and current slider dot ---
image_with_current_dot = get_image_with_dots(st.session_state.dots, (x, y), dot_size)
img_bytes = io.BytesIO()
image_with_current_dot.save(img_bytes, format="PNG")
st.image(img_bytes.getvalue(), width=display_width)

if st.button("Add Dot"):
    st.session_state.dots.append((x, y))
    st.rerun()

# --- Display saved entries ---
st.subheader("📋 Saved Entries")

if st.session_state.entries:
    # Display DataFrame without coordinates
    df = pd.DataFrame([
        {"Date": date, "Label": label, "Dot Size": size}
        for date, label, _, size in st.session_state.entries
    ])
    st.dataframe(df)

    # Show image previews and download buttons
    for i, (date, label, img_bytes, size) in enumerate(st.session_state.entries):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{label}** — *{date}* (Dot size: {size})")
            st.image(img_bytes, width=200)
            st.download_button(
                label="📥 Download Image",
                data=img_bytes,
                file_name=f"{label.replace(' ', '_')}_{date.replace(':', '-')}.png",
                mime="image/png",
                key=f"img_download_{i}"
            )
        with col2:
            if st.button("❌ Delete", key=f"delete_{i}"):
                st.session_state.entries.pop(i)
                st.rerun()
else:
    st.info("No entries saved yet.")

# --- Export CSV (in memory) ---
if st.button("📥 Prepare CSV"):
    csv_io = io.StringIO()
    writer = csv.writer(csv_io)
    writer.writerow(["Date", "Label", "Dot Size"])
    for date, label, _, size in st.session_state.entries:
        writer.writerow([date, label, size])
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_io.getvalue(),
        file_name="body_markers_summary.csv",
        mime="text/csv"
    )
