import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import geopandas as gpd
import plotly.graph_objs as go
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

df_sequia= pd.read_excel('data/Municipios_con_ sequia.xlsx', sheet_name=2)
columnas_fechas= list(df_sequia.columns[9:])
df_sequia= df_sequia[ ['CVE_CONCATENADA','CVE_ENT','CVE_MUN','NOMBRE_MUN','ENTIDAD'] + columnas_fechas]
df_sequia= df_sequia.melt(id_vars=['CVE_CONCATENADA','CVE_ENT','CVE_MUN','NOMBRE_MUN','ENTIDAD'], var_name='Fecha', value_name='Sequia')
df_sequia['Sequia']= df_sequia['Sequia'].replace({'D0': 0, 'D1': 1, 'D2': 2, 'D3': 3, 'D4': 4, 'D5': 5})
df_sequia['Sequia']= df_sequia['Sequia'].fillna(0)
df_sequia['Sequia']= df_sequia['Sequia'].astype(int)
df_sequia['Fecha']= pd.to_datetime(df_sequia['Fecha'], format='%Y-%m-%d')
df_sequia['mes']= df_sequia['Fecha'].dt.month
df_sequia['anio']= df_sequia['Fecha'].dt.year
df_sequia_estado= df_sequia.groupby(['CVE_ENT','ENTIDAD','anio', 'mes'])[['Sequia']].mean().reset_index()
df_sequia_estado['Fecha']= pd.to_datetime(df_sequia_estado['anio'].astype(str) + '-' + df_sequia_estado['mes'].astype(str) + '-1')

app.layout = dbc.Col([
    
    html.H1('Droughts Forecast', style={'text-align': 'center'}),
    
    dbc.Select(
        id='input-state',
        options=[{'label': estado, 'value': estado} for estado in df_sequia_estado['ENTIDAD'].unique()],
        placeholder='Selecciona un estado',
        style={'margin-top': '10px'}
    ),
    
    html.H3('Droughts Forecast', style={'text-align': 'center', 'margin-top': '30px'}),
    
    dcc.Loading( type='graph', children=[dcc.Graph(id='forecast-droughts')]),
    
    html.H3('Droughts components', style={'text-align': 'center', 'margin-top': '30px'}),
    
    dcc.Loading( type='graph', children=[dcc.Graph(id='components-droughts')])
    
], style={'margin': '30px'})


@app.callback(
    Output('forecast-droughts', 'figure'),
    [Input('input-state', 'value')]
)
def update_forecast_droughts(selected_state):
    df_sequia_estado_filtro= df_sequia_estado[df_sequia_estado['ENTIDAD']==selected_state]
    df_sequia_estado_filtro= df_sequia_estado_filtro.groupby(['Fecha'])[['Sequia']].mean().reset_index()
    df_sequia_estado_filtro.columns= ['ds', 'y']
    
    m = Prophet(changepoint_prior_scale=1,seasonality_mode='multiplicative', seasonality_prior_scale=10)
    m.fit(df_sequia_estado_filtro)
    
    future = m.make_future_dataframe(periods=24, freq='ME')
    forecast = m.predict(future)
    
    fig_final= go.Figure()
    
    fig= plot_plotly(m, forecast, changepoints=True)
    
    fig_final.add_traces(fig.data)
    
    fig_final.update_layout(
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
    ) 
    
    return fig_final

@app.callback(
    Output('components-droughts', 'figure'),
    [Input('input-state', 'value')]
)
def update_components_droughts(selected_state):
    df_sequia_estado_filtro= df_sequia_estado[df_sequia_estado['ENTIDAD']==selected_state]
    df_sequia_estado_filtro= df_sequia_estado_filtro.groupby(['Fecha'])[['Sequia']].mean().reset_index()
    df_sequia_estado_filtro.columns= ['ds', 'y']
    
    m = Prophet(changepoint_prior_scale=1,seasonality_mode='multiplicative', seasonality_prior_scale=10)
    m.fit(df_sequia_estado_filtro)
    
    future = m.make_future_dataframe(periods=24, freq='ME')
    forecast = m.predict(future)
    
    from plotly.subplots import make_subplots
    
    # Create subplots
    fig_final = make_subplots(rows=1, cols=2)
    
    fig = plot_components_plotly(m, forecast)
    
    # Add traces to subplots
    fig_final.add_trace(fig.data[0], row=1, col=1)
    fig_final.add_trace(fig.data[1], row=1, col=1)
    fig_final.add_trace(fig.data[2], row=1, col=1)
    fig_final.add_trace(fig.data[3], row=1, col=2)
    
    fig_final.update_layout(
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
    ) 
    
    return fig_final




if __name__ == '__main__':
    app.run_server()
