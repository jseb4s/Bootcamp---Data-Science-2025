import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

dash.register_page(__name__, path="/")

# Cargar datos
ventas = pd.read_csv('data/ventas.csv', parse_dates=['fecha'])
productos = pd.read_csv('data/productos.csv')
ventas['total_venta'] = ventas['cantidad'] * ventas['precio_unitario']

# Preprocesamiento rápido
ventas['total_venta'] = ventas['cantidad'] * ventas['precio_unitario']
ventas = ventas.merge(productos, on='id_producto', how='left')

layout = dbc.Container([
    html.H2("Resumen Ejecutivo de Ventas", className="text-center"),
    html.Br(),
    dbc.Row([
        dbc.Col(dcc.DatePickerRange(
            id="rango-fechas",
            min_date_allowed=ventas['fecha'].min(),
            max_date_allowed=ventas['fecha'].max(),
            start_date=ventas['fecha'].min(),
            end_date=ventas['fecha'].max()
        ), width=4),
    ], justify="center"),
    html.Br(),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Ventas Totales", className="card-title"),
                html.H3(id="ventas-totales", className="text-success")
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Órdenes Totales", className="card-title"),
                html.H3(id="ordenes-totales", className="text-info")
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5("Ticket Promedio", className="card-title"),
                html.H3(id="ticket-promedio", className="text-warning")
            ])
        ]), width=3),
    ], justify="center"),
    html.Br(),
    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-lineas-ventas"), width=8),
        dbc.Col(dcc.Graph(id="grafico-pie-categorias"), width=4),
    ])
], fluid=True)

@dash.callback(
    Output('ventas-totales', 'children'),
    Output('ordenes-totales', 'children'),
    Output('ticket-promedio', 'children'),
    Output('grafico-lineas-ventas', 'figure'),
    Output('grafico-pie-categorias', 'figure'),
    Input('rango-fechas', 'start_date'),
    Input('rango-fechas', 'end_date')
)
def actualizar_dashboard(start_date, end_date):
    df = ventas[(ventas['fecha'] >= start_date) & (ventas['fecha'] <= end_date)]

    ventas_total = f"${df['total_venta'].sum():,.0f}"
    ordenes_total = f"{df.shape[0]:,}"
    ticket_promedio = f"${df['total_venta'].mean():,.0f}" if not df.empty else "$0"

    fig_lineas = px.line(df.groupby('fecha')['total_venta'].sum().reset_index(),
                         x='fecha', y='total_venta',
                         title="Ventas por Día", markers=True)

    fig_pie = px.pie(df, names='categoría', values='total_venta',
                     title="Distribución por Categoría")

    return ventas_total, ordenes_total, ticket_promedio, fig_lineas, fig_pie