import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl

def calculate_bounds(lat, lon, radius_km=100):
    radius = radius_km * 1000
    north = lat + (radius / 111320)
    south = lat - (radius / 111320)
    east = lon + (radius / (40008000 / 360))
    west = lon - (radius / (40008000 / 360))
    return [[south, west], [north, east]]

# Configuração do Streamlit
st.set_page_config(page_title="Mapa Interativo", layout="wide")
st.title("📍 Mapa Interativo com Localização Automática")

# Inicializa o mapa (localização padrão: Centro do Brasil)
m = folium.Map(location=[-15.788, -47.879], zoom_start=5, tiles="cartodbpositron")

# Adiciona o controle de localização
LocateControl(
    auto_start=True,
    keepCurrentZoomLevel=True,
    drawMarker=True,
    locate_options={"enableHighAccuracy": True}
).add_to(m)

# Renderiza o mapa e captura interações (incluindo localização)
map_data = st_folium(m, width=800, height=500, key="map")

# Se o usuário permitir a localização, ajusta os limites
if map_data.get("last_location"):
    user_lat = map_data["last_location"]["lat"]
    user_lon = map_data["last_location"]["lng"]
    bounds = calculate_bounds(user_lat, user_lon)
    st.success(f"Localização capturada: Latitude {user_lat}, Longitude {user_lon}")
    m.fit_bounds(bounds)