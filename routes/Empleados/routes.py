
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from flask_login import login_required
from models.models import (
    db, Galleta, PresentacionGalleta, VentaLocal,PedidosCliente,Usuario
)
from forms import AgregarAlCarritoForm,RegistroEmpleadoForm

from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

empleados_bp = Blueprint('empleados', __name__)

@empleados_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar_empleado():
    # Verificar que solo los administradores pueden registrar empleados
    if current_user.rol != 'admin':
        flash('No tienes permisos para acceder a esta página', 'registro_error')
        return redirect(url_for('index'))
    
    form = RegistroEmpleadoForm()
    
    if form.validate_on_submit():
        try:
            nuevo_empleado = Usuario(
            nombre=form.nombreUsuario.data,           # nombreUsuario -> nombre
            apellido_paterno=form.apellidoPa.data,   # apellidoPa -> apellido_paterno
            apellido_materno=form.apellidoMa.data,   # apellidoMa -> apellido_materno
            correo=form.correo.data,
            rol=form.rol.data
            )
            
            nuevo_empleado.set_password(form.contrasenia.data)
            
            db.session.add(nuevo_empleado)
            db.session.commit()
            
            flash('Empleado registrado exitosamente!', 'registro_success')
            return redirect(url_for('empleados.lista_empleados'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar empleado: {str(e)}', 'registro_error')
    
    return render_template('Empleados/registro_empleado.html', form=form)

@empleados_bp.route('/', methods=['GET'])
@login_required
def lista_empleados():
    if current_user.rol != 'admin':
        flash('No tienes permisos para acceder a esta página', 'registro_error')
        return redirect(url_for('index'))
    
    # Obtener solo empleados (excluyendo clientes si existen en el modelo)
    empleados = Usuario.query.filter(Usuario.rol.in_(['admin', 'cajero', 'inventario', 'produccion'])).all()
    return render_template('Empleados/lista_empleados.html', empleados=empleados)


from flask import jsonify

@empleados_bp.route('/actualizar-rol/<int:id>', methods=['POST'])
@login_required
def actualizar_rol(id):
    if current_user.rol != 'admin':
        return jsonify({'success': False, 'error': 'No tienes permisos'}), 403
    
    empleado = Usuario.query.get_or_404(id)
    nuevo_rol = request.form.get('rol')
    
    if nuevo_rol not in ['admin', 'cajero', 'produccion', 'inventario']:
        return jsonify({'success': False, 'error': 'Rol no válido'}), 400
    
    try:
        empleado.rol = nuevo_rol
        db.session.commit()
        return redirect(url_for('empleados.lista_empleados'))
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
     
                     
@empleados_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_empleado(id):
    if current_user.rol != 'admin':
        flash('No tienes permisos para esta acción', 'lista_error')
        return redirect(url_for('inicio'))
    
    empleado = Usuario.query.get_or_404(id)
    
    # No permitir eliminarse a sí mismo
    if empleado.id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'lista_error')
        return redirect(url_for('empleados.lista_empleados'))
    
    try:
        db.session.delete(empleado)
        db.session.commit()
        flash('Empleado eliminado exitosamente', 'lista_error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar empleado: {str(e)}', 'lista_error')
    
    return redirect(url_for('empleados.lista_empleados'))