from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from models.models import (
    db, Galleta, PresentacionGalleta, VentaLocal
)
from forms import AgregarAlCarritoForm

ventas_bp = Blueprint('ventas', __name__)

@ventas_bp.route('/ventas', methods=['GET', 'POST'])
def ventas():
    galletas = Galleta.query.options(db.joinedload(Galleta.presentaciones)).all()
    form = AgregarAlCarritoForm()
    
    if 'carrito' not in session:
        session['carrito'] = []
        session['carrito_subtotal'] = 0
        session['carrito_iva'] = 0
        session['carrito_total'] = 0
    
    return render_template('Ventas/ventas2.html', galletas=galletas, form=form)

@ventas_bp.route('/agregar_al_carrito', methods=['POST'])
def agregar_al_carrito():
    form = AgregarAlCarritoForm()
    if form.validate_on_submit():
        galleta_id = form.galleta_id.data
        presentacion_id = form.presentacion_id.data
        cantidad = form.cantidad.data
        
        presentacion = PresentacionGalleta.query.get(presentacion_id)
        if not presentacion:
            flash('Presentación no válida', 'error')
            return redirect(url_for('ventas.ventas'))
        
        if 'carrito' not in session:
            session['carrito'] = []
            session['carrito_subtotal'] = 0
            session['carrito_iva'] = 0
            session['carrito_total'] = 0
        
        item_exists = False
        for item in session['carrito']:
            if item['galleta_id'] == galleta_id and item['presentacion_id'] == presentacion_id:
                item['cantidad'] += cantidad
                item['subtotal'] = item['precio'] * item['cantidad']
                item_exists = True
                break
        
        if not item_exists:
            new_item = {
                'galleta_id': galleta_id,
                'presentacion_id': presentacion_id,
                'presentacion_texto': presentacion.tipoPresentacion,
                'precio': float(presentacion.precio),
                'cantidad': cantidad,
                'subtotal': float(presentacion.precio) * cantidad
            }
            session['carrito'].append(new_item)
        
        subtotal = sum(item['subtotal'] for item in session['carrito'])
        iva = subtotal * 0.16
        total = subtotal + iva
        
        session['carrito_subtotal'] = subtotal
        session['carrito_iva'] = iva
        session['carrito_total'] = total
        session.modified = True
        
        flash('Producto agregado al carrito', 'success')
    else:
        flash('Error en el formulario', 'error')
    return redirect(url_for('ventas.ventas'))

@ventas_bp.route('/eliminar_del_carrito/<int:index>', methods=['POST'])
def eliminar_del_carrito(index):
    if 'carrito' in session and len(session['carrito']) > index:
        session['carrito'].pop(index)
        session['carrito_subtotal'] = sum(item['subtotal'] for item in session['carrito'])
        session['carrito_iva'] = session['carrito_subtotal'] * 0.16
        session['carrito_total'] = session['carrito_subtotal'] + session['carrito_iva']
        session.modified = True
        flash('Producto eliminado del carrito', 'success')
    else:
        flash('Error al eliminar el producto', 'error')

    return redirect(url_for('ventas.ventas'))


@ventas_bp.route('/procesar_pedido', methods=['POST'])
def procesar_pedido():
    if 'carrito' not in session or not session['carrito']:
        flash('El carrito está vacío', 'error')
        return redirect(url_for('ventas.ventas'))
    
    try:
        for item in session['carrito']:
            nueva_venta = VentaLocal(
                id_usuario=1,
                id_presentacion=item['presentacion_id'],
                cantidadcomprado=item['cantidad'],
                subtotal=item['subtotal'],
                total=item['subtotal'],
                fechaCompra=datetime.now()
            )
            db.session.add(nueva_venta)
        
        db.session.commit()
        session.pop('carrito', None)
        session.pop('carrito_subtotal', None)
        session.pop('carrito_iva', None)
        session.pop('carrito_total', None)
        
        flash('Pedido procesado con éxito', 'success')
        return redirect(url_for('ventas.ventas'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar el pedido: {str(e)}', 'error')
        return redirect(url_for('ventas.ventas'))