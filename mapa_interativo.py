import streamlit as st
import streamlit.components.v1 as components

def main():
    st.title("Obter Localização com Geolocalização")

    # Exibir a página com o código HTML/JavaScript
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Obter Localização</title>
    </head>
    <body>
        <h1>Clique no botão para compartilhar sua localização</h1>
        <button onclick="getLocation()">Obter Minha Localização</button>
        <p id="result"></p>
        
        <script>
            function getLocation() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            const lat = position.coords.latitude;
                            const lon = position.coords.longitude;
                            
                            // Envia a localização para o Streamlit
                            window.parent.postMessage({latitude: lat, longitude: lon}, "*");
                        },
                        function(error) {
                            alert("Erro ao obter localização: " + error.message);
                        }
                    );
                } else {
                    alert("Seu navegador não suporta geolocalização.");
                }
            }

        </script>
    </body>
    </html>
    """, height=600)

    # Recebe a localização do JavaScript
    location = st.experimental_get_query_params()
    if location:
        lat = location.get("latitude", [""])[0]
        lon = location.get("longitude", [""])[0]
        if lat and lon:
            st.success(f"Localização recebida! Latitude: {lat}, Longitude: {lon}")

if __name__ == '__main__':
    main()
