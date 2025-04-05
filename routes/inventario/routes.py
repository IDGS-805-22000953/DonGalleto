from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from flask_login import login_required
from forms import RawMaterialForm, ProveedorForm
from models.models import Proveedor, Insumo, PagoProveedor
from models.models import db  # Importa la instancia de db
from . import inventario_bp
from sqlalchemy.orm import joinedload
# Crear el Blueprint para el módulo de inventario
inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

# Ruta para mostrar el inventario de insumos
@inventario_bp.route('/', methods=['GET'])
@login_required  # Protege esta ruta para usuarios autenticados
def inventario():
    search_term = request.args.get('search', '')  # Obtiene el término de búsqueda desde la URL
    sort_by = request.args.get('sort_by', '')  # Obtener el parámetro de ordenación
    notification_weeks = int(request.args.get('weeks', 4))  # Obtener el parámetro de tiempo de alerta

    if search_term:
        
        raw_materials = Insumo.query.filter(Insumo.nombre.ilike(f'%{search_term}%'))
    else:
        raw_materials = Insumo.query

    if sort_by == 'fechaCaducidad':
        raw_materials = raw_materials.order_by(Insumo.fechaCaducidad)

    raw_materials = raw_materials.all()

    # Generar notificaciones
    notifications = []
    for material in raw_materials:
        caducidad = material.fechaCaducidad if isinstance(material.fechaCaducidad, datetime) else datetime.combine(material.fechaCaducidad, datetime.min.time())

        if caducidad <= (datetime.now() + timedelta(weeks=notification_weeks)):
            notifications.append({
                'nombre': material.nombre,
                'status': 'cerca de caducar',
                'fechaCaducidad': caducidad
            })

    return render_template('inventario/inventario.html', raw_materials=raw_materials, notifications=notifications, notification_weeks=notification_weeks)

# Ruta para agregar insumos 
@inventario_bp.route('/agregar', methods=['GET', 'POST'])
@login_required  # Protege esta ruta para usuarios autenticados
def agregar_material():
    form = RawMaterialForm()
    form.proveedor_id.choices = [(p.id, p.nombreProveedor) for p in Proveedor.query.all()]  # Llenar el select

    if form.validate_on_submit():
        nuevo_material = Insumo(
            nombre=form.name.data,
            fechaCaducidad=form.expiration_date.data,
            cantidad=form.quantity.data,
            unidadBase=form.unit.data,
            costoPorUnidad=form.cost_per_unit.data,
            descripcion=form.description.data,
            proveedor_id=form.proveedor_id.data  # Asigna el proveedor
        )
        db.session.add(nuevo_material)
        db.session.commit()
        flash('Materia prima agregada correctamente.', 'success')
        return redirect(url_for('inventario.inventario'))

    return render_template('inventario/agregar_material.html', form=form)

# Ruta para editar insumos
@inventario_bp.route('/editar/<int:material_id>', methods=['GET', 'POST'])
@login_required  # Protege esta ruta para usuarios autenticados
def editar_material(material_id):
    material = Insumo.query.get_or_404(material_id)
    form = RawMaterialForm(obj=material)
    form.proveedor_id.choices = [(p.id, p.nombreProveedor) for p in Proveedor.query.all()]

    if form.validate_on_submit():
        material.nombre = form.name.data
        material.fechaCaducidad = form.expiration_date.data
        material.cantidad = form.quantity.data
        material.unidadBase = form.unit.data
        material.costoPorUnidad = form.cost_per_unit.data
        material.descripcion = form.description.data
        material.proveedor_id = form.proveedor_id.data  # Actualiza el proveedor
        db.session.commit()
        flash('Materia prima actualizada correctamente.', 'success')
        return redirect(url_for('inventario.inventario'))

    form.proveedor_id.data = material.proveedor_id  # Preseleccionar proveedor
    return render_template('inventario/editar_material.html', form=form, material=material)

# Ruta para eliminar un insumo
@inventario_bp.route('/eliminar/<int:material_id>', methods=['POST'])
@login_required  # Protege esta ruta para usuarios autenticados
def eliminar_material(material_id):
    material = Insumo.query.get_or_404(material_id)
    db.session.delete(material)
    db.session.commit()
    flash('Materia prima eliminada correctamente.', 'danger')
    return redirect(url_for('inventario.inventario'))

# Ruta para mostrar la agenda de proveedores
@inventario_bp.route('/proveedores', methods=['GET'])
@login_required
def agenda_proveedores():
    proveedores = Proveedor.query.all()
    form_agregar = ProveedorForm()
    return render_template('inventario/agenda_proveedores.html', proveedores=proveedores, form=form_agregar)

# Ruta para agregar un nuevo proveedor (modal)
@inventario_bp.route('/proveedores/agregar', methods=['POST'])
@login_required
def agregar_proveedor():
    form = ProveedorForm()
    if form.validate_on_submit():
        nuevo_proveedor = Proveedor(
            nombreProveedor=form.nombreProveedor.data,
            direccion=form.direccion.data,
            correo=form.correo.data,
            telefono=form.telefono.data
        )
        db.session.add(nuevo_proveedor)
        db.session.commit()
        flash('Proveedor agregado correctamente.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
    return redirect(url_for('inventario.agenda_proveedores'))

# Ruta para editar un proveedor existente (modal)
@inventario_bp.route('/proveedores/editar/<int:proveedor_id>', methods=['POST'])
@login_required
def editar_proveedor(proveedor_id):
    proveedor = Proveedor.query.get_or_404(proveedor_id)
    form = ProveedorForm(obj=proveedor)
    if form.validate_on_submit():
        proveedor.nombreProveedor = form.nombreProveedor.data
        proveedor.direccion = form.direccion.data
        proveedor.correo = form.correo.data
        proveedor.telefono = form.telefono.data
        db.session.commit()
        flash('Proveedor actualizado correctamente.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en el campo {getattr(form, field).label.text}: {error}', 'danger')
    return redirect(url_for('inventario.agenda_proveedores'))

# Ruta para eliminar un proveedor
@inventario_bp.route('/proveedores/eliminar/<int:proveedor_id>', methods=['POST'])
@login_required
def eliminar_proveedor(proveedor_id):
    proveedor = Proveedor.query.get_or_404(proveedor_id)
    db.session.delete(proveedor)
    db.session.commit()
    flash('Proveedor eliminado correctamente.', 'danger')
    return redirect(url_for('inventario.agenda_proveedores'))
