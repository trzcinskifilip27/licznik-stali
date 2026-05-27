import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="Licznik Stali", layout="wide")
st.title("Licznik Rur Stalowych")

# Menu boczne z ustawieniami
st.sidebar.header("Ustawienia detekcji")
min_dist = st.sidebar.slider("Minimalny dystans między rurami", 10, 100, 30)
param1 = st.sidebar.slider("Czułość wykrywania (Param1)", 10, 100, 50)
param2 = st.sidebar.slider("Czułość wykrywania (Param2)", 10, 100, 30)
min_r = st.sidebar.slider("Minimalna średnica (px)", 5, 50, 10)
max_r = st.sidebar.slider("Maksymalna średnica (px)", 50, 200, 100)

# NOWOŚĆ: Gilotyna (odcinanie obszaru)
st.sidebar.header("Gilotyna (Przytnij obszar)")
crop_top = st.sidebar.slider("Przytnij zdjęcie od góry (%)", 0, 50, 0)
crop_bottom = st.sidebar.slider("Przytnij zdjęcie od dołu (%)", 0, 50, 0)

uploaded_file = st.file_uploader("Wybierz zdjęcie rur...", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    img_array = np.array(image)
    
    # Zastosowanie przycinania (Gilotyna)
    h, w, _ = img_array.shape
    top_y = int(h * (crop_top / 100))
    bottom_y = int(h * (1 - crop_bottom / 100))
    img_cropped = img_array[top_y:bottom_y, 0:w]
    
    # Przetwarzanie
    gray = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, minDist=min_dist,
                               param1=param1, param2=param2, minRadius=min_r, maxRadius=max_r)
    
    # Wyświetlanie wyników
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv2.circle(img_cropped, (i[0], i[1]), i[2], (0, 255, 0), 3)
            cv2.circle(img_cropped, (i[0], i[1]), 2, (0, 0, 255), 3)
        
        st.subheader(f"Znaleziono sztuk: {len(circles[0])}")
        st.image(img_cropped, channels="BGR", use_column_width=True)
    else:
        st.write("Nie znaleziono żadnych rur. Spróbuj zmienić ustawienia suwaków.")
