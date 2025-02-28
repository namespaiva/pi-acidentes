import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import numpy as np
from datetime import date
st.set_page_config(page_title="Acidentes", page_icon="🚗", layout='wide',initial_sidebar_state="collapsed")
st.title("Dados de Acidentes")

@st.cache_data
def load_data():
    dados = pd.read_csv("dados/acidentes.csv")

    dados.sort_values(by=['data', 'hora'], inplace=True)
    dados.reset_index(drop=True, inplace=True)
    dados['data'] = pd.to_datetime(dados['data'])
    dados['data'] = pd.to_datetime(dados['data'].astype(str) + ' ' + dados['hora'])
    dados.drop(columns='hora', inplace=True)
    dados['dia_semana'] = (dados['data'].dt.dayofweek)
    dias = {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 1}
    dados['dia_semana'] = dados['dia_semana'].map(dias)
    dados.rename(columns={'lon':'lon','data':'data_hora'}, inplace=True)
    return dados

@st.cache_data
def load_frota():
    frota = pd.read_csv("dados/frota.csv")
    frota['Ano'] = pd.to_datetime(frota['Ano'], format='%Y')
    frota = frota[frota['Veículo'] != 'Total']
    return frota

# Carrega os dados
df = load_data()
dffrota = load_frota()

@st.cache_data
def apply_filters(df, filters):
    for filter_value, column in filters:
        if filter_value: 
            if column == 'data_hora':  # Para datas
                start, finish = filter_value
                if all(col in df.columns for col in ['Ano', 'Veículo', 'Contagem']):
                    df = df[(df['Ano'].dt.year >= start.year) & (df['Ano'].dt.year <= finish.year)]
                else:
                    df = df[(df['data_hora'] >= start) & (df['data_hora'] <= finish)]
            elif isinstance(filter_value, list):  # Para mais de um valor (multiselect)
                if all(col in df.columns for col in ['Ano', 'Veículo', 'Contagem']):
                    df = df[df[column].isin(filter_value)]
                else:
                    df = df[df[column].isin(filter_value)]
            else:  # Para só um valor (selectbox)
                if all(col in df.columns for col in ['Ano', 'Veículo', 'Contagem']):
                    df = df[df[column] == filter_value]
                else:
                    df = df[df[column] == filter_value]    
    return df

with st.expander('Sobre'):
    st.markdown('''
            Dados de acidentes em Santos de 2015 a 2024. A partir de 2018 a quantidade de dados 
            anuais cai drasticamente, por isso o ano inicial padrão é 2018. 

            Muitos acidentes aconteceram no mesmo endereço/cruzamento, por isso os pontos ficam 
            sobrepostos no mapa. Recomendo usar (clicar) a legenda do próprio gráfico para ocultar 
            alguns pontos e ver quais estão acima de quais, ou usar o seletor do mapa.

            A ordem das ruas no cruzamento importa. Rua A x B vai mostrar resultados diferentes de 
            rua B x A.

            A legenda do mapa oculta os pontos apenas visualmente, ou seja, eles ainda aparecerão
            na tabela de dados. Para evitar isso, selecione a gravidade desejada no filtro de gravidade. 
            
            Os dias da semana estão representados em números, de 1, domingo até 7, sábado.
                ''')

# Filtros
with st.container():
    st.header('Filtros')
    
    min_date = df['data_hora'].min().date()
    max_date = df['data_hora'].max().date()

    linhaPeriodo = st.columns([1,1])
    # Filtro de data inicial
    start_date = linhaPeriodo[0].date_input(
        "Escolha a data inicial",
        format="DD/MM/YYYY",
        value=date(2018,1,1),
        min_value=min_date,
        max_value=max_date
    )

    # Filtro de data final
    end_date = linhaPeriodo[1].date_input(
        "Escolha a data final",
        format="DD/MM/YYYY",
        value=max_date,
        min_value=start_date,
        max_value=max_date
    )

    filters = []
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filters.append(((start_date, end_date), 'data_hora'))
    df = apply_filters(df, filters)
    dffrota = apply_filters(dffrota, filters)

    colGrav, colTipo, colTempo = st.columns(3)

    with colGrav:
        selected_gravidade = st.multiselect(
            label='Gravidade(s)',
            options=df['gravidade'].unique(),
            placeholder='Escolha a(s) gravidade(s)'
        )
        filters.append((selected_gravidade, 'gravidade'))
        df = apply_filters(df, filters)

    with colTipo:
        selected_tipo = st.multiselect(
            label='Tipo(s) de acidente',
            options=df['tipo_acidente'].unique(),
            placeholder='Escolha o(s) tipo(s) de acidente'
        )
        filters.append((selected_tipo, 'tipo_acidente'))
        df = apply_filters(df, filters)

    with colTempo:
        selected_tempo = st.multiselect(
            label='Condições Climáticas',
            options=df['tempo'].unique(),
            placeholder='Escolha o(s) tempo(s)'
        )
        filters.append((selected_tempo, 'tempo'))
        df = apply_filters(df, filters)

    linha2 = st.columns([2,1,2])

    selected_logras = linha2[0].multiselect(
        label='Logradouro',
        options=df['logradouro'].unique(),
        placeholder='Escolha o(s) Logradouro(s)'
        )
    filters.append((selected_logras, 'logradouro'))
    df = apply_filters(df, filters)

    selected_nums = linha2[1].multiselect(
        label='Número',
        options=df['numero'].unique(),
        placeholder='Escolha um nº'
    )
    filters.append((selected_nums, 'numero'))
    df = apply_filters(df, filters)

    selected_cruz = linha2[2].multiselect(
            label='Cruzamento',
            options=df['cruzamento'].unique(),
            placeholder = 'Escolha o(s) cruzamento(s)'
            )
    filters.append((selected_cruz, 'cruzamento'))
    df = apply_filters(df, filters)

gravidade_colors = {
    'C/ VÍTIMAS LEVES': 'green',
    'C/ VÍTIMAS GRAVES': 'orange',
    'C/ VÍTIMAS FATAIS': 'red',
    'S/ LESÃO': 'blue'
}

config = {'displayModeBar': True}
fig = go.Figure()

gravidades = df['gravidade'].unique()
for gravidade in gravidades:
    df_gravidades = df[df['gravidade'] == gravidade]
    
    hover_text = df_gravidades.apply(
        lambda row: f"Logradouro: {row['logradouro']}<br>Número: {row['numero']}<br>Cruzamento: {row['cruzamento']}",
        axis=1
    )

    fig.add_trace(go.Scattermapbox(
        lat=df_gravidades.lat,
        lon=df_gravidades.lon,
        mode='markers',
        marker=dict(
            size=8,
            opacity=0.7,
            color=gravidade_colors.get(gravidade, 'gray')
        ),
        name=f'{gravidade}',
        hovertext=hover_text, 
        hoverinfo='text' 
    ))

fig.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=-23.959, lon=-46.342),
        zoom=12
    ),
    height=450,
    margin=dict(l=0, r=0, t=0, b=0),
    legend=dict(
        x=0.0,
        y=0.925,
        xanchor='left',
        yanchor='middle',
        font=dict(size=14),
        orientation='v' 
    ),
    showlegend=True
)

tabScatter, tabHeat, tabGraphs = st.tabs(['Mapa de Pontos', 'Mapa de Calor','Gráficos'])

# Visualização
with tabScatter:
    colMap, colDF = st.columns(2)
    with colMap:
        st.write('Mapa de Acidentes por Gravidade')
        selected_points = st.plotly_chart(fig, use_container_width=True,
                        on_select='rerun',
                        selection_mode=['box','lasso'])

    if selected_points:
        selected_coords = [(p['lon'], p['lat']) for p in selected_points.get('selection', {}).get('points', [])]
        
        if selected_coords:
            df_filtered = df[df[['lon', 'lat']].apply(tuple, axis=1).isin(selected_coords)]
        else:
            df_filtered = pd.DataFrame() 
    else:
        df_filtered = df

    with colDF:
        st.write("Dados")
        st.dataframe(df_filtered, hide_index=True,
                        column_order=['data_hora','dia_semana','logradouro','numero',
                                    'cruzamento','tipo_acidente','gravidade','tempo'])
        if df_filtered.empty:
            st.write('Contagem: ', df.shape[0])
        else:
            st.write('Contagem: ', df_filtered.shape[0])

with tabHeat: 
    chart = st.pydeck_chart(
        pdk.Deck(
            map_style='light',
            initial_view_state=pdk.ViewState(
                latitude=-23.959,
                longitude=-46.342,
                zoom=11,
                pitch=50
            ),
            layers=[
                pdk.Layer(
                    "HexagonLayer",
                    data=df,
                    get_position="[lon, lat]",
                    radius=70,
                    elevation_scale=2,
                    auto_highlight=True,
                    elevation_range=[0, 1000],
                    upperPercentile=99,
                    #lowerPercentile=1,
                    pickable=True,
                    extruded=True,
                    material=True
                )
            ],
        )
    )

with tabGraphs:
    
    linha1 = st.columns([1]) 
    linha2 = st.columns([1])

    dflogs = df['logradouro'].value_counts().head(10).reset_index()
    dflogs.columns = ['Logradouro', 'Contagem']
    dflogs = dflogs.sort_values(by='Contagem', ascending=False)

    figlog = px.bar(dflogs, x='Contagem', y='Logradouro', orientation='h',
            title="Logradouros com Mais Acidentes")

    figlog.update_layout(
        xaxis_title="Contagem de Acidentes",
        yaxis_title="Logradouro",
        yaxis_tickfont=dict(size=10)) 
    graphLog = linha1[0].plotly_chart(figlog)

    df_crossings = df.dropna(subset=['cruzamento'])

    df_crossings['logradouro_cruzamento'] = df_crossings['logradouro'] + ' x ' + df_crossings['cruzamento']
    df_top_crossings = df_crossings['logradouro_cruzamento'].value_counts().head(10).reset_index()
    df_top_crossings.columns = ['Cruzamento', 'Contagem']

    figcruz = px.bar(df_top_crossings, x='Contagem', y='Cruzamento', 
                orientation='h',
                title="Cruzamentos com Mais Acidentes")

    figcruz.update_layout(
        xaxis_title="Contagem de Acidentes",
        yaxis_title="Cruzamento",
        yaxis_tickfont=dict(size=10) 
    )

    linha2[0].plotly_chart(figcruz)

    linhaPizza = st.columns([2,2,3])

    gravidade_counts = df['gravidade'].value_counts().reset_index()
    gravidade_counts.columns = ['Gravidade', 'Contagem']

    figgrav = px.pie(gravidade_counts,names='Gravidade',values='Contagem', title='Distribuição de Gravidade')

    linhaPizza[0].plotly_chart(figgrav)

    tipo_counts = df['tipo_acidente'].value_counts().reset_index()
    tipo_counts.columns = ['Tipo', 'Contagem']
    figtipo = px.pie(tipo_counts,names='Tipo',values='Contagem', title='Tipos de Acidente')

    linhaPizza[2].plotly_chart(figtipo)

    tempo_counts = df['tempo'].value_counts().reset_index()
    tempo_counts.columns = ['Tempo', 'Contagem']
    figtempo = px.pie(tempo_counts,names='Tempo',values='Contagem', title='Condições Climáticas')

    linhaPizza[1].plotly_chart(figtempo)

    df['hora'] = pd.to_datetime(df['data_hora']).dt.floor('30min').dt.time
    hora_counts = df['hora'].value_counts().reset_index()
    hora_counts.columns = ['Horário', 'Contagem']
    hora_counts = hora_counts.sort_values(by='Horário')
    hora_counts['Horário'] = hora_counts['Horário'].astype(str)

    histogram_fig = px.histogram(hora_counts,
                                 x='Horário',
                                 y='Contagem',
                                 title='Histograma de Contagem de Acidentes por Horário',
                                 nbins=24
                                )

    histogram_fig.update_layout(
        xaxis_title='Horário',
        yaxis_title='Contagem',
        xaxis_tickangle=-45,
        showlegend=True
    )
    st.plotly_chart(histogram_fig, use_container_width=True)
    
    linha3 = st.columns([1])
    df['Dia'] = df['dia_semana']
    count_semana = df.groupby('Dia').size().reset_index(name='Contagem')
    all_months = pd.DataFrame({'Dia': range(1, 8)})
    count_semana = all_months.merge(count_semana, on='Dia', how='left').fillna(0)
    figSemana = px.bar(
        count_semana, 
        x='Dia', 
        y='Contagem', 
        title="Contagem de Acidentes por Dia da Semana")
    figSemana.update_layout(
        xaxis_title="Dia da Semana", 
        yaxis_title="Contagem",
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 8)),
            ticktext=[
                'Domingo', 'Segunda', 'Terça', 'Quarta', 
                'Quinta', 'Sexta', 'Sábado'
                ]
            ))
    linha3[0].plotly_chart(figSemana)

    linha4 = st.columns([1])
    df['data_hora'] = pd.to_datetime(df['data_hora'])
    df['Mês'] = df['data_hora'].dt.month
    count_month = df.groupby('Mês').size().reset_index(name='Contagem')
    all_months = pd.DataFrame({'Mês': range(1, 13)})
    count_month = all_months.merge(count_month, on='Mês', how='left').fillna(0)
    figMonth = px.bar(
        count_month, 
        x='Mês', 
        y='Contagem', 
        title="Contagem de Acidentes por Mês")
    figMonth.update_layout(
        xaxis_title="Mês", 
        yaxis_title="Contagem",
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=[
                'Janeiro', 'Fevereiro', 'Março', 'Abril', 
                'Maio', 'Junho', 'Julho', 'Agosto', 
                'Setembro', 'Outubro', 'Novembro', 'Dezembro'
                ]
            )
    )
    linha4[0].plotly_chart(figMonth)

    linha5 = st.columns([1,1])
    df['dia'] = pd.to_datetime(df['data_hora']).dt.date

    monthly_counts = df.groupby(pd.Grouper(key='data_hora', freq='ME')).size().reset_index(name='Contagem')
    monthly_counts['Mês'] = monthly_counts['data_hora'].astype(str)

    area_fig = px.area(monthly_counts,
                    x='Mês',
                    y='Contagem',
                    title='Contagem de Acidentes ao longo dos meses')

    area_fig.update_layout(
        xaxis_title='Data',
        yaxis_title='Contagem',
        showlegend=True
    )

    linha5[0].plotly_chart(area_fig, use_container_width=True)

    df['Semana'] = df['data_hora'].dt.to_period('W').apply(lambda r: r.start_time)
    weekly_counts = df.groupby('Semana').size().reset_index(name='Contagem')

    area_fig = px.area(weekly_counts,
                    x='Semana',
                    y='Contagem',
                    title='Contagem de Acidentes por Semana')

    area_fig.update_layout(
        xaxis_title='Semana',
        yaxis_title='Contagem',
        showlegend=True
    )

    linha5[1].plotly_chart(area_fig, use_container_width=True)

    linha6 = st.columns([1,1])

    filters_frota = []

    selected_veiculos = st.multiselect(
            label='Tipo(s) de Veículo',
            options=dffrota['Veículo'].unique(),
            placeholder='Escolha o(s) tipo(s) de veículo',
            default=dffrota['Veículo'].unique()
        )
    filters_frota.append((selected_veiculos, 'Veículo'))
    dffrota = apply_filters(dffrota, filters_frota)

    linha7 = st.columns([1,2])

    dffrota_counts = pd.DataFrame()
    dffrota_counts = dffrota.groupby('Veículo')['Contagem'].sum().reset_index()
    figfrota = px.pie(dffrota_counts,names='Veículo',values='Contagem', title='Tipos de Veículos na cidade')
    linha7[0].plotly_chart(figfrota, use_container_width=True)

    if selected_veiculos:
        dffrota_anos = dffrota[dffrota['Veículo'].isin(selected_veiculos)]
        dffrota_anos = dffrota_anos.groupby(['Ano', 'Veículo'])['Contagem'].sum().reset_index()

        figfrota_anos = px.line(dffrota_anos,
                        x='Ano',
                        y='Contagem',
                        color='Veículo',
                        title='Contagem de Veículos por Ano')
        figfrota_anos.update_layout(showlegend=True)

        linha7[1].plotly_chart(figfrota_anos, use_container_width=True)
    else:
        dffrota_anos = dffrota.groupby('Ano')['Contagem'].sum().reset_index()

        figfrota_anos = px.line(dffrota_anos,
                        x='Ano',
                        y='Contagem',
                        title='Contagem de Veículos por Ano (Total)')
        figfrota_anos.update_layout(showlegend=True)

        linha7[1].plotly_chart(figfrota_anos, use_container_width=True)