import streamlit as st
import cv2
import numpy as np
from PIL import Image

# Konfiguracja strony - dopasowana do wyświetlaczy mobilnych
st.set_page_config(page_title="FIL-MET | Licznik Materiałów", page_icon="🛠️", layout="centered")

# Estetyczne ostylowanie elementów interfejsu (czysty, techniczny wygląd)
st.markdown("""
    <style>
    .main-title { font-size: 22pt; font-weight: bold; color: #1E1E1E; text-align: center; margin-bottom: 5px; }
    .subtitle { font-size: 11pt; color: #555555; text-align: center; margin-bottom: 20px; }
    .result-box { padding: 15px; background-color: #F1F3F6; border-radius: 8px; border-left: 6px solid #0066CC; margin-top: 15px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛠️ Licznik Materiałów Hutniczych</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Aplikacja mobilna do szybkiej inwentaryzacji na placu i hali</div>', unsafe_allow_html=True)

# --- PANEL STEROWANIA (Menu boczne na komputerze / wysuwane od góry na telefonie) ---
st.sidebar.header("⚙️ Ustawienia Materiału")
typ_materialu = st.sidebar.selectbox(
    "Co chcesz policzyć?",
    ["Rury okrągłe", "Pręty okrągłe", "Profile kwadratowe/prostokątne", "Kątowniki / Ceowniki"]
)

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Parametry Algorytmu")
st.sidebar.write("Dostosuj suwaki, jeśli program pomija elementy lub łapie cienie.")

# Dynamiczne suwaki w zależności od wybranego asortymentu
if typ_materialu in ["Rury okrągłe", "Pręty okrągłe"]:
    czulosc = st.sidebar.slider("Czułość wykrywania okręgów (im mniej, tym czulszy)", min_value=10, max_value=60, value=25, step=1)
    min_dist = st.sidebar.slider("Minimalny dystans między środkami (px)", min_value=5, max_value=50, value=15, step=1)
    min_rad = st.sidebar.slider("Minimalna średnica (px)", min_value=2, max_value=50, value=6, step=1)
    max_rad = st.sidebar.slider("Maksymalna średnica (px)", min_value=10, max_value=100, value=25, step=1)
else:
    # Parametry dla kształtowników o przekroju prostokątnym/kątowym (detekcja konturów)
    prog_krawedzi = st.sidebar.slider("Próg odcięcia tła (jasność)", min_value=10, max_value=255, value=110, step=5)
    min_area = st.sidebar.slider("Minimalna wielkość profilu (px²)", min_value=10, max_value=500, value=40, step=5)
    max_area = st.sidebar.slider("Maksymalna wielkość profilu (px²)", min_value=500, max_value=5000, value=1500, step=50)

# --- SEKCJA KOREKTY RĘCZNEJ (Kluczowa funkcja na telefonie) ---
st.markdown("### ✏️ Ręczna korekta wyniku")
st.write("Jeśli algorytm nie policzył wszystkiego idealnie, użyj poniższych pól, aby poprawić wynik:")
col1, col2 = st.columns(2)
with col1:
    dodaj_sztuk = st.number_input("Dodaj pominięte sztuki (+)", min_value=0, value=0, step=1)
with col2:
    odejmij_sztuk = st.number_input("Odejmij fałszywe oznaczenia (-)", min_value=0, value=0, step=1)

# --- WGrywanie ZDJĘCIA (Aparat fotograficzny) ---
st.markdown("---")
uploaded_file = st.file_uploader("📷 Zrób zdjęcie smartfonem lub wybierz z galerii:", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Wczytanie i przygotowanie obrazu
    image = Image.open(uploaded_file)
    img_array = np.array(image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Standaryzacja rozdzielczości (stabilne działanie suwaków niezależnie od aparatu w telefonie)
    height, width = img_bgr.shape[:2]
    target_width = 1000
    target_height = int(height * (target_width / width))
    img_bgr = cv2.resize(img_bgr, (target_width, target_height))
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    output = img_bgr.copy()
    raw_count = 0

    # --- LOGIKA PRZETWARZANIA WIZYJNEGO (OpenCV) ---
    if typ_materialu in ["Rury okrągłe", "Pręty okrągłe"]:
        # Filtrowanie szumów (np. rdzy, brudu na metalu)
        blur = cv2.medianBlur(gray, 5)
        circles = cv2.HoughCircles(
            blur, cv2.HOUGH_GRADIENT, dp=1, minDist=min_dist,
            param1=50, param2=czulosc, minRadius=min_rad, maxRadius=max_rad
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            raw_count = len(circles[0])
            for i in circles[0, :]:
                # Rysowanie zielonej obwódki i czerwonego środka
                cv2.circle(output, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(output, (i[0], i[1]), 2, (0, 0, 255), 3)
                
    else:
        # Algorytm progowania adaptacyjnego dla profili, kątowników i ceowników
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, prog_krawedzi, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                x, y, w, h = cv2.boundingRect(cnt)
                # Odrzucamy skrajnie wąskie linie (szumy na zdjęciu)
                if w / h < 4 and h / w < 4:
                    cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.circle(output, (x + int(w/2), y + int(h/2)), 2, (0, 0, 255), 3)
                    raw_count += 1

    # --- OBLICZENIE I WYŚWIETLENIE FINALNEGO WYNIKU ---
    final_count = raw_count + dodaj_sztuk - odejmij_szerokosc = raw_count + dodaj_sztuk - odejmij_sztuk
    if final_count < 0:
        final_count = 0

    st.markdown(f"""
    <div class="result-box">
        <h3 style='margin:0; color:#1E1E1E; font-size:14pt;'>📊 Podsumowanie pomiaru:</h3>
        <p style='font-size:12pt; margin:5px 0 0 0;'>Wykryte automatycznie: <b>{raw_count} szt.</b></p>
        <p style='font-size:18pt; margin:5px 0 0 0; color:#0066CC;'>Ostateczna ilość: <b>{final_count} szt.</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Konwersja do wyświetlenia na ekranie telefonu
    output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
    st.image(output_rgb, caption="Podgląd detekcji (Zielone znaczniki = policzone pozycje)", use_container_width=True)
