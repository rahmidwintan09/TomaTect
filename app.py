import streamlit as st
from PIL import Image
from ultralytics import YOLO
import tempfile
import gdown
import os

# === SETUP GDRIVE ===
MODEL_URL = "https://drive.google.com/file/d/1rmnWEytbPOrRymJUeohSykxnJG01-tIH/view?usp=sharing"  
MODEL_PATH = "/content/drive/MyDrive/KULIAH/PI RAHMI/best_fine_tune.pt"

# Download model jika belum ada
if not os.path.exists(MODEL_PATH):
    with st.spinner("Mengunduh model..."):
        gdown.download(MODEL_URL, MODEL_PATH, quiet=False)

# === APLIKASI ===
st.set_page_config(page_title="Deteksi Kualitas Tomat", layout="centered")
st.title("🍅 Deteksi Kualitas Buah Tomat (Grade A, B, C)")
st.write("Upload gambar tomat, dan sistem akan mendeteksi kualitasnya.")

if not os.path.exists(MODEL_PATH) or os.path.getsize(MODEL_PATH) < 10000:
    st.error("❌ Model gagal diunduh atau file corrupt.")
else:
    model = YOLO(MODEL_PATH)

# Upload gambar
uploaded_file = st.file_uploader("Upload Gambar Tomat", type=["jpg", "jpeg", "png", "heic"])

from PIL import Image, UnidentifiedImageError

if uploaded_file is not None:
    try:
        img = Image.open(uploaded_file)
    except UnidentifiedImageError:
        st.error("❌ Format gambar tidak didukung. Ubah ke .jpg, .jpeg, atau .png dulu ya!")
        st.stop()

    st.image(img, caption="Gambar yang Diupload", use_column_width=True)

    with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
        img.save(temp_file.name)
        results = model(temp_file.name)


        for r in results:
            r.save(filename="hasil.jpg")
            st.image("hasil.jpg", caption="Hasil Deteksi Grade", use_column_width=True)
