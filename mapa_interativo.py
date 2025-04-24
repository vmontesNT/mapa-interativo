import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from math import radians, sin, cos, sqrt, atan2
import os
import tempfile
from folium.plugins import LocateControl
import zipfile

# ========== CONFIGURAÇÕES INICIAIS ==========
st.set_page_config(page_title="Áreas de Atuação", layout="wide")
st.title("📍 Monitoramento de Áreas de Atuação")

# 1. VALORES PADRÃO ATUALIZADOS PARA BELÉM/PA
DEFAULT_LATITUDE = -20.828997  # Latitude de Belém
DEFAULT_LONGITUDE = -49.423328  # Longitude de Belém

# ========== GERENCIAMENTO DE LOCALIZAÇÃO ==========
if 'latitude' not in st.session_state:
    st.session_state.latitude = DEFAULT_LATITUDE
    st.session_state.longitude = DEFAULT_LONGITUDE

# Mapa principal
mapa = folium.Map(
    location=[st.session_state.latitude, st.session_state.longitude],
    zoom_start=12,
    tiles="cartodbpositron"
)

# Controle de localização aprimorado
lc = LocateControl(
    auto_start=False,  # Agora requer interação do usuário
    strings={"title": "Clique para usar minha localização"},
    locate_options={"enableHighAccuracy": True, "timeout": 15}
)
lc.add_to(mapa)

# Botão para forçar atualização
if st.button("🔍 Usar Minha Localização Atual"):
    st.session_state.force_update = True

# Renderização do mapa
map_data = st_folium(
    mapa,
    width=700,
    height=500,
    returned_objects=["last_location"]
)

# Atualização de coordenadas
if map_data.get("last_location"):
    new_lat = map_data["last_location"]["lat"]
    new_lng = map_data["last_location"]["lng"]
    if (abs(new_lat - st.session_state.latitude) > 0.0001) or \
       (abs(new_lng - st.session_state.longitude) > 0.0001):
        st.session_state.latitude = new_lat
        st.session_state.longitude = new_lng
        st.rerun()

# ========== FUNÇÕES DO GEOJSON ==========
def carregar_dados_json():
    json_zip_path = os.path.join("data", "areas_cobertura.geojson.zip")
    try:
        with zipfile.ZipFile(json_zip_path, 'r') as z:
            with z.open("areas_cobertura.geojson") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {str(e)}")
        return {"features": []}

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371.0  # Raio da Terra em km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

# ========== PROCESSAMENTO DO MAPA ==========
dados_json = carregar_dados_json()
poligonos_filtrados = []

for feature in dados_json.get("features", []):
    try:
        coords = feature.get("geometry", {}).get("coordinates", [[]])[0]
        for coord in coords:
            if len(coord) >= 2:
                distancia = calcular_distancia(
                    st.session_state.latitude, st.session_state.longitude,
                    coord[1], coord[0]  # GeoJSON usa [lon, lat]
                )
                if distancia <= 20:
                    poligonos_filtrados.append(feature)
                    break
    except Exception:
        continue

# ========== RENDERIZAÇÃO FINAL ==========
def criar_mapa_completo():
    m = folium.Map(
        location=[st.session_state.latitude, st.session_state.longitude],
        zoom_start=12,
        tiles="cartodbpositron"
    )
    
    # Polígonos (se existirem)
    for feature in poligonos_filtrados:
        folium.Polygon(
            locations=feature["geometry"]["coordinates"][0],
            color='blue',
            fill=True,
            tooltip=feature.get("properties", {}).get("name", "Área")
        ).add_to(m)
    
    # Marcador do usuário
    folium.Marker(
        [st.session_state.latitude, st.session_state.longitude],
        popup="Sua Localização",
        icon=folium.Icon(color="red")
    ).add_to(m)
    
    # Círculo de 20km
    folium.Circle(
        [st.session_state.latitude, st.session_state.longitude],
        radius=20000,
        color='green',
        fill=True,
        fill_opacity=0.1
    ).add_to(m)
    
    return m

# Exibição do mapa
mapa_final = criar_mapa_completo()
mapa_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
mapa_final.save(mapa_html.name)
st.components.v1.html(open(mapa_html.name, "r").read(), height=600)
os.unlink(mapa_html.name)

# Feedback visual
if not poligonos_filtrados:
    st.warning("Nenhuma área encontrada em 20km. Verifique sua localização.")
else:
    st.success(f"{len(poligonos_filtrados)} áreas encontradas próximas a você!")
