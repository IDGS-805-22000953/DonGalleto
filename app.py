from flask import Flask, render_template, request, redirect, url_for,jsonify
from flask import flash
from flask_wtf.csrf import CSRFProtect
from flask import g
from config import DevelopmentConfig
from models import (
    db,
    Usuario,
    Cliente,
    Insumo,
    Proveedor,
    InsumosProveedor,
    PagoProveedor,
    Receta,
    RecetaInsumos,
    Galleta,
    Produccion,
    Pedido,
    DetallePedido,
    Venta,
    Merma,
    CorteVentas
)

from models import db


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf=CSRFProtect()


@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

@app.route("/")
@app.route("/central")
def central():
	return render_template("Central/inicioCentral.html")

@app.route("/")
@app.route("/cliente")
def cliente():
	return render_template("Cliente/inicioCliente.html")

@app.errorhandler(404)
def page_not_found(e):
        return render_template('404.html'), 404

@app.route('/catalogo')
def catalogo_galletas():
    galletas = Galleta.query.all()
    print("Galletas encontradas:", [(g.id, g.nombre, g.rutaFoto) for g in galletas])  # Debug
    return render_template("Cliente/catalogo.html", galletas=galletas)



@app.route('/cliente/pedidos', methods=['GET'])
def mostrar_pedidos():
    # Obtener todas las galletas de la base de datos
    galletas = Galleta.query.all()
    return render_template("Cliente/pedidos.html", galletas=galletas)

@app.route('/cliente/pedidos', methods=['POST'])
def guardar_pedido():
    try:
        data = request.get_json()
        nombre_cliente = data.get("name")
        direccion = data.get("address")
        metodo_pago = data.get("payment")
        carrito = data.get("cart", [])

        # Validar si el carrito tiene productos
        if not carrito:
            return jsonify({"error": "El carrito está vacío"}), 400

        # Verificar si el cliente existe
        cliente = Cliente.query.filter_by(nombre=nombre_cliente).first()
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        # Crear un nuevo pedido
        nuevo_pedido = Pedido(idCliente=cliente.id, fechaRecogida=None, estado='pendiente')
        db.session.add(nuevo_pedido)
        db.session.commit()  # Guardamos para obtener el ID del pedido

        # Agregar los productos del carrito al detalle del pedido
        for item in carrito:
            galleta = Galleta.query.filter_by(nombre=item["name"]).first()
            if not galleta:
                return jsonify({"error": f"Galleta '{item['name']}' no encontrada"}), 404

            nuevo_detalle = DetallePedido(
                idPedido=nuevo_pedido.id,
                idGalleta=galleta.id,
                tipoPresentacion="piezas",  # Ajustar según necesidad
                cantidad=1,  # Ajustar según el JSON recibido
                subtotal=item["price"]
            )
            db.session.add(nuevo_detalle)

        db.session.commit()  # Guardar los detalles

        return jsonify({"message": "Pedido guardado exitosamente"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
  

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run()