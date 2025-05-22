import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Registrar la página
dash.register_page(__name__, path="/clientes")

# Cargar datos
clientes = pd.read_csv('data/clientes.csv')
ventas = pd.read_csv('data/ventas.csv', parse_dates=['fecha'])

# Preprocesamiento inicial
ventas['total_venta'] = ventas['cantidad'] * ventas['precio_unitario']

layout = dbc.Container([
    html.H2("Análisis de Clientes", className="text-center text-primary mb-4"),

    dbc.Row([
        dbc.Col([
            dcc.DatePickerRange(
                id='rango-fechas',
                min_date_allowed=ventas['fecha'].min(),
                max_date_allowed=ventas['fecha'].max(),
                start_date=ventas['fecha'].min(),
                end_date=ventas['fecha'].max(),
                display_format='YYYY-MM-DD',
            )
        ], width=6),
    ], justify="center"),

    html.Br(),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-clientes-pie"), width=6),
        dbc.Col(dcc.Graph(id="grafico-clientes-barra"), width=6),
    ]),
], fluid=True)


# Callback
@dash.callback(
    Output('grafico-clientes-pie', 'figure'),
    Output('grafico-clientes-barra', 'figure'),
    Input('rango-fechas', 'start_date'),
    Input('rango-fechas', 'end_date')
)
def actualizar_clientes(start_date, end_date):
    # Filtrar ventas por fecha
    ventas_filtradas = ventas[(ventas['fecha'] >= start_date) & (ventas['fecha'] <= end_date)]
    
    # Recalcular ventas por cliente
    ventas_cliente = ventas_filtradas.groupby('id_cliente')['total_venta'].sum().reset_index()
    
    # Actualizar dataframe de clientes con ventas
    clientes_actualizados = clientes.merge(ventas_cliente, on='id_cliente', how='left')
    clientes_actualizados['total_venta'] = clientes_actualizados['total_venta'].fillna(0)

    # Pie chart: Ventas por país
    fig_pie = px.pie(
        clientes_actualizados,
        names='país',
        values='total_venta',
        title="Ventas por País",
        color_discrete_sequence=px.colors.sequential.RdBu
    )

    # Bar chart: Top 10 clientes por venta
    top_clientes = clientes_actualizados.sort_values('total_venta', ascending=False).head(10)

    fig_barra = px.bar(
        top_clientes,
        x='nombre',
        y='total_venta',
        title="Top 10 Clientes por Ventas",
        color='total_venta',
        color_continuous_scale='blues'
    )

    fig_barra.update_layout(xaxis_title="Cliente", yaxis_title="Total de Venta (USD)")

    return fig_pie, fig_barra