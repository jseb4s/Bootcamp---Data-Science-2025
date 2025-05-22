import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from prophet import Prophet
import pandas as pd
import plotly.graph_objects as go

dash.register_page(__name__, path="/forecast")

# Cargar datos
ventas = pd.read_csv('data/ventas.csv', parse_dates=['fecha'])
ventas['total_venta'] = ventas['cantidad'] * ventas['precio_unitario']

# Preprocesamiento
df_forecast = ventas.groupby('fecha').sum().reset_index()[['fecha', 'total_venta']]
df_forecast = df_forecast.rename(columns={'fecha': 'ds', 'total_venta': 'y'})

# Modelo Prophet
model = Prophet()
model.fit(df_forecast)

# Predicción
future = model.make_future_dataframe(periods=7)
forecast = model.predict(future)

# Separar real y forecast
ultima_fecha_real = df_forecast['ds'].max()
forecast_real = forecast[forecast['ds'] <= ultima_fecha_real]  # Históricos (de Prophet)
forecast_futuro = forecast[forecast['ds'] > ultima_fecha_real]  # Predicciones

# Layout
layout = dbc.Container([
    html.H2("Predicción de Ventas (Forecast)", className="text-center text-success mb-4"),

    dbc.Row([
        dbc.Col([
            dcc.DatePickerRange(
                id='rango-fechas-forecast',
                min_date_allowed=future['ds'].min(),
                max_date_allowed=future['ds'].max(),
                start_date=df_forecast['ds'].min(),
                end_date=future['ds'].max(),
                display_format='YYYY-MM-DD',
            )
        ], width=6),
    ], justify="center"),

    html.Br(),

    dcc.Graph(id="grafico-forecast")
], fluid=True)


@dash.callback(
    Output('grafico-forecast', 'figure'),
    Input('rango-fechas-forecast', 'start_date'),
    Input('rango-fechas-forecast', 'end_date')
)
def actualizar_forecast(start_date, end_date):
    # Filtrar
    reales_filtrado = df_forecast[(df_forecast['ds'] >= start_date) & (df_forecast['ds'] <= end_date)]
    forecast_real_filtrado = forecast_real[(forecast_real['ds'] >= start_date) & (forecast_real['ds'] <= end_date)]
    forecast_futuro_filtrado = forecast_futuro[(forecast_futuro['ds'] >= start_date) & (forecast_futuro['ds'] <= end_date)]

    # Gráfico
    fig = go.Figure()

    # Ventas reales (línea azul)
    fig.add_trace(go.Scatter(
        x=reales_filtrado['ds'],
        y=reales_filtrado['y'],
        mode='lines',
        name='Ventas Reales',
        line=dict(color='royalblue')
    ))

    # Pronóstico histórico (línea punteada gris, opcional)
    # fig.add_trace(go.Scatter(
    #     x=forecast_real_filtrado['ds'],
    #     y=forecast_real_filtrado['yhat'],
    #     mode='lines',
    #     name='Predicción pasada (modelo)',
    #     line=dict(color='lightgrey', dash='dot')
    # ))

    # Forecast futuro (línea roja)
    fig.add_trace(go.Scatter(
        x=forecast_futuro_filtrado['ds'],
        y=forecast_futuro_filtrado['yhat'],
        mode='lines',
        name='Pronóstico Futuro',
        line=dict(color='firebrick')
    ))

    fig.update_layout(
        title="Ventas Históricas + Pronóstico de Ventas",
        xaxis_title="Fecha",
        yaxis_title="Ventas",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=20, r=20, t=50, b=50),
    )

    return fig
