from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
import logging
from models.models import (
    db
)


from routes.clientes.routes import clientes_bp
from routes.cocina.routes import cocina_bp
from routes.produccion.routes import produccion_bp
from routes.ventas.routes import ventas_bp
from routes.central.routes import dashboard_bp
from routes.corte_caja.routes import corte_bp


# Configuracion del logging
logging.basicConfig(
    filename='app.log', level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)

db.init_app(app)


""" # Configuración del Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login' 

# Cargar usuario para flask-login
@login_manager.user_loader
def load_user(user_id):
    from models.models import User
    return User.query.get(int(user_id)) """

# Registrar los Blueprints
app.register_blueprint(clientes_bp, url_prefix='/cliente')
app.register_blueprint(cocina_bp, url_prefix='/cocina')
app.register_blueprint(produccion_bp, url_prefix='/produccion')
app.register_blueprint(ventas_bp, url_prefix='/ventas')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(corte_bp, url_prefix='/corte')




with app.app_context():
    print("Intentando crear tablas negras...")
    db.create_all()
    print("Tablas creadas.")

with app.app_context():
    db.create_all()
    

# =======================
# Rutas principales
# =======================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/central")
def central():
    return render_template("Central/inicioCentral.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404



# =======================
# Iniciar aplicación
# =======================
if __name__ == '__main__':
    csrf.init_app(app)
    with app.app_context():
        
        db.create_all()
    app.run(debug=True)
