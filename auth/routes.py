from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.models import db, Usuario, Cliente
from forms import LoginForm, RegistrationForm
from werkzeug.security import check_password_hash
import requests
import re

auth_bp = Blueprint('auth', __name__)
# Función para verificar el CAPTCHA
def verify_recaptcha(recaptcha_response):
    secret_key = '6LdEuQUrAAAAABGCpdHiYk3-TBA1cgIxOJ61gzLN'  # Reemplaza con tu clave secreta
    payload = {
        'secret': secret_key,
        'response': recaptcha_response
    }
    verify_response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
    result = verify_response.json()
    return result.get('success')

# Función para validar que el nombre de usuario tenga al menos dos nombres
def validate_username(username):
    # Verificamos que haya al menos dos palabras en el nombre de usuario
    if len(username.split()) < 2:
        return False
    return True

# Ruta de login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        recaptcha_response = request.form['g-recaptcha-response']

        if not verify_recaptcha(recaptcha_response):
            flash('Por favor completa el CAPTCHA', 'danger')
            return redirect(url_for('auth.login'))

        user = Usuario.query.filter_by(nombreUsuario=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')

            # Redirección basada en el rol del usuario, cargando los HTML correspondientes
            if user.rol == 'admin':
                return redirect(url_for('auth.admin_dashboard'))  # Redirige al dashboard del admin
            elif user.rol == 'cliente':
                return redirect(url_for('auth.cliente_dashboard'))  # Redirige al dashboard del cliente
            else:
                flash('Rol desconocido', 'danger')
                return redirect(url_for('auth.login'))  # Vuelve a la página de login
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('index.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Verificar si el cliente ya existe
            existing_client = Cliente.query.filter_by(correo=form.email.data).first()
            if existing_client:
                flash('Este correo electrónico ya está registrado', 'danger')
                return redirect(url_for('auth.register'))

            # Validación de contraseña
            if len(form.password.data) < 8:
                flash('La contraseña debe tener al menos 8 caracteres', 'danger')
                return redirect(url_for('auth.register'))

            # Crear nuevo cliente
            new_client = Cliente(
                nombre=form.username.data,
                apellidoPa=form.apellidoPa.data,
                correo=form.email.data,
                contrasenia=generate_password_hash(form.password.data)
            )

            db.session.add(new_client)
            db.session.commit()  # Asegurar el commit
            
            flash('Registro exitoso. Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Error al registrar. Por favor intenta nuevamente.', 'danger')
            print(f"Error en registro: {str(e)}")  # Para depuración
            return redirect(url_for('auth.register'))

    # Si hay errores en el formulario
    elif request.method == 'POST':
        flash('Por favor corrige los errores en el formulario', 'danger')

    return render_template('registro.html', form=form)

# Ruta de logout
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('auth.login'))

# Protege las rutas para que sólo los usuarios autenticados puedan acceder
@auth_bp.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.rol != 'admin':
        flash('No tienes permiso para acceder a esta página', 'danger')
        return redirect(url_for('auth.login'))
    return redirect(url_for('dashboard.mostrar_dashboard'))

@auth_bp.route('/cliente_dashboard')
@login_required
def cliente_dashboard():
    if current_user.rol != 'cliente':
        flash('No tienes permiso para acceder a esta página', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('Cliente/pedidosOnline.html')