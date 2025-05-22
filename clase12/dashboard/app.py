
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.LUX],
    suppress_callback_exceptions=True
)

app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="E-commerce Dashboard",
        brand_href="/",
        color="primary",
        dark=True,
        children=[
            dbc.NavItem(dbc.NavLink("Resumen", href="/")),
            dbc.NavItem(dbc.NavLink("Clientes", href="/clientes")),
            dbc.NavItem(dbc.NavLink("Productos", href="/productos")),
            dbc.NavItem(dbc.NavLink("Forecast", href="/forecast")),
        ]
    ),
    html.Br(),
    dash.page_container
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True)
