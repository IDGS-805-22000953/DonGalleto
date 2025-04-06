from flask import Flask, render_template, redirect, url_for, jsonify, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from sqlalchemy.exc import SAWarning
from datetime import datetime
from flask_login import LoginManager, logout_user, login_required, login_user, current_user
import logging
from auth import auth_bp  
import forms
from models.models import (
    db, Usuario, Insumo, Proveedor, InsumosProveedor, PagoProveedor, Receta, RecetaInsumos,
    Galleta, Produccion, Merma
)
from routes.clientes.routes import clientes_bp
from routes.cocina.routes import cocina_bp
from routes.produccion.routes import produccion_bp
from routes.ventas.routes import ventas_bp
from routes.central.routes import dashboard_bp
from routes.inventario.routes import inventario_bp
from routes.corte_caja.routes import corte_bp

from routes.Empleados.routes import empleados_bp
from auth.routes import auth_bp

# Configuración del logging
logging.basicConfig(
    filename='app.log', level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.secret_key = "supersecretkey"
csrf = CSRFProtect(app)
db.init_app(app)

# Configuración del Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))  # Método actualizado para SQLAlchemy 2.0

# Registrar los Blueprints
app.register_blueprint(clientes_bp, url_prefix='/cliente')
app.register_blueprint(cocina_bp, url_prefix='/cocina')
app.register_blueprint(produccion_bp, url_prefix='/produccion')
app.register_blueprint(ventas_bp, url_prefix='/ventas')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(inventario_bp, url_prefix='/inventario')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(corte_bp, url_prefix='/corte')
app.register_blueprint(empleados_bp, url_prefix='/empleados')

# =======================
# Rutas principales
# =======================
from flask import Flask, render_template
from forms import LoginForm  

@app.route("/")
def index():
    form = LoginForm()  # Instancia del formulario
    return render_template("index.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('auth.login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# =======================
# Iniciar aplicación
# =======================
if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            
        app.run(debug=True)
    except Exception as e:
        logging.error(f"Error al iniciar la aplicación: {e}")
