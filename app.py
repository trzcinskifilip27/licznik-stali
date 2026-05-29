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
    top_y = int(h * (crop_top / 100))
    bottom_y = int(h * (1 - crop_bottom / 100))
    cropped_image = image.crop((0, top_y, w, bottom_y))
    
    st.image(cropped_image, caption="Podgląd obszaru analizy", use_column_width=True)
    
    if st.button("Policz materiał", type="primary"):
        with st.spinner("AI analizuje zdjęcie..."):
            # Przygotowanie zdjęcia do wysłania
            buffered = io.BytesIO()
            cropped_image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
            
            # Zapytanie do serwera Roboflow
            url = f"https://detect.roboflow.com/{PROJECT_ID}?api_key={ROBOFLOW_API_KEY}&confidence={confidence}"
            response = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"})
            
            if response.status_code == 200:
                data = response.json()
                predictions = data.get("predictions", [])
                
                # Rysowanie znaczników
                draw = ImageDraw.Draw(cropped_image)
                for p in predictions:
                    x = p['x']
                    y = p['y']
                    w_box = p['width']
                    h_box = p['height']
                    
                    # Obliczanie rogów prostokąta
                    x0 = x - (w_box / 2)
                    y0 = y - (h_box / 2)
                    x1 = x + (w_box / 2)
                    y1 = y + (h_box / 2)
                    
                    draw.rectangle([x0, y0, x1, y1], outline="lime", width=5)
                
                st.success(f"Wynik inwentaryzacji: {len(predictions)} szt.")
                st.image(cropped_image, use_column_width=True)
            else:
                st.error("Błąd połączenia. Upewnij się, że wpisałeś poprawny klucz API!")
