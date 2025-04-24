import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import Point, Polygon
from math import radians, sin, cos, sqrt, atan2
import webbrowser
import os
import tempfile
import shutil
from folium.plugins import LocateControl
import zipfile

# Configurações
st.set_page_config(page_title="Áreas de Atuação", layout="wide")
st.title("📍 Monitoramento de Áreas de Atuação")

# Caminho do arquivo JSON (agora relativo e zipado)
json_zip_path = os.path.join(os.path.dirname(__file__), "data", "areas_cobertura.geojson.zip")
json_filename = "areas_cobertura.geojson"  # Nome do arquivo dentro do ZIP

# Inicializar variáveis de sessão para localização
if 'latitude' not in st.session_state:
    st.session_state.latitude = -26.200259324  # Valor padrão
    st.session_state.longitude = -52.6997003783  # Valor padrão

# Criar mapa inicial para captura de localização
mapa_localizacao = folium.Map(
    location=[st.session_state.latitude, st.session_state.longitude],
    zoom_start=12,
    tiles="cartodbpositron"
)

# Adicionar controle de localização
LocateControl(
    auto_start=True,
    keepCurrentZoomLevel=True,
    drawMarker=True,
    locate_options={"enableHighAccuracy": True}
).add_to(mapa_localizacao)

# Renderizar mapa para capturar localização
map_data = st_folium(mapa_localizacao, width=1, height=1, returned_objects=["last_location"])

# Atualizar localização se obtida
if map_data and map_data.get("last_location"):
    st.session_state.latitude = map_data["last_location"]["lat"]
    st.session_state.longitude = map_data["last_location"]["lng"]

# Função para calcular distância entre coordenadas (Haversine)
def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371.0  # Raio da Terra em km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# Carregar dados do JSON ZIPADO
def carregar_dados_json():
    try:
        with zipfile.ZipFile(json_zip_path, 'r') as z:
            with z.open(json_filename) as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar arquivo GeoJSON: {str(e)}")
        return {"features": []}  # Retorna estrutura vazia em caso de erro

# Função para gerar o mapa
def criar_mapa(poligonos_filtrados):
    # Criar mapa base
    m = folium.Map(
        location=[st.session_state.latitude, st.session_state.longitude], 
        zoom_start=12,
        tiles="cartodbpositron",
        control_scale=True
    )
    
    # Adicionar polígonos ao mapa
    for feature in poligonos_filtrados:
        # Verifica se as coordenadas estão no formato correto
        if "geometry" in feature:
            coordinates = feature["geometry"]["coordinates"][0]  # Para Polygon
        else:
            coordinates = feature["coordinates"]  # Formato alternativo
        
        folium.Polygon(
            locations=coordinates,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.2,
            weight=2,
            tooltip=feature.get("name", "Área sem nome")
        ).add_to(m)
    
    # Adicionar marcador do vendedor
    folium.Marker(
        location=[st.session_state.latitude, st.session_state.longitude],
        popup="<b>Você está aqui</b>",
        icon=folium.Icon(color="red", icon="user")
    ).add_to(m)
    
    # Adicionar círculo de 20km
    folium.Circle(
        location=[st.session_state.latitude, st.session_state.longitude],
        radius=20000,
        color="green",
        fill=True,
        fill_opacity=0.05,
        tooltip="Raio de 20km"
    ).add_to(m)
    
    return m

# Função para salvar o mapa em um arquivo temporário HTML
def salvar_mapa_como_html(mapa):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        mapa.save(tmp_file.name)
        return tmp_file.name

# Carregar dados do JSON
dados_json = carregar_dados_json()

# Filtrar polígonos dentro do raio de 20km
poligonos_filtrados = []
for feature in dados_json.get("features", []):
    try:
        # Obtém as coordenadas do polígono
        if "geometry" in feature:
            coordinates = feature["geometry"]["coordinates"][0]  # Para Polygon
        else:
            coordinates = feature.get("coordinates", [])
        
        # Verifica cada coordenada do polígono
        for coord in coordinates:
            # Alguns GeoJSON armazenam como [lon, lat], outros como [lat, lon]
            if len(coord) >= 2:
                lon, lat = coord[0], coord[1]
                dist = calcular_distancia(st.session_state.latitude, st.session_state.longitude, lat, lon)
                if dist <= 20:
                    poligonos_filtrados.append(feature)
                    break
    except Exception as e:
        st.warning(f"Erro ao processar feature: {str(e)}")
        continue

# Interface principal
if poligonos_filtrados:
    if st.button("Atualizar Mapa"):
        mapa = criar_mapa(poligonos_filtrados)
        mapa_html_path = salvar_mapa_como_html(mapa)
        
        st.subheader("Mapa de Áreas de Atuação")
        st.components.v1.html(open(mapa_html_path, "r", encoding='utf-8').read(), 
                             height=600, width=800)
        
        os.remove(mapa_html_path)
    else:
        st.write("Clique no botão para atualizar o mapa")
else:
    st.warning("Nenhuma área encontrada no raio de 20km. Verifique sua localização ou os dados do GeoJSON.")
