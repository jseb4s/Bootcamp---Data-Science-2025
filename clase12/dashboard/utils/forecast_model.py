from prophet import Prophet
import pandas as pd

def generar_forecast(ventas):
    """
    Genera el forecast de ventas usando el modelo Prophet.
    """
    # Preprocesar los datos para Prophet
    df_forecast = ventas.groupby('fecha').sum().reset_index()[['fecha', 'total_venta']]
    df_forecast = df_forecast.rename(columns={'fecha': 'ds', 'total_venta': 'y'})

    # Crear y entrenar el modelo
    model = Prophet()
    model.fit(df_forecast)

    # Generar las predicciones
    future = model.make_future_dataframe(df_forecast, periods=180)  # Predicción 180 días en el futuro
    forecast = model.predict(future)

    return forecast