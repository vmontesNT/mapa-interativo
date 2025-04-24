import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import zipfile
import os
from math import radians, cos, sin, sqrt, atan2
from folium.plugins import LocateControl  # Importação correta do LocateControl

# Configuração da página
st.set_page_config(page_title="Áreas de Atuação", layout="wide")
st.title("📍 Monitoramento de Áreas de Atuação")

## 1. Configuração Inicial ##
DEFAULT_LOCATION = [-20.828997, -49.423328]  # Coordenadas com polígonos conhecidos

# Inicialização do estado da sessão
if 'map_center' not in st.session_state:
    st.session_state.map_center = DEFAULT_LOCATION
    st.session_state.user_location = None
    st.session_state.polygons_loaded = False

## 2. Carregamento do GeoJSON ##
@st.cache_data
def load_geojson_data():
    try:
        with zipfile.ZipFile("data/areas_cobertura.geojson.zip") as z:
            with z.open("areas_cobertura.geojson") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return {"type": "FeatureCollection", "features": []}

## 3. Cálculo de Distância ##
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Raio da Terra em km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

## 4. Filtro de Polígonos ##
def filter_polygons(geojson_data, center_point, radius_km=20):
    filtered_features = []
    for feature in geojson_data.get("features", []):
        try:
            polygon_coords = feature["geometry"]["coordinates"][0]
            for coord in polygon_coords:
                distance = calculate_distance(center_point[0], center_point[1], coord[1], coord[0])
                if distance <= radius_km:
                    filtered_features.append(feature)
                    break
        except (KeyError, TypeError):
            continue
    return filtered_features

## 5. Criação do Mapa ##
def create_map(center, polygons=[]):
    m = folium.Map(
        location=center,
        zoom_start=14,
        tiles="cartodbpositron",
        control_scale=True
    )
    
    # Adiciona controle de localização (configuração simplificada)
    LocateControl(auto_start=False).add_to(m)
    
    # Adiciona polígonos
    for polygon in polygons:
        folium.Polygon(
            locations=polygon["geometry"]["coordinates"][0],
            color='blue',
            fill=True,
            fill_opacity=0.4,
            weight=2
        ).add_to(m)
    
    # Adiciona marcador do usuário
    folium.Marker(
        location=center,
        popup="Sua Localização",
        icon=folium.Icon(color="red")
    ).add_to(m)
    
    # Adiciona círculo de 20km
    folium.Circle(
        location=center,
        radius=20000,
        color='green',
        fill=True,
        fill_opacity=0.1
    ).add_to(m)
    
    return m

## 6. Interface Principal ##
geojson_data = load_geojson_data()
filtered_polygons = filter_polygons(geojson_data, st.session_state.map_center)

# Cria e exibe o mapa principal
main_map = create_map(st.session_state.map_center, filtered_polygons)
map_data = st_folium(main_map, width=800, height=600, returned_objects=["last_location"])

## 7. Atualização de Localização ##
if map_data.get("last_location"):
    new_location = [map_data["last_location"]["lat"], map_data["last_location"]["lng"]]
    if new_location != st.session_state.map_center:
        st.session_state.map_center = new_location
        st.rerun()

## 8. Feedback ao Usuário ##
if filtered_polygons:
    st.success(f"{len(filtered_polygons)} áreas de cobertura encontradas!")
else:
    st.warning("Nenhuma área de cobertura encontrada neste local.")
    st.write(f"Coordenadas atuais: {st.session_state.map_center}")

if st.button("Resetar para Localização Padrão"):
    st.session_state.map_center = DEFAULT_LOCATION
    st.rerun()
