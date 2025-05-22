import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# Configuración inicial
TICKERS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "BRK-B", "META", "TSLA", "UNH", "LLY",
    "JPM", "V", "XOM", "PG", "MA", "AVGO", "CVX", "JNJ", "HD", "MRK"
]
START_DATE = "2020-01-01"
END_DATE = pd.to_datetime("today").strftime("%Y-%m-%d")

# Funciones auxiliares
def human_format(num):
    if num is None or num == 'N/A':
        return "N/A"
    num = float(num)
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    suffixes = ['', 'K', 'M', 'B', 'T']
    return f'{num:.2f}{suffixes[magnitude]}'


def download_data(tickers, start, end):
    return yf.download(tickers, start=start, end=end, group_by='ticker')

def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_indicators(df):
    df['RSI'] = compute_rsi(df['Close'])
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Upper_BB'] = df['Close'].rolling(window=20).mean() + 2*df['Close'].rolling(window=20).std()
    df['Lower_BB'] = df['Close'].rolling(window=20).mean() - 2*df['Close'].rolling(window=20).std()
    return df



def fundamental_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    pe = info.get('trailingPE', 'N/A')
    eps = info.get('trailingEps', 'N/A')
    market_cap = info.get('marketCap', 'N/A')
    dividend_yield = info.get('dividendYield', 'N/A')
    beta = info.get('beta', 'N/A')
    return pe, eps, market_cap, dividend_yield, beta

def backtest_strategy(df, initial_capital=10000):
    capital = initial_capital
    position = 0
    capital_over_time = []
    for fecha, row in df.iterrows():
        if row['RSI'] < 30 and position == 0:
            position = capital / row['Close']
            capital = 0
        elif row['RSI'] > 70 and position > 0:
            capital = position * row['Close']
            position = 0
        total_capital = capital + (position * row['Close'])
        capital_over_time.append(total_capital)
    return capital_over_time

# Descargar datos
data = download_data(TICKERS, START_DATE, END_DATE)

# Crear app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Layout
app.layout = dbc.Container([
    html.H1("🚀 Dashboard Financiero Avanzado S&P500 + Backtesting", className="text-center mb-4"),
    
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='ticker-dropdown',
                         options=[{'label': ticker, 'value': ticker} for ticker in TICKERS],
                         value=["AAPL"],
                         multi=True,
                         style={'color':'black'}),
        ], width=8),
        dbc.Col([
            dcc.DatePickerRange(
                id='date-picker',
                start_date=START_DATE,
                end_date=END_DATE,
                display_format='YYYY-MM-DD'
            )
        ], width=4),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(id="kpi-precio", className="text-center p-3 bg-dark text-white")),
        dbc.Col(dbc.Card(id="kpi-cambio", className="text-center p-3 bg-dark text-white")),
        dbc.Col(dbc.Card(id="kpi-max", className="text-center p-3 bg-dark text-white")),
        dbc.Col(dbc.Card(id="kpi-min", className="text-center p-3 bg-dark text-white")),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(id="kpi-pe", className="text-center p-3 bg-secondary text-white")),
        dbc.Col(dbc.Card(id="kpi-eps", className="text-center p-3 bg-secondary text-white")),
        dbc.Col(dbc.Card(id="kpi-mcap", className="text-center p-3 bg-secondary text-white")),
        dbc.Col(dbc.Card(id="kpi-div", className="text-center p-3 bg-secondary text-white")),
        dbc.Col(dbc.Card(id="kpi-beta", className="text-center p-3 bg-secondary text-white")),
    ], className="mb-4"),

    dcc.Loading([
        dcc.Graph(id='candlestick-chart'),
        dcc.Graph(id='rsi-chart'),
        dcc.Graph(id='macd-chart'),
        dcc.Graph(id='heatmap-chart'),

        html.Br(),
        dbc.Row([
            dbc.Col([
                html.Label("💵 Monto Inicial Backtesting ($)"),
                dcc.Input(id='input-monto', type='number', value=10000, step=1000, min=1000)
            ], width=4),
            dbc.Col([
                html.Label("📅 Fecha Inicio Backtesting"),
                dcc.DatePickerSingle(
                    id='input-fecha-backtest',
                    min_date_allowed=pd.to_datetime(START_DATE),
                    max_date_allowed=pd.to_datetime(END_DATE),
                    initial_visible_month=pd.to_datetime("2021-01-01"),
                    date="2021-01-01",
                    display_format='YYYY-MM-DD'
                )
            ], width=4),
        ], className="mb-4 text-center"),

        html.Div(id='backtest-config', style={'textAlign': 'center', 'marginBottom': '10px'}),
        dcc.Graph(id='backtest-chart')
    ])
], fluid=True)

# Callback principal
@app.callback(
    Output('kpi-precio', 'children'),
    Output('kpi-cambio', 'children'),
    Output('kpi-max', 'children'),
    Output('kpi-min', 'children'),
    Output('kpi-pe', 'children'),
    Output('kpi-eps', 'children'),
    Output('kpi-mcap', 'children'),
    Output('kpi-div', 'children'),
    Output('kpi-beta', 'children'),
    Output('candlestick-chart', 'figure'),
    Output('rsi-chart', 'figure'),
    Output('macd-chart', 'figure'),
    Output('heatmap-chart', 'figure'),
    Output('backtest-config', 'children'),
    Output('backtest-chart', 'figure'),
    Input('ticker-dropdown', 'value'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date'),
    Input('input-monto', 'value'),
    Input('input-fecha-backtest', 'date')
)

def update_dashboard(tickers, start_date, end_date, initial_capital, backtest_start):
    if isinstance(tickers, str):
        tickers = [tickers]

    fig_candle = go.Figure()
    fig_rsi = go.Figure()
    fig_macd = go.Figure()
    fig_backtest = go.Figure()
    price_changes = {}

    first_ticker = tickers[0]
    pe, eps, mcap, div, beta = fundamental_data(first_ticker)

    for ticker in tickers:
        df = data[ticker].loc[start_date:end_date].copy()
        df = compute_indicators(df)

        precio_actual = df['Close'].iloc[-1]
        cambio = (df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
        max_anual = df['Close'].max()
        min_anual = df['Close'].min()

        # Candlestick Chart
        fig_candle.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=ticker
        ))
        fig_candle.add_trace(go.Scatter(x=df.index, y=df['Upper_BB'], line=dict(color='lightblue'), name=f'Upper BB {ticker}'))
        fig_candle.add_trace(go.Scatter(x=df.index, y=df['Lower_BB'], line=dict(color='lightblue'), name=f'Lower BB {ticker}'))
        fig_candle.add_trace(go.Bar(x=df.index, y=df['Volume'], name=f'Volume {ticker}', yaxis="y2", opacity=0.3))

        # RSI Chart
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name=f'RSI {ticker}'))
        buy_signals = df[df['RSI'] < 30]
        sell_signals = df[df['RSI'] > 70]
        fig_rsi.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['RSI'], mode='markers', marker=dict(color='green', size=8), name=f'Buy Signal {ticker}'))
        fig_rsi.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['RSI'], mode='markers', marker=dict(color='red', size=8), name=f'Sell Signal {ticker}'))

        # MACD Chart
        fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD'] - df['Signal_Line'], name=f'MACD Hist {ticker}'))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name=f'MACD Line {ticker}'))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name=f'Signal Line {ticker}'))

        # Backtesting
        df_backtest = df[df.index >= backtest_start]
        capital_history = backtest_strategy(df_backtest, initial_capital=initial_capital)
        fig_backtest.add_trace(go.Scatter(x=df_backtest.index, y=capital_history, name=f'Capital {ticker}'))

        # Calcular % ganancia o pérdida
        capital_final = capital_history[-1]
        rendimiento_pct = ((capital_final - initial_capital) / initial_capital) * 100
        rendimiento_text = f"Resultado: {'+' if rendimiento_pct >= 0 else ''}{rendimiento_pct:.2f}% {'' if rendimiento_pct >= 0 else ''} ({capital_final:,.2f} USD)"


        # Heatmap
        df_weekly = df['Close'].resample('W').last()
        price_changes[ticker] = df_weekly.pct_change().dropna() * 100

    fig_candle.update_layout(title='Velas, Volumen y Bandas de Bollinger', template="plotly_dark", yaxis2=dict(overlaying='y', side='right'))
    fig_rsi.update_layout(title='RSI', yaxis=dict(range=[0, 100]), template="plotly_dark")
    fig_macd.update_layout(title='MACD', template="plotly_dark")
    fig_backtest.update_layout(title='Backtesting Capital (RSI Strategy)', template="plotly_dark", yaxis_title="Capital ($)")

    heatmap_df = pd.DataFrame(price_changes)
    fig_heatmap = px.imshow(heatmap_df.T, aspect="auto", color_continuous_scale='RdBu', origin='lower')
    fig_heatmap.update_layout(title='Heatmap Variación Semanal (%)', template="plotly_dark", height=400)

    return (
        html.H5(f'Precio Actual: ${precio_actual:.2f}'),
        html.H5(f'Cambio Diario: {cambio:.2f}%'),
        html.H5(f'Máximo Anual: ${max_anual:.2f}'),
        html.H5(f'Mínimo Anual: ${min_anual:.2f}'),
        html.H5(f'P/E Ratio: {pe}'),
        html.H5(f'EPS: {eps}'),
        html.H5(f'Market Cap: {human_format(mcap)}'),
        html.H5(f'Dividend Yield: {div}'),
        html.H5(f'Beta: {beta}'),
        fig_candle,
        fig_rsi,
        fig_macd,
        fig_heatmap,
        html.Div([
            html.H5(f"Backtesting iniciado el {pd.to_datetime(backtest_start).strftime('%Y-%m-%d')} con ${initial_capital:,.0f} USD"),
            html.H5(rendimiento_text)
        ]),
        fig_backtest
    )

# Correr la app
if __name__ == '__main__':
    app.run(debug=True)