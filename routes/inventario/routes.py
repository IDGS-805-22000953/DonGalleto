from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Insumo
from forms import RawMaterialForm
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from flask_login import login_required  # Importa el decorador login_required

# Crear el Blueprint para el módulo de inventario
inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

# Ruta para mostrar el inventario de insumos
@inventario_bp.route('/', methods=['GET'])
 # Protege esta ruta para usuarios autenticados
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
  # Protege esta ruta para usuarios autenticados
def agregar_material():
    form = RawMaterialForm()
    if form.validate_on_submit():
        nuevo_material = Insumo(
            nombre=form.name.data,
            fechaCaducidad=form.expiration_date.data,
            cantidad=form.quantity.data,
            unidadMedida=form.unit.data,
            presentacion="N/A",
            descripcion=form.description.data,
            porcentajeMerma=form.percentage_waste.data
        )
        db.session.add(nuevo_material)
        db.session.commit()
        flash('Materia prima agregada correctamente.', 'success')
        return redirect(url_for('inventario.inventario'))
    
    return render_template('inventario/agregar_material.html', form=form)

# Ruta para editar insumos 
@inventario_bp.route('/editar/<int:material_id>', methods=['GET', 'POST'])
  # Protege esta ruta para usuarios autenticados
def editar_material(material_id):
    material = Insumo.query.get_or_404(material_id)
    form = RawMaterialForm(obj=material)

    if form.validate_on_submit():
        material.nombre = form.name.data
        material.fechaCaducidad = form.expiration_date.data
        material.cantidad = form.quantity.data
        material.unidadMedida = form.unit.data
        material.presentacion = form.presentation.data
        material.descripcion = form.description.data
        material.porcentajeMerma = form.percentage_waste.data
        db.session.commit()
        flash('Materia prima actualizada correctamente.', 'success')
        return redirect(url_for('inventario.inventario'))

    return render_template('inventario/editar_material.html', form=form, material=material)

# Ruta para eliminar un insumo
@inventario_bp.route('/eliminar/<int:material_id>', methods=['POST'])
  # Protege esta ruta para usuarios autenticados
def eliminar_material(material_id):
    material = Insumo.query.get_or_404(material_id)
    db.session.delete(material)
    db.session.commit()
    flash('Materia prima eliminada correctamente.', 'danger')
    return redirect(url_for('inventario.inventario'))