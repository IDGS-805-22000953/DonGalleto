from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.models import db, Usuario
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
            flash('Por favor completa el CAPTCHA', 'login_error')
            return redirect(url_for('auth.login'))

        # Buscar en Usuario (por nombreUsuario o correo)
        user = Usuario.query.filter(
            (Usuario.nombre == username) | (Usuario.correo == username)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso', 'login_success')

            if user.rol == 'admin':
                return redirect(url_for('dashboard.mostrar_dashboard'))
            elif user.rol == 'cliente':
                return redirect(url_for('clientes.clientes'))
            elif user.rol == 'cajero':
                return redirect(url_for('ventas.ventas'))
            elif user.rol == 'cocina':
                return redirect(url_for('produccion.produccion'))
            else:
                flash('Rol desconocido', 'login_advertencia')
                return redirect(url_for('auth.login'))
        else:
            flash('Usuario o contraseña incorrectos', 'login_error')
    
    return render_template('index.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        apellidoPa = form.apellidoPa.data
        recaptcha_response = request.form['g-recaptcha-response']

        if not verify_recaptcha(recaptcha_response):
            flash('Por favor completa el CAPTCHA', 'register_error')
            return redirect(url_for('auth.register'))

        # Validaciones
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'register_error')
            return redirect(url_for('auth.register'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('El correo electrónico no es válido', 'register_error')
            return redirect(url_for('auth.register'))

        if Usuario.query.filter_by(correo=email).first():
            flash('El correo electrónico ya está registrado', 'register_error')
            return redirect(url_for('auth.register'))

        # Crear nuevo usuario con rol de cliente
        new_user = Usuario(
            nombre=username,
            apellido_paterno=apellidoPa,
            correo=email,
            rol='cliente'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registro exitoso, ahora puedes iniciar sesión', 'register_success')
        return redirect(url_for('auth.login'))

    return render_template('registro.html', form=form)

# Ruta de logout
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'login_success')
    return redirect(url_for('auth.login'))

# Protege las rutas para que sólo los usuarios autenticados puedan acceder
@auth_bp.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.rol != 'admin':
        flash('No tienes permiso para acceder a esta página', 'login_error')
        return redirect(url_for('auth.login'))
    return render_template('Central/dashboard.html')

@auth_bp.route('/cliente_dashboard')
@login_required
def cliente_dashboard():
    if current_user.rol != 'cliente':
        flash('No tienes permiso para acceder a esta página', 'login_error')
        return redirect(url_for('auth.login'))
    return render_template('Cliente/pedidosOnline.html')