import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Registrar la página
dash.register_page(__name__, path="/productos")

# Cargar datos
productos = pd.read_csv('data/productos.csv')
ventas = pd.read_csv('data/ventas.csv', parse_dates=['fecha'])

# Preprocesamiento
ventas['total_venta'] = ventas['cantidad'] * ventas['precio_unitario']

layout = dbc.Container([
    html.H2("Análisis de Productos", className="text-center text-primary mb-4"),

    dbc.Row([
        dbc.Col([
            dcc.DatePickerRange(
                id='rango-fechas-productos',
                min_date_allowed=ventas['fecha'].min(),
                max_date_allowed=ventas['fecha'].max(),
                start_date=ventas['fecha'].min(),
                end_date=ventas['fecha'].max(),
                display_format='YYYY-MM-DD',
            )
        ], width=6),
        dbc.Col([
            dcc.Dropdown(
                id='filtro-producto',
                options=[{'label': nombre, 'value': nombre} for nombre in productos['nombre'].unique()],
                placeholder="Selecciona un producto (opcional)",
                multi=False,
                clearable=True
            )
        ], width=6),
    ], justify="center"),

    html.Br(),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-productos-pie"), width=6),
        dbc.Col(dcc.Graph(id="grafico-productos-barra"), width=6),
    ]),
], fluid=True)


# Callback
@dash.callback(
    Output('grafico-productos-pie', 'figure'),
    Output('grafico-productos-barra', 'figure'),
    Input('rango-fechas-productos', 'start_date'),
    Input('rango-fechas-productos', 'end_date'),
    Input('filtro-producto', 'value')
)
def actualizar_productos(start_date, end_date, producto_seleccionado):
    # Filtrar ventas por fecha
    ventas_filtradas = ventas[(ventas['fecha'] >= start_date) & (ventas['fecha'] <= end_date)]
    
    # Agregar nombre y categoría al dataframe de ventas
    ventas_completa = ventas_filtradas.merge(productos, on='id_producto', how='left')

    # Si se selecciona un producto, filtrar
    if producto_seleccionado:
        ventas_completa = ventas_completa[ventas_completa['nombre'] == producto_seleccionado]

    # Agrupar ventas por categoría y por producto
    ventas_categoria = ventas_completa.groupby('categoría')['total_venta'].sum().reset_index()
    ventas_nombre = ventas_completa.groupby('nombre')['total_venta'].sum().reset_index()

    # Pie chart: Ventas por categoría
    fig_pie = px.pie(
        ventas_categoria,
        names='categoría',
        values='total_venta',
        title="Distribución de Ventas por Categoría",
        color_discrete_sequence=px.colors.sequential.RdBu
    )

    # Bar chart: Top 10 productos
    top_productos = ventas_nombre.sort_values('total_venta', ascending=False).head(10)

    fig_barra = px.bar(
        top_productos,
        x='nombre',
        y='total_venta',
        title="Top 10 Productos más Vendidos",
        color='total_venta',
        color_continuous_scale='viridis'
    )

    fig_barra.update_layout(xaxis_title="Producto", yaxis_title="Total de Venta (USD)")

    return fig_pie, fig_barra