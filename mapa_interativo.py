import streamlit as st
from streamlit.components.v1 import html
import json

# JavaScript para pegar a localização e enviar para o Python
geolocation_script = """
<script>
function sendLocationToPython(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: JSON.stringify({latitude: lat, longitude: lon})
    }, '*');
}

function handleError(error) {
    console.error("Erro na geolocalização:", error.message);
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: JSON.stringify({error: error.message})
    }, '*');
}

if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(sendLocationToPython, handleError);
} else {
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: JSON.stringify({error: "Geolocalização não suportada pelo navegador"})
    }, '*');
}
</script>
"""

# Interface principal
st.title("📍 Minha Localização")
st.write("Clique no botão abaixo para compartilhar sua localização:")

if st.button("Obter Minha Localização"):
    # Inicializa a variável de sessão se não existir
    if 'location' not in st.session_state:
        st.session_state.location = None
    
    # Executa o JavaScript
    html(geolocation_script, height=0)
    
    # Usamos um placeholder para capturar o retorno
    location_placeholder = st.empty()
    
    # Se já tivermos os dados, mostra eles
    if st.session_state.location:
        if 'error' in st.session_state.location:
            location_placeholder.error(f"Erro: {st.session_state.location['error']}")
        else:
            location_placeholder.success("Localização obtida com sucesso!")
            st.write(f"**Latitude:** {st.session_state.location['latitude']}")
            st.write(f"**Longitude:** {st.session_state.location['longitude']}")
            st.map(data=[{
                'lat': [float(st.session_state.location['latitude'])],
                'lon': [float(st.session_state.location['longitude'])]
            }], zoom=15)

# Captura o retorno do JavaScript
if st.session_state.get('location'):
    # Já mostramos os dados acima
    pass

# Função para processar mensagens do JavaScript (será chamada via callback)
def process_message():
    data = st.session_state.get('geolocation_data')
    if data:
        try:
            st.session_state.location = json.loads(data)
            st.rerun()
        except:
            st.session_state.location = {'error': 'Dados inválidos recebidos'}

# Registra o callback para receber os dados
html("""
<script>
// Envia os dados para o Streamlit quando a página carrega
function sendData() {
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    if (urlParams.has('geolocation_data')) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            key: 'geolocation_data',
            value: urlParams.get('geolocation_data')
        }, '*');
    }
}
// Executa quando a página carrega
window.addEventListener('load', sendData);
</script>
""", height=0)
