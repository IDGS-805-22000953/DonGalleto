from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .models import db, Usuario, Cliente, Insumo, Proveedor, InsumosProveedor, PagoProveedor, Receta, RecetaInsumos, Galleta, Produccion, Pedido, DetallePedido, Venta, Merma, CorteVentas
