import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import date
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

st.set_page_config(page_title="Adicionar Acidentes", page_icon="🚗", layout='wide',initial_sidebar_state="collapsed")
#st.title("Adicionar Acidentes")

# Autenticação 
# vide (https://blog.streamlit.io/streamlit-authenticator-part-1-adding-an-authentication-component-to-your-app/#how-to-install-streamlit-authenticator)
# ou (https://github.com/mkhorasani/Streamlit-Authenticator?ref=blog.streamlit.io)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Para fazer o hash das senhas
#hashed_passwords = stauth.Hasher(['123','abc']).generate()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

try:
    authenticator.login()
except Exception as e:
    st.error(e)

if st.session_state['authentication_status']:
    authenticator.logout(key='add')
    if st.session_state['username'] == 'admin':
        st.title(f'Olá *{st.session_state["name"]}*')

        # Página inteira
        @st.cache_data
        def read_acidentes():
            acidentes = pd.read_csv("dados/acidentes.csv")
            return acidentes

        st.session_state.acidentes = read_acidentes()
        linha1 = st.columns([1])
        linha = st.columns([1, 1])

        def concat(): # Junta o arquivo original com os dados novos
            if "dfgeo" not in st.session_state or st.session_state.dfgeo.empty:
                st.warning("Por favor, carregue um arquivo e realize o geocoding antes de adicionar os acidentes.")
                return
            
            df = st.session_state.dfgeo
            
            acidentes = st.session_state.acidentes
            acidentes = pd.concat([acidentes, df], ignore_index=True)
            acidentes = acidentes[['data', 'hora', 'dia_semana', 'logradouro', 'numero', 
                                   'cruzamento', 'tipo_acidente', 'gravidade', 'tempo', 
                                   'lat', 'lon','types', 'bairro']]
            acidentes.to_csv("dados/acidentes2.csv", index=False)

            return st.success("Acidentes adicionados com sucesso!")

        dfgeo = pd.DataFrame()

        def geocoding(): # Autoexplicativo
            if "df" not in st.session_state or st.session_state.df.empty:
                st.warning("Por favor, carregue um arquivo antes de realizar o geocoding.")
                return
            
            df = st.session_state.df

            # Versão gratuita (Nominatim) (Não sabe o que é um cruzamento)
            geolocator = Nominatim(user_agent="acidentes_app/1.0 (cetsantoscpmu@gmail.com)")
            
            for i, row in df.iterrows():
                if row['lat'] == '':
                    try:
                        # Montar o endereço considerando se há cruzamento
                        if pd.notna(row['cruzamento']): 
                            address = f"{row['logradouro']} com {row['cruzamento']}, Santos, SP, Brazil"
                        else:
                            address = f"{row['logradouro']} {row['numero']}, Santos, SP, Brazil"
                        
                        location = geolocator.geocode(address)
                        
                        if location:
                            df.at[i, 'lat'] = location.latitude
                            df.at[i, 'lon'] = location.longitude
                            df.at[i, 'types'] = location.raw.get('type', '')
                            df.at[i, 'bairro'] = location.raw.get('address', {}).get('suburb', '')
                        else:
                            st.warning(f"Endereço não encontrado: {address}",)
                            df.at[i, 'lat'] = '0'
                            df.at[i, 'lon'] = '0'
                        
                        time.sleep(2)  # Limite de requisições (1 por segundo)
                    
                    except GeocoderTimedOut:
                        st.warning(f"Timeout para o endereço: {address}")

            # Versão paga (Google Maps) (Pode resultar em coordenadas incorretas)

            # chave = userdata.get('chave')
            # gmaps = googlemaps.Client(key=chave)

            # for index, row in df.iterrows():
            # if pd.isna(row['cruzamento']):
            #     local = str(row['numero']) + ' ' + str(row['logradouro'])
            # else:
            #     local = str(row['logradouro']) + ' ' + str(row['cruzamento'])

            # geocode_result = gmaps.geocode(f'{local}, Santos, SP, Brazil')

            # if pd.isna(row['cruzamento']):
            #     if len(geocode_result[0]['address_components']) > 2 and 'long_name' in geocode_result[0]['address_components'][2]:
            #     df.at[index, 'bairro'] = geocode_result[0]['address_components'][2]['long_name']
            #     else:
            #     print(index)
            #     df.at[index, 'bairro'] = 'Bairro não encontrado'
            # else:
            #     if len(geocode_result[0]['address_components']) > 2 and 'long_name' in geocode_result[0]['address_components'][2]:
            #     df.at[index, 'bairro'] = geocode_result[0]['address_components'][1]['long_name']
            #     else:
            #     print(index)
            #     df.at[index, 'bairro'] = 'Bairro não encontrado'

            # df.at[index, 'types'] = geocode_result[0]['types']
            # df.at[index, 'lat'] = geocode_result[0]['geometry']['location']['lat']
            # df.at[index, 'lon'] = geocode_result[0]['geometry']['location']['lon']

            dfgeo = df # Salva o dataframe com as coordenadas
            st.session_state.dfgeo = dfgeo # Salva o dataframe na sessão
        
        def update_mapa():
            m = st_folium(mapa(st.session_state.dfgeo), height=500, width=700)
            output = st.empty()
            with output:
                output.clear()
                output = st_folium(m, height=500, width=700)
                
        def mapa(df):
            m = folium.Map(location=[-23.959, -46.342], zoom_start=12)
            # Add markers for each accident
            gravidade_colors = {
                'C/ VÍTIMAS LEVES': 'green',
                'C/ VÍTIMAS GRAVES': 'orange',
                'C/ VÍTIMAS FATAIS': 'red',
                'S/ LESÃO': 'blue'
            }

            for _, row in df.iterrows():
                try:
                    # Valide os valores de lat/lon
                    lat = float(row['lat'])
                    lon = float(row['lon'])
                    
                    gravidade = row['gravidade']
                    color = gravidade_colors.get(gravidade, 'gray')

                    # Adicione o marcador ao mapa
                    folium.Marker(
                        location=[lat, lon],
                        popup=(
                            f"Logradouro: {row['logradouro']}<br>"
                            f"Número: {row['numero']}<br>"
                            f"Cruzamento: {row['cruzamento']}<br>"
                            f"Gravidade: {row['gravidade']}"
                        ),
                        icon=folium.Icon(color=color, icon='car-burst', prefix='fa')
                    ).add_to(m)
                except (ValueError, TypeError):
                    # Ignore linhas com lat/lon inválidas
                    continue

            m.add_child(folium.LatLngPopup())

            return m
            
        dados = linha1[0].file_uploader("Escolha um arquivo", type=["xls"], accept_multiple_files=False)

        if dados is not None:
            df = pd.read_excel(dados)
            df['DATA'] = pd.to_datetime(df['DATA'])
            df.rename(columns={'Nº': 'NUMERO'}, inplace=True)
            df['NUMERO'] = df['NUMERO'].astype(str)
            df['lat'] = ''
            df['lon'] = ''
            df['types'] = ''
            df['bairro'] = ''
            df.rename(columns={'DATA': 'data', 'HORA': 'hora', 'TEMPO': 'tempo',
                            'TIPO_ACIDENTE': 'tipo_acidente', 'GRAVIDADE': 'gravidade',
                            'LOGRADOURO': 'logradouro', 'NUMERO': 'numero', 'CRUZAMENTO': 'cruzamento'}, inplace=True)
            df['dia_semana'] = (df['data'].dt.dayofweek)
            dias = {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 1}
            df['dia_semana'] = df['dia_semana'].map(dias)
            st.session_state.df = df
            
        if st.session_state.get('df') is not None:
            if st.button("Realizar Geocoding"):
                geocoding()
        if st.session_state.get("dfgeo") is not None:
            with linha[0]:
                st.write("Mapa de Acidentes por Gravidade")
                output = st_folium(mapa(st.session_state.dfgeo), height=500, width=700)
            with linha[1]:
                st.write("Dados")
                editor = st.data_editor(st.session_state.dfgeo, 
                                        hide_index=True, 
                                        column_order=['lat','lon','data_hora','dia_semana','logradouro',
                                                      'numero','cruzamento','tipo_acidente','gravidade',
                                                      'tempo'])
                if st.button("Atualizar Mapa"):
                    st.session_state.dfgeo = editor
                    update_mapa()    
            botaoC = st.button("Concatenar", on_click=concat)
    else:
        st.title('Você não tem acesso a esta página')
elif st.session_state['authentication_status'] is False:
    st.error('Usuário ou senha inválidos')
elif st.session_state['authentication_status'] is None:
    st.warning('Por favor, faça o login')