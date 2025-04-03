from flask import Blueprint, render_template
from models.models import db, VentaLocal, PedidosCliente, PresentacionGalleta, Galleta
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.sql import func
import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def mostrar_dashboard():
    # Fecha de hoy
    hoy = datetime.date.today()

    # Ventas diarias (VentaLocal y PedidosCliente completados)
    ventas_local = db.session.query(func.coalesce(func.sum(VentaLocal.total), 0)).filter(
        func.date(VentaLocal.fechaCompra) == hoy
    ).scalar()

    ventas_pedidos = db.session.query(func.coalesce(func.sum(PedidosCliente.total), 0)).filter(
        func.date(PedidosCliente.fechaRecogida) == hoy,
        PedidosCliente.estatus == 'completado'
    ).scalar()

    # Sumar ambas ventas
    ventas_totales = (ventas_local or 0) + (ventas_pedidos or 0)

    # Top 3 galletas del mes
    inicio_mes = hoy.replace(day=1)

    top_galletas = db.session.query(
        Galleta.nombre,
        func.coalesce(func.sum(VentaLocal.cantidadcomprado), 0) +
        func.coalesce(func.sum(PedidosCliente.cantidadcomprado), 0)
    ).join(PresentacionGalleta, PresentacionGalleta.id == VentaLocal.id_presentacion) \
     .join(Galleta, Galleta.id == PresentacionGalleta.idGalleta) \
     .outerjoin(PedidosCliente, PedidosCliente.id_presentacion == PresentacionGalleta.id) \
     .filter(
         func.date(VentaLocal.fechaCompra) >= inicio_mes
     ).filter(
         (PedidosCliente.id == None) | 
         ((func.date(PedidosCliente.fechaPedido) >= inicio_mes) & (PedidosCliente.estatus == 'completado'))
     ) \
     .group_by(Galleta.id, Galleta.nombre) \
     .order_by(func.coalesce(func.sum(VentaLocal.cantidadcomprado), 0) +
               func.coalesce(func.sum(PedidosCliente.cantidadcomprado), 0).desc()) \
     .limit(3).all()

    # Top presentaciones
    top_presentaciones = db.session.query(
        PresentacionGalleta.tipoPresentacion,
        func.coalesce(func.sum(VentaLocal.cantidadcomprado), 0) +
        func.coalesce(func.sum(PedidosCliente.cantidadcomprado), 0)
    ).join(VentaLocal, VentaLocal.id_presentacion == PresentacionGalleta.id) \
     .outerjoin(PedidosCliente, PedidosCliente.id_presentacion == PresentacionGalleta.id) \
     .filter(
         func.date(VentaLocal.fechaCompra) >= inicio_mes
     ).filter(
         (PedidosCliente.id == None) | 
         ((func.date(PedidosCliente.fechaPedido) >= inicio_mes) & (PedidosCliente.estatus == 'completado'))
     ) \
     .group_by(PresentacionGalleta.tipoPresentacion) \
     .order_by(func.coalesce(func.sum(VentaLocal.cantidadcomprado), 0) +
               func.coalesce(func.sum(PedidosCliente.cantidadcomprado), 0).desc()) \
     .all()

    return render_template('Central/dashboard.html',ventas_diarias=ventas_totales,fecha=hoy.strftime('%d/%m/%Y'),top_galletas=top_galletas,top_presentaciones=top_presentaciones
    )
