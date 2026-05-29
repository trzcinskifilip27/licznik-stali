import streamlit as st
import requests
import base64
import io
from PIL import Image, ImageDraw

# --- KONFIGURACJA ---
st.set_page_config(page_title="Licznik AI - FIL-MET", layout="wide")
st.title("Licznik Profili - Sztuczna Inteligencja")

# Klucz API i dane modelu
ROBOFLOW_API_KEY = "ytw88UnqukUMrVSArigV"
PROJECT_ID = "my-first-project-zr9qw/1"

# --- MENU BOCZNE ---
st.sidebar.header("Gilotyna (Przytnij obszar)")
crop_top = st.sidebar.slider("Odetnij górę (%)", 0, 50, 0)
crop_bottom = st.sidebar.slider("Odetnij dół (%)", 0, 50, 0)

st.sidebar.header("Czułość AI")
confidence = st.sidebar.slider("Pewność modelu (%)", 10, 100, 40)
st.sidebar.caption("Zmniejsz, jeśli program omija profile. Zwiększ, jeśli łapie śmieci.")

# --- GŁÓWNY PROGRAM ---
uploaded_file = st.file_uploader("Wybierz zdjęcie profili...", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Wczytanie obrazu
    image = Image.open(uploaded_file)
    
    # Gilotyna - docinanie
    w, h = image.size
