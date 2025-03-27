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


cocina_bp = Blueprint('cocina', __name__)


#COCINA
@cocina_bp.route("/cocina")
def cocina():
    return render_template("Cocina/cocina.html")


