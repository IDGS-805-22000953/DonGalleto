from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from models.models import (
    db, Galleta, PresentacionGalleta, VentaLocal,PedidosCliente
)
from forms import AgregarAlCarritoForm

ventas_bp = Blueprint('ventas', __name__)

import base64
import os
from flask import current_app

@ventas_bp.route('/ventas', methods=['GET', 'POST'])
def ventas():
    galletas = Galleta.query.options(db.joinedload(Galleta.presentaciones)).all()
    
    # Convertir imágenes a base64
    for galleta in galletas:
        if galleta.rutaFoto:  # Asegúrate que haya una ruta de imagen
            try:
                image_path = os.path.join(current_app.static_folder, galleta.rutaFoto)
                with open(image_path, 'rb') as img_file:
                    galleta.rutaFoto_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            except Exception as e:
                current_app.logger.error(f"Error al cargar imagen: {str(e)}")
                galleta.rutaFoto_base64 = None
    
    form = AgregarAlCarritoForm()
    pedidos_pendientes_count = PedidosCliente.query.filter_by(estatus='pendiente').count()
    
    if 'carrito' not in session:
        session['carrito'] = []
        session['carrito_subtotal'] = 0
        session['carrito_iva'] = 0
        session['carrito_total'] = 0
    
    return render_template('Ventas/ventas2.html', 
                         galletas=galletas, 
                         form=form,
                         pedidos_pendientes_count=pedidos_pendientes_count) 
       
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

    return redirect(url_for('ventas.ventas'))


from flask_login import current_user  # Asegúrate de importar current_user

@ventas_bp.route('/procesar_pedido', methods=['POST'])
def procesar_pedido():
    if 'carrito' not in session or not session['carrito']:
        flash('El carrito está vacío', 'error')
        return redirect(url_for('ventas.ventas'))
    
    # Verificar si el usuario está autenticado
    if not current_user.is_authenticated:
        flash('Debes iniciar sesión para procesar un pedido', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        for item in session['carrito']:
            # Obtener la presentación de galleta
            presentacion = PresentacionGalleta.query.get(item['presentacion_id'])
            
            if not presentacion:
                flash(f'Presentación de galleta no encontrada (ID: {item["presentacion_id"]})', 'error')
                return redirect(url_for('ventas.ventas'))
                
            # Verificar que haya suficiente stock
            if presentacion.stock < item['cantidad']:
                flash(f'No hay suficiente stock para {presentacion.tipoPresentacion}', 'error')
                return redirect(url_for('ventas.ventas'))
            
            # Restar el stock
            presentacion.stock -= item['cantidad']
            
            # Crear la venta usando el ID del usuario autenticado
            nueva_venta = VentaLocal(
                id_usuario=current_user.id,  # Aquí usamos el ID del usuario logueado
                id_presentacion=item['presentacion_id'],
                cantidadcomprado=item['cantidad'],
                subtotal=item['subtotal'],
                total=item['subtotal'] * 1.16,
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
        
    
@ventas_bp.route('/pedidos-pendientes')
def mostrar_pedidos_pendientes():
    # Obtener todos los pedidos pendientes con relaciones
    pedidos_pendientes = PedidosCliente.query.filter_by(estatus='pendiente')\
        .options(db.joinedload(PedidosCliente.cliente),
                 db.joinedload(PedidosCliente.presentacion).joinedload(PresentacionGalleta.galleta))\
        .all()
    
    return render_template('Ventas/pedidos_pendientes.html',
                         pedidos_pendientes=pedidos_pendientes)

@ventas_bp.route('/marcar-como-vendido/<int:pedido_id>', methods=['POST'])
def marcar_como_vendido(pedido_id):
    pedido = PedidosCliente.query.get_or_404(pedido_id)
    
    try:
        pedido.estatus = 'completado'
        pedido.fechaRecogida = datetime.now()
        db.session.commit()
        flash('Pedido marcado como completado con éxito', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar el pedido: {str(e)}', 'error')
    
    return redirect(url_for('ventas.mostrar_pedidos_pendientes'))