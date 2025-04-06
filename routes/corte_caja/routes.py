from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from models.models import CorteCaja, VentaLocal, PedidosCliente, PagoProveedor, Merma, db
from flask_login import login_required
from datetime import datetime, date
from sqlalchemy import extract
from decimal import Decimal

corte_bp = Blueprint('corte', __name__)

@corte_bp.route('/cortes')
# @login_required
def listar_cortes():
    cortes = CorteCaja.query.order_by(CorteCaja.fecha_creacion.desc()).all()
    return render_template('Corte_caja/corte_caja.html', cortes=cortes, date=date, datetime=datetime)

@corte_bp.route('/cortes/calcular', methods=['POST'])
# @login_required
def calcular_corte():
    fecha_str = request.form.get('mes')
    if not fecha_str:
        return jsonify({'error': 'Fecha no proporcionada'}), 400
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        año = fecha.year
        mes_num = fecha.month
        mes_formateado = f"{año}-{mes_num:02d}"
        
        # Calcular ingresos locales
        ingresos_local = sum([v.total for v in VentaLocal.query.filter(
            extract('year', VentaLocal.fechaCompra) == año,
            extract('month', VentaLocal.fechaCompra) == mes_num
        )]) or 0
        
        # Calcular ingresos por pedidos
        ingresos_pedidos = sum([p.total for p in PedidosCliente.query.filter(
            extract('year', PedidosCliente.fechaPedido) == año,
            extract('month', PedidosCliente.fechaPedido) == mes_num
        )]) or 0
        
        # Calcular egresos
        egresos = sum([p.monto for p in PagoProveedor.query.filter(
            extract('year', PagoProveedor.fechaPago) == año,
            extract('month', PagoProveedor.fechaPago) == mes_num
        )]) or 0
        
        # Calcular mermas
        mermas = sum([m.cantidad for m in Merma.query.filter(
            extract('year', Merma.fechaRegistro) == año,
            extract('month', Merma.fechaRegistro) == mes_num
        )]) or 0
        
        ingreso_total = Decimal(ingresos_local) + Decimal(ingresos_pedidos)
        egresos_total = Decimal(egresos)
        monto_mermas = Decimal(mermas)
        utilidad = ingreso_total - egresos_total - monto_mermas
        
        return jsonify({
            'ingresos': float(ingreso_total),
            'egresos': float(egresos_total),
            'mermas': float(monto_mermas),
            'utilidad': float(utilidad)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@corte_bp.route('/cortes/nuevo', methods=['POST'])
# @login_required
def nuevo_corte():
    fecha_str = request.form.get('mes')
    caja_reportada = request.form.get('caja_reportada')

    if not fecha_str or not caja_reportada:
        flash('Todos los campos son requeridos', 'corte_error')
        return redirect(url_for('corte.listar_cortes'))

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        año = fecha.year
        mes_num = fecha.month
        mes_formateado = f"{año}-{mes_num:02d}"

        if CorteCaja.query.filter_by(mes=mes_formateado).first():
            flash('Ya se ha realizado el corte de este mes.', 'corte_advertencia')
            return redirect(url_for('corte.listar_cortes'))

        # Los cálculos se hacen igual que en la función calcular_corte
        ingresos_local = sum([v.total for v in VentaLocal.query.filter(
            extract('year', VentaLocal.fechaCompra) == año,
            extract('month', VentaLocal.fechaCompra) == mes_num
        )]) or 0
        
        ingresos_pedidos = sum([p.total for p in PedidosCliente.query.filter(
            extract('year', PedidosCliente.fechaPedido) == año,
            extract('month', PedidosCliente.fechaPedido) == mes_num
        )]) or 0
        
        egresos = sum([p.monto for p in PagoProveedor.query.filter(
            extract('year', PagoProveedor.fechaPago) == año,
            extract('month', PagoProveedor.fechaPago) == mes_num
        )]) or 0
        
        mermas = sum([m.cantidad for m in Merma.query.filter(
            extract('year', Merma.fechaRegistro) == año,
            extract('month', Merma.fechaRegistro) == mes_num
        )]) or 0
        
        ingreso_total = Decimal(ingresos_local) + Decimal(ingresos_pedidos)
        egresos_total = Decimal(egresos)
        monto_mermas = Decimal(mermas)
        utilidad = ingreso_total - egresos_total - monto_mermas

        nuevo_corte = CorteCaja(
            mes=mes_formateado,
            ingreso_total=ingreso_total,
            egresos_total=egresos_total,
            monto_mermas=monto_mermas,
            caja_reportada=Decimal(caja_reportada),
            utilidad=utilidad,
            fecha_creacion=datetime.now()
        )

        db.session.add(nuevo_corte)
        db.session.commit()
        flash('Corte de caja registrado exitosamente.', 'corte_success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar el corte: {str(e)}', 'corte_error')

    return redirect(url_for('corte.listar_cortes'))