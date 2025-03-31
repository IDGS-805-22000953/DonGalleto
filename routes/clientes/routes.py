from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from models.models import (
    db, Galleta, PresentacionGalleta, VentaLocal,PedidosCliente
)
from forms import AgregarAlCarritoForm
from datetime import datetime

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/clientes', methods=['GET', 'POST'])
def clientes():
    galletas = Galleta.query.options(db.joinedload(Galleta.presentaciones)).all()
    form = AgregarAlCarritoForm()
    
    if 'carrito' not in session:
        session['carrito'] = []
        session['carrito_subtotal'] = 0
        session['carrito_iva'] = 0
        session['carrito_total'] = 0
    
    return render_template('Cliente/pedidosOnline.html', galletas=galletas, form=form, now=datetime.now)

@clientes_bp.route('/agregar_al_carrito', methods=['POST'])
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
    return redirect(url_for('clientes.clientes'))

@clientes_bp.route('/eliminar_del_carrito/<int:index>', methods=['POST'])
def eliminar_del_carrito(index):
    if 'carrito' in session and 0 <= index < len(session['carrito']):
        item_eliminado = session['carrito'].pop(index)
        
        # Recalcular los totales
        subtotal = sum(item['subtotal'] for item in session['carrito'])
        iva = subtotal * 0.16
        total = subtotal + iva
        
        session['carrito_subtotal'] = subtotal
        session['carrito_iva'] = iva
        session['carrito_total'] = total
        session.modified = True
        
        flash(f'Producto {item_eliminado["presentacion_texto"]} eliminado del carrito', 'success')
    else:
        flash('Error al eliminar el producto: índice no válido', 'error')

    return redirect(url_for('clientes.clientes'))


@clientes_bp.route('/procesar_pedido', methods=['POST'])
def procesar_pedido():
    if 'carrito' not in session or not session['carrito']:
        flash('El carrito está vacío', 'error')
        return redirect(url_for('clientes.clientes'))
    
    # Obtener la fecha de recogida del formulario
    fecha_recogida_str = request.form.get('fecha_recogida')
    if not fecha_recogida_str:
        flash('Por favor selecciona una fecha de recogida', 'error')
        return redirect(url_for('clientes.ventas'))
    
    try:
        fecha_recogida = datetime.strptime(fecha_recogida_str, '%Y-%m-%d')
        
        # Verificar que la fecha no sea en el pasado
        if fecha_recogida.date() < datetime.now().date():
            flash('La fecha de recogida no puede ser en el pasado', 'error')
            return redirect(url_for('clientes.clientes'))
            
        # Obtener el ID del cliente (asumiendo que está en la sesión)
        #id_cliente = session.get('user_id')  # Ajusta esto según tu sistema de autenticación
        id_cliente = 1
        for item in session['carrito']:
            # Obtener la presentación de galleta
            presentacion = PresentacionGalleta.query.get(item['presentacion_id'])
            
            if not presentacion:
                flash(f'Presentación de galleta no encontrada (ID: {item["presentacion_id"]})', 'error')
                return redirect(url_for('clientes.clientes'))
                
            # Verificar que haya suficiente stock
            if presentacion.stock < item['cantidad']:
                flash(f'No hay suficiente stock para {presentacion.tipoPresentacion}', 'error')
                return redirect(url_for('clientes.clientes'))
            
            # Restar el stock
            presentacion.stock -= item['cantidad']
            
            # Crear el pedido del cliente
            nuevo_pedido = PedidosCliente(
                idCliente=id_cliente,
                id_presentacion=item['presentacion_id'],
                cantidadcomprado=item['cantidad'],
                subtotal=item['subtotal'],
                total=item['subtotal'] * 1.16,  # Incluyendo IVA
                fechaRecogida=fecha_recogida,
                estatus='pendiente'
            )
            db.session.add(nuevo_pedido)
        
        db.session.commit()
        session.pop('carrito', None)
        session.pop('carrito_subtotal', None)
        session.pop('carrito_iva', None)
        session.pop('carrito_total', None)
        
        flash('Pedido procesado con éxito. ¡Gracias por tu compra!', 'success')
        return redirect(url_for('clientes.clientes'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar el pedido: {str(e)}', 'error')
        return redirect(url_for('clientes.clientes'))