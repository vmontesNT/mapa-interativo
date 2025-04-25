import streamlit as st
from streamlit.components.v1 import html

# Função JavaScript para pegar a localização
def get_geolocation():
    return """
    <script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        // Envia para o Streamlit via window
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: {latitude: lat, longitude: lon}
                        }, '*');
                    },
                    function(error) {
                        console.error("Erro ao obter localização: " + error.message);
                    }
                );
            } else {
                alert("Seu navegador não suporta geolocalização.");
            }
        }
        getLocation();
    </script>
    """

# Interface do Streamlit
st.title("📍 Geolocalização no Streamlit")
st.write("Clique no botão para compartilhar sua localização:")

# Botão para acionar o JavaScript
if st.button("Obter Minha Localização"):
    html(get_geolocation(), height=0)  # Executa o JavaScript
    st.rerun()  # Força atualização (substitui experimental_rerun)

# Mostra os resultados (se existirem)
if "location" in st.session_state:
    st.success("Localização obtida!")
    st.write(f"**Latitude:** {st.session_state.location['latitude']}")
    st.write(f"**Longitude:** {st.session_state.location['longitude']}")

# Captura os dados enviados pelo JavaScript (usando st.query_params)
params = st.query_params
if "latitude" in params and "longitude" in params:
    lat = params["latitude"]
    lon = params["longitude"]
    st.session_state.location = {"latitude": lat, "longitude": lon}
    st.rerun()  # Atualiza a interface
