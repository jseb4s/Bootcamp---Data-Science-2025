import pandas as pd

def cargar_datos_ventas(filepath):
    """
    Carga los datos de ventas desde un archivo CSV.
    """
    ventas = pd.read_csv(filepath, parse_dates=['fecha'])
    ventas['total_venta'] = ventas['cantidad'] * ventas['precio_unitario']
    return ventas

def preprocesar_clientes(ventas, clientes):
    """
    Une los datos de ventas con los datos de clientes y agrega el total de ventas por cliente.
    """
    ventas_cliente = ventas.groupby('id_cliente')['total_venta'].sum().reset_index()
    clientes = clientes.merge(ventas_cliente, on='id_cliente', how='left')
    return clientes

def preprocesar_productos(ventas, productos):
    """
    Une los datos de ventas con los productos y agrega el total de ventas por producto.
    """
    ventas_producto = ventas.groupby('id_producto')['total_venta'].sum().reset_index()
    productos = productos.merge(ventas_producto, on='id_producto', how='left')
    return productos