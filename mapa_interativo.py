import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
import tempfile
from folium.plugins import LocateControl
import zipfile

# Configurações iniciais
st.set_page_config(page_title="Áreas de Atuação", layout="wide")
st.title("📍 Monitoramento de Áreas de Atuação")

# 1. LOCALIZAÇÃO - Valores padrão para um ponto conhecido em Belém
DEFAULT_LOCATION = [-1.4557, -48.4902]  # Centro de Belém

# Inicialização da sessão
if 'location' not in st.session_state:
    st.session_state.location = DEFAULT_LOCATION
    st.session_state.found_polygons = False

# 2. CARREGAMENTO DO GEOJSON - Versão mais robusta
@st.cache_data
def load_geojson():
    try:
        with zipfile.ZipFile("data/areas_cobertura.geojson.zip") as z:
            with z.open("areas_cobertura.geojson") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {str(e)}")
        return {"type": "FeatureCollection", "features": []}

# 3. MAPA PRINCIPAL - Única instância
def create_main_map():
    m = folium.Map(
        location=st.session_state.location,
        zoom_start=14,
        tiles="cartodbpositron",
        control_scale=True
    )
    
    # Controle de localização
    LocateControl(
        auto_start=False,
        strings={"title": "Clique para usar minha localização"},
        locate_options={"enableHighAccuracy": True, "timeout": 15}
    ).add_to(m)
    
    return m

# 4. ATUALIZAÇÃO DE LOCALIZAÇÃO
def update_location():
    if st.session_state.get("new_location"):
        st.session_state.location = st.session_state.new_location
        st.session_state.found_polygons = False
        st.rerun()

# Interface principal
main_map = create_main_map()

# Renderização do mapa
map_data = st_folium(
    main_map,
    key="main_map",
    width=700,
    height=500,
    returned_objects=["last_location"]
)

# Processamento da localização
if map_data.get("last_location"):
    new_loc = [map_data["last_location"]["lat"], map_data["last_location"]["lng"]
    if new_loc != st.session_state.location:
        st.session_state.new_location = new_loc
        update_location()

# 5. FILTRAGEM DE POLÍGONOS - Versão otimizada
def filter_polygons(data, center, radius_km=20):
    filtered = []
    for feature in data.get("features", []):
        try:
            polygon = feature["geometry"]["coordinates"][0]
            if any(is_point_near(center, point, radius_km) for point in polygon):
                filtered.append(feature)
        except (KeyError, TypeError):
            continue
    return filtered

def is_point_near(center, point, radius_km):
    # Conversão simples para cálculo aproximado
    lat_diff = abs(center[0] - point[1]) * 111  # 1 grau ≈ 111 km
    lon_diff = abs(center[1] - point[0]) * 111 * cos(radians(center[0]))
    return (lat_diff**2 + lon_diff**2)**0.5 <= radius_km

# Carregamento e filtragem
geojson_data = load_geojson()
filtered_polygons = filter_polygons(geojson_data, st.session_state.location)

# 6. ATUALIZAÇÃO DO MAPA - Adiciona elementos dinâmicos
if filtered_polygons:
    st.session_state.found_polygons = True
    with st.spinner("Atualizando mapa..."):
        for feature in filtered_polygons:
            folium.Polygon(
                locations=feature["geometry"]["coordinates"][0],
                color='blue',
                fill=True,
                fill_opacity=0.4,
                tooltip=feature.get("properties", {}).get("name", "Área de Cobertura")
            ).add_to(main_map)

# Elementos fixos do mapa
folium.Marker(
    st.session_state.location,
    popup="Sua Localização",
    icon=folium.Icon(color="red", icon="user")
).add_to(main_map)

folium.Circle(
    st.session_state.location,
    radius=20000,
    color='green',
    fill=True,
    fill_opacity=0.1,
    tooltip="Raio de 20km"
).add_to(main_map)

# Exibição final
st_folium(main_map, width=700, height=500)

# Feedback ao usuário
if not st.session_state.found_polygons:
    st.warning("""
    Nenhuma área de cobertura encontrada neste local. 
    Verifique se você está dentro da região de atendimento.
    """)
    st.write(f"Coordenadas atuais: {st.session_state.location}")
