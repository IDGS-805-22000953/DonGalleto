
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
        flash('No tienes permisos para acceder a esta página', 'danger')
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
            
            flash('Empleado registrado exitosamente!', 'success')
            return redirect(url_for('empleados.lista_empleados'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar empleado: {str(e)}', 'danger')
    
    return render_template('Empleados/registro_empleado.html', form=form)

@empleados_bp.route('/', methods=['GET'])
@login_required
def lista_empleados():
    if current_user.rol != 'admin':
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('inicio'))
    
    # Obtener solo empleados (excluyendo clientes si existen en el modelo)
    empleados = Usuario.query.filter(Usuario.rol.in_(['admin', 'cajero', 'inventario', 'produccion'])).all()
    return render_template('lista_empleados.html', empleados=empleados)

@empleados_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_empleado(id):
    if current_user.rol != 'admin':
        flash('No tienes permisos para esta acción', 'danger')
        return redirect(url_for('inicio'))
    
    empleado = Usuario.query.get_or_404(id)
    form = RegistroEmpleadoForm(obj=empleado)
    
    if request.method == 'GET':
        form.rol.data = empleado.rol  # Asegurar que el rol se cargue correctamente
    
    if form.validate_on_submit():
        try:
            empleado.nombreUsuario = form.nombreUsuario.data
            empleado.apellidoPa = form.apellidoPa.data
            empleado.apellidoMa = form.apellidoMa.data
            empleado.correo = form.correo.data
            empleado.rol = form.rol.data
            
            if form.contrasenia.data:
                empleado.set_password(form.contrasenia.data)
            
            db.session.commit()
            flash('Empleado actualizado exitosamente!', 'success')
            return redirect(url_for('empleados.lista_empleados'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar empleado: {str(e)}', 'danger')
    
    return render_template('editar_empleado.html', form=form, empleado=empleado)

@empleados_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_empleado(id):
    if current_user.rol != 'admin':
        flash('No tienes permisos para esta acción', 'danger')
        return redirect(url_for('inicio'))
    
    empleado = Usuario.query.get_or_404(id)
    
    # No permitir eliminarse a sí mismo
    if empleado.id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('empleados.lista_empleados'))
    
    try:
        db.session.delete(empleado)
        db.session.commit()
        flash('Empleado eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar empleado: {str(e)}', 'danger')
    
    return redirect(url_for('empleados.lista_empleados'))