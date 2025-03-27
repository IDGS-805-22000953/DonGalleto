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
    CorteVentas,
    PresentacionGalleta
)


produccion_bp = Blueprint('produccion', __name__)

#PRODUCCION
# 🔹 Mostrar todas las galletas con sus presentaciones
@produccion_bp.route("/produccion")
def produccion():
    galletas = Galleta.query.all()
    presentaciones = {g.id: PresentacionGalleta.query.filter_by(idGalleta=g.id).all() for g in galletas}
    return render_template("Produccion/inicioProduccion.html", galletas=galletas, presentaciones=presentaciones)

# 🔹 Filtrar solo por piezas
@produccion_bp.route("/piezas")
def piezas():
    presentaciones = PresentacionGalleta.query.filter_by(tipoPresentacion="piezas").all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="piezas")

# 🔹 Filtrar solo por gramaje
@produccion_bp.route("/gramaje")
def gramaje():
    presentaciones = PresentacionGalleta.query.filter_by(tipoPresentacion="gramos").all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="gramaje")

# 🔹 Filtrar solo por paquete (1kg y 700g)
@produccion_bp.route("/paquete")
def paquete():
    presentaciones = PresentacionGalleta.query.filter(PresentacionGalleta.tipoPresentacion.in_(["1kg", "700g"])).all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="paquete")
