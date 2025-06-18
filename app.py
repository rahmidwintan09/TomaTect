import streamlit as st
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO
import tempfile
import gdown
import os

# === SETUP GDRIVE === --------------------------------------------------
MODEL_URL  = "https://drive.google.com/file/d/1ZE6fp6XCdQt1EHQLCfZkcVYKNr9-2RdD/view?usp=sharing"
MODEL_PATH = "best.pt"

if not os.path.exists(MODEL_PATH):
    with st.spinner("🔄 Mengunduh model dari Google Drive..."):
        gdown.download(MODEL_URL, MODEL_PATH, quiet=False, fuzzy=True)

try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    st.error(f"❌ Gagal memuat model: {e}")
    st.stop()

# === APLIKASI STREAMLIT  ----------------------------------------------
st.set_page_config(page_title="Deteksi Kualitas Tomat", layout="centered")
st.title("🍅 Deteksi Kualitas Buah Tomat (Grade A, B, C)")
st.write("Upload gambar tomat, dan sistem akan mendeteksi kualitasnya.")

uploaded_file = st.file_uploader("Upload Gambar Tomat", type=["jpg", "jpeg", "png", "heic"])

if uploaded_file is not None:
    try:
        img = Image.open(uploaded_file)
    except UnidentifiedImageError:
        st.error("❌ Format gambar tidak didukung. Gunakan .jpg, .jpeg, .png, atau .heic.")
        st.stop()

    st.image(img, caption="Gambar yang Diupload", use_container_width=True)

    # --- Simpan ke file sementara untuk deteksi
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        temp_path = tf.name

    img.save(temp_path)
    results = model(temp_path)

    for r in results:
        # Plot hasil deteksi ke dalam array dengan bounding box
        result_img_array = r.plot()  # format numpy ndarray (BGR)
        result_img_pil = Image.fromarray(result_img_array[..., ::-1])  # konversi ke RGB

        # Tampilkan ke Streamlit
        st.image(result_img_pil, caption="Hasil Deteksi dengan Bounding Box", use_container_width=True)

    # Hapus file sementara
    os.remove(temp_path)
