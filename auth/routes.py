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
        username = form.username.data
        password = form.password.data
        email = form.email.data
        apellidoPa = form.apellidoPa.data
        apellidoMa = form.apellidoMa.data
        rol = form.rol.data
        recaptcha_response = request.form['g-recaptcha-response']

        if not verify_recaptcha(recaptcha_response):
            flash('Por favor completa el CAPTCHA', 'danger')
            return redirect(url_for('auth.register'))

        # Validar que el nombre de usuario tenga al menos dos nombres
        if not validate_username(username):
            flash('El nombre de usuario debe tener al menos dos nombres', 'danger')
            return redirect(url_for('auth.register'))

        # Validar la longitud de la contraseña
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return redirect(url_for('auth.register'))

        # Validar formato de email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('El correo electrónico no es válido', 'danger')
            return redirect(url_for('auth.register'))

        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(nombreUsuario=username).first():
            flash('El usuario ya existe', 'warning')
            return redirect(url_for('auth.register'))

        # Si pasa todas las validaciones
        new_user = Usuario(
            nombreUsuario=username,
            apellidoPa=apellidoPa,
            apellidoMa=apellidoMa,
            correo=email,
            rol=rol
        )
        new_user.set_password(password)  # Almacena la contraseña hasheada
        db.session.add(new_user)
        db.session.commit()
        flash('Registro exitoso, ahora puedes iniciar sesión', 'success')
        return redirect(url_for('auth.login'))

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
    return render_template('Central/inicioCentral.html')

@auth_bp.route('/cliente_dashboard')
@login_required
def cliente_dashboard():
    if current_user.rol != 'cliente':
        flash('No tienes permiso para acceder a esta página', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('Cliente/inicioCliente.html')
