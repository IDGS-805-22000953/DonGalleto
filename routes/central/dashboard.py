from flask import Blueprint, render_template
from sqlalchemy import func
from models import db
from models.models import PresentacionGalleta, Galleta, DetallePedido, Venta


dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    # Ventas Diarias (Promedio)
    total_galletas = (
        db.session.query(func.sum(DetallePedido.cantidad))
        .scalar()
    )
    total_dias = (
        db.session.query(func.count(func.distinct(func.date(Venta.fechaVenta))))
        .scalar()
    )
    promedio_diario = round(total_galletas / total_dias, 2) if total_dias else 0

    # Productos Más Vendidos
    productos = (
        db.session.query(Galleta.nombre, func.sum(DetallePedido.cantidad))
        .join(PresentacionGalleta, PresentacionGalleta.id == DetallePedido.idPresentacion)
        .join(Galleta, Galleta.id == PresentacionGalleta.idGalleta)
        .group_by(Galleta.nombre)
        .order_by(func.sum(DetallePedido.cantidad).desc())
        .limit(3)
        .all()
    )
    productos_mas_vendidos = [p[0] for p in productos]

    #Presentaciones Más Vendidas
    presentaciones = (
        db.session.query(PresentacionGalleta.tipoPresentacion, func.sum(DetallePedido.cantidad))
        .join(DetallePedido, PresentacionGalleta.id == DetallePedido.idPresentacion)
        .group_by(PresentacionGalleta.tipoPresentacion)
        .order_by(func.sum(DetallePedido.cantidad).desc())
        .first()
    )
    presentacion_mas_vendida = presentaciones[0] if presentaciones else "Ninguna"

    return render_template('dashboard.html', promedio_diario=promedio_diario, productos_mas_vendidos=productos_mas_vendidos, presentacion_mas_vendida=presentacion_mas_vendida)
