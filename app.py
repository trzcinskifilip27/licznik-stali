import streamlit as st
import requests
import base64
import io
from PIL import Image, ImageDraw

# --- KONFIGURACJA ---
st.set_page_config(page_title="Licznik AI - FIL-MET", layout="wide")
st.title("Licznik Materiałów Hutniczych")

# Klucz API (wspólny dla całego Twojego konta Roboflow)
ROBOFLOW_API_KEY = "ytw88UnqukUMrVSArigV"

# Baza modeli AI - tutaj w przyszłości podmienisz "TUTAJ_WPISZ..." na prawdziwe ID po wytrenowaniu
MODELS = {
    "Profile": "my-first-project-zr9qw/1",
    "Rury": "TUTAJ_WPISZ_ID_DLA_RUR",
    "Płaskowniki": "TUTAJ_WPISZ_ID_DLA_PLASKOWNIKOW",
    "Kątowniki": "TUTAJ_WPISZ_ID_DLA_KATOWNIKOW",
    "Ceowniki": "TUTAJ_WPISZ_ID_DLA_CEOWNIKOW",
    "Dwuteowniki": "TUTAJ_WPISZ_ID_DLA_DWUTEOWNIKOW",
    "Pręty": "TUTAJ_WPISZ_ID_DLA_PRETOW"
}

# --- MENU BOCZNE ---
st.sidebar.header("Rodzaj materiału")
material = st.sidebar.selectbox("Co dzisiaj liczymy?", list(MODELS.keys()))

st.sidebar.header("Gilotyna (Przytnij obszar)")
crop_top = st.sidebar.slider("Odetnij górę (%)", 0, 50, 0)
crop_bottom = st.sidebar.slider("Odetnij dół (%)", 0, 50, 0)
crop_left = st.sidebar.slider("Odetnij lewy bok (%)", 0, 50, 0)
crop_right = st.sidebar.slider("Odetnij prawy bok (%)", 0, 50, 0)

st.sidebar.header("Czułość AI")
confidence = st.sidebar.slider("Pewność modelu (%)", 10, 100, 40)
st.sidebar.caption("Zmniejsz, jeśli program omija sztuki. Zwiększ, jeśli łapie śmieci.")

# --- GŁÓWNY PROGRAM ---
uploaded_file = st.file_uploader(f"Wybierz zdjęcie dla asortymentu: {material}...", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Wczytanie obrazu
    image = Image.open(uploaded_file)
    w, h = image.size
    
    # Obliczanie współrzędnych cięcia dla 4 stron
    top_y = int(h * (crop_top / 100))
    bottom_y = int(h * (1 - crop_bottom / 100))
    left_x = int(w * (crop_left / 100))
    right_x = int(w * (1 - crop_right / 100))
    
    # Zabezpieczenie przed ucięciem całego zdjęcia
    if left_x >= right_x or top_y >= bottom_y:
        st.error("Błąd obszaru roboczego! Zostaw przynajmniej kawałek zdjęcia do analizy.")
    else:
        # Wycięcie właściwego kadru
        cropped_image = image.crop((left_x, top_y, right_x, bottom_y))
        st.image(cropped_image, caption="Podgląd obszaru analizy", use_column_width=True)
        
        if st.button("Policz materiał", type="primary"):
            selected_project_id = MODELS[material]
            
            # Sprawdzenie, czy model dla danego materiału istnieje
            if "TUTAJ_WPISZ" in selected_project_id:
                st.warning(f"Model sztucznej inteligencji dla kategorii '{material}' nie został jeszcze wdrożony. Wgraj zdjęcia na Roboflow, wytrenuj model i wklej jego ID w kodzie aplikacji!")
            else:
                with st.spinner("AI analizuje zdjęcie..."):
                    # Przygotowanie zdjęcia do wysłania
                    buffered = io.BytesIO()
                    cropped_image.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
                    
                    # Zapytanie do serwera Roboflow
                    url = f"https://detect.roboflow.com/{selected_project_id}?api_key={ROBOFLOW_API_KEY}&confidence={confidence}"
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
                            
                            x0 = x - (w_box / 2)
                            y0 = y - (h_box / 2)
                            x1 = x + (w_box / 2)
                            y1 = y + (h_box / 2)
                            
                            draw.rectangle([x0, y0, x1, y1], outline="lime", width=5)
                        
                        st.success(f"Wynik inwentaryzacji ({material}): {len(predictions)} szt.")
                        st.image(cropped_image, use_column_width=True)
                    else:
                        st.error("Błąd połączenia z serwerem. Spróbuj ponownie.")
