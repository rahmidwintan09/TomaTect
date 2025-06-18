
import streamlit as st
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO
from fpdf import FPDF
import tempfile, gdown, os, json, io, datetime


# ╭───────────────────  AUTO-THEME  ───────────────────╮
#   Light ⬅︎ default | otomatis gelap jika device dark
# ╰─────────────────────────────────────────────────────╯
st.markdown(
    """
    <style id="auto-theme">
    @media (prefers-color-scheme: dark) {
      :root {
        --primary-color:#ff6347;
        --text-color:#eeeeee;
        --background-color:#1e1e1e;
        --secondary-background-color:#262730;
      }
    }
    @media (prefers-color-scheme: light), (prefers-color-scheme: no-preference) {
      :root {
        --primary-color:#d13b0c;
        --text-color:#000000;
        --background-color:#ffffff;
        --secondary-background-color:#fdfdf5;
      }
    }
    body, .stApp {
      background-color: var(--background-color);
      color: var(--text-color);
    }
    input, textarea, .stTextInput > div > div, .stPasswordInput > div > div,
    .stButton > button {
      background-color: var(--secondary-background-color) !important;
      color: var(--text-color) !important;
      border: 1px solid #ccc;
    }
    .stButton > button:hover {
      background-color: #ecebe1 !important;
      color: var(--text-color) !important;
    }
    ::placeholder { color:#666 !important; opacity:1; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────────
#  SELANJUTNYA TETAPI KODE LAMA TANPA BAGIAN THEME
# ───────────────────────────────────────────────
# (hapus: cur_theme/mode/force_rerun/apply_theme)

def force_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

st.set_page_config(page_title="🍅 TomaTect: Deteksi Kualitas Tomat", layout="centered")

# ………………………………………………………………………………………………………… 
# ↓↓↓ SELURUH BAGIAN LOGIN / SIGNUP / DETEKSI / PDF
#     TETAP SAMA DENGAN KODE TERAKHIR ANDA ↓↓↓
# …………………………………………………………………………………………………………




USER_FILE = "users.json"
def load_users():
    return json.load(open(USER_FILE)) if os.path.exists(USER_FILE) else {}
def save_users(u): json.dump(u, open(USER_FILE, "w"))

users = load_users()
defaults = { "logged_in": False, "page": "login", "username": "",
             "model": None, "label_names": {}, "sub_page": "Deteksi" }
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

def signup():
    st.title("Daftar Akun")
    u = st.text_input("Username Baru")
    p = st.text_input("Password", type="password")
    if st.button("Daftar"):
        if u in users:
            st.error("Username sudah ada.")
        elif not u or not p:
            st.warning("Username / Password kosong.")
        else:
            users[u] = p
            save_users(users)
            st.success("Berhasil daftar, silakan login.")
            st.session_state.page = "login"
            force_rerun()
    st.button("Kembali ke Login", on_click=lambda: st.session_state.update(page="login"))

def login():
    st.title("Login TomaTect")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state.update(logged_in=True, username=u, page="main")
            force_rerun()
        else:
            st.error("Username / Password salah.")
    st.button("Belum punya akun? Daftar", on_click=lambda: st.session_state.update(page="signup"))

def about_page():
    st.title("ℹ️ Tentang TomaTect")
    st.write("""
    **TomaTect** adalah aplikasi web interaktif yang dirancang untuk mendeteksi dan mengklasifikasikan kualitas buah tomat secara otomatis ke dalam tiga kategori: Grade A, B, dan C berdasarkan citra visual. Aplikasi ini memanfaatkan model YOLO (You Only Look Once) yang telah dilatih untuk mendeteksi morfologi dan fitur fisik tomat, seperti bentuk, ukuran, dan warna permukaan.

Aplikasi dibangun menggunakan framework Streamlit, sehingga pengguna hanya perlu mengunggah gambar tomat, dan hasil deteksi akan ditampilkan secara langsung dalam bentuk:
             
    • Bounding box pada setiap tomat yang terdeteksi,
             
    • Ringkasan jumlah masing-masing grade,
             
    • Fitur unduhan gambar hasil deteksi,
             
    • Laporan deteksi otomatis dalam format PDF.
             
TomaTect juga menyediakan fitur multi-user login, serta tampilan UI yang menyesuaikan mode terang/gelap berdasarkan pengaturan perangkat pengguna, menjadikannya modern, ringan, dan ramah pengguna.
    """)

def detect_page():
    st.title("🍅 TomaTect: Deteksi Kualitas Tomat")
    st.caption("Deteksi Tomat Sekarang!")

    MODEL_URL  = "https://drive.google.com/file/d/1ZE6fp6XCdQt1EHQLCfZkcVYKNr9-2RdD/view?usp=sharing"
    MODEL_PATH = "best.pt"

    # ── load model sekali saja ──
    if st.session_state.model is None:
        if not os.path.exists(MODEL_PATH):
            with st.spinner("Mengunduh model…"):
                gdown.download(MODEL_URL, MODEL_PATH, quiet=False, fuzzy=True)
        st.session_state.model = YOLO(MODEL_PATH)
        st.session_state.label_names = st.session_state.model.names

    model, NAMES = st.session_state.model, st.session_state.label_names

    # uploader multi-file
    uploaded_files = st.file_uploader(
        "Upload Gambar", type=["jpg", "jpeg", "png", "heic"],
        accept_multiple_files=True
    )
    if not uploaded_files:
        return

    # PDF gabungan
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for idx, uploaded in enumerate(uploaded_files, 1):
        st.markdown(f"### 📷 {uploaded.name}")

        try:
            img = Image.open(uploaded).convert("RGB")
        except UnidentifiedImageError:
            st.error("Format tidak didukung.");  continue
        st.image(img, caption="Gambar Asli", use_container_width=True)

        # simpan sementara > inferensi
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
            img.save(tf.name)
            temp_path = tf.name

        r = model(temp_path)[0]
        annotated = Image.fromarray(r.plot()[..., ::-1])
        st.image(annotated, caption="Hasil Deteksi", use_container_width=True)

        # hitung grade
        cls = [NAMES[int(i)] for i in (r.boxes.cls.tolist() if r.boxes else [])]
        a, b, c = cls.count("A"), cls.count("B"), cls.count("C")
        col1, col2, col3 = st.columns(3)
        col1.metric("Grade A", a); col2.metric("Grade B", b); col3.metric("Grade C", c)

        # tombol download gambar individual
        buf = io.BytesIO()
        annotated.save(buf, format="JPEG")
        st.download_button(f"Download Gambar – {uploaded.name}",
                           buf.getvalue(), f"hasil_{uploaded.name}", "image/jpeg")

               # ── tambahkan ke PDF (tulisan di atas gambar) ──
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        # tulis info deteksi di bagian atas
        pdf.set_xy(10, 10)
        pdf.multi_cell(0, 8,
            f"[{idx}] {uploaded.name}\n"
            f"Grade A : {a}   Grade B : {b}   Grade C : {c}\n"
            f"Tanggal  : {datetime.datetime.now():%d/%m/%Y %H:%M}\n"
            f"Pengguna : {st.session_state.username}"
        )

        # kemudian simpan dan tampilkan gambar hasil anotasi
        img_path = f"{temp_path}_annot.jpg"
        annotated.save(img_path)

        # posisi gambar dimulai setelah teks (misal mulai dari Y = 50)
        pdf.image(img_path, x=20, y=55, w=170, h=140)

        os.remove(img_path)
        os.remove(temp_path)



    # tombol download PDF gabungan
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    st.download_button("📄 Download Laporan (PDF)",
                       pdf_bytes, "laporan_tomatect_semua.pdf", "application/pdf")



def main_app():
    with st.sidebar:
        st.markdown(f"👤 **{st.session_state.username}**")
        st.session_state.sub_page = st.radio("Navigasi", ["Deteksi", "Tentang"])
        if st.button("Logout"):
            st.session_state.update(logged_in=False, page="login", username="")
            force_rerun()
    if st.session_state.sub_page == "Tentang":
        about_page()
    else:
        detect_page()

if st.session_state.page == "signup":
    signup()
elif not st.session_state.logged_in:
    login()
elif st.session_state.page == "main":
    main_app()
else:
    st.session_state.page = "login"; login()
