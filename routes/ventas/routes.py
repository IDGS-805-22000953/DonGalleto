from flask import Blueprint,Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from datetime import datetime
from models.models import (
    db,
    Usuario,
    Cliente,
    Insumo,
    Proveedor,
    InsumosProveedor,
    PagoProveedor,
    Receta,
    RecetaInsumos,
    Galleta,
    Produccion,
    Pedido,
    DetallePedido,
    Venta,
    Merma,
    CorteVentas
)



ventas_bp = Blueprint('ventas', __name__)

# prueba ventas

@ventas_bp.route('/ventas')
def ventas():
    # Obtener todas las galletas con sus presentaciones
    galletas = Galleta.query.options(db.joinedload(Galleta.presentaciones)).all()
    
    # Procesar los datos para la vista
    galletas_data = []
    for galleta in galletas:
        presentaciones = ", ".join([f"{p.cantidad} {p.tipoPresentacion}" 
                                  for p in galleta.presentaciones])
        galletas_data.append({
            'id': galleta.id,
            'nombre': galleta.nombre,
            'descripcion': galleta.descripcion,
            'precio': galleta.precio,
            'stock': galleta.stock,
            'presentaciones': presentaciones,
            'rutaFoto': galleta.rutaFoto
        })
    
    return render_template('Ventas/ventas2.html', galletas=galletas_data)

