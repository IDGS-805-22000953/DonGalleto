from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from datetime import datetime
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
from models import db, Galleta, PresentacionGalleta


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.secret_key = "supersecretkey"  # Asegurar sesiones
csrf = CSRFProtect(app)
db.init_app(app)

# =======================
# Rutas principales
# =======================
@app.route("/")
def index():
    return render_template("index.html")



@app.route("/central")
def central():
    return render_template("Central/inicioCentral.html")


#PRODUCCION
# 🔹 Mostrar todas las galletas con sus presentaciones
@app.route("/produccion")
def produccion():
    galletas = Galleta.query.all()
    presentaciones = {g.id: PresentacionGalleta.query.filter_by(idGalleta=g.id).all() for g in galletas}
    return render_template("Produccion/inicioProduccion.html", galletas=galletas, presentaciones=presentaciones)

# 🔹 Filtrar solo por piezas
@app.route("/piezas")
def piezas():
    presentaciones = PresentacionGalleta.query.filter_by(tipoPresentacion="piezas").all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="piezas")

# 🔹 Filtrar solo por gramaje
@app.route("/gramaje")
def gramaje():
    presentaciones = PresentacionGalleta.query.filter_by(tipoPresentacion="gramos").all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="gramaje")

# 🔹 Filtrar solo por paquete (1kg y 700g)
@app.route("/paquete")
def paquete():
    presentaciones = PresentacionGalleta.query.filter(PresentacionGalleta.tipoPresentacion.in_(["1kg", "700g"])).all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="paquete")


#COCINA
@app.route("/cocina")
def cocina():
    
    return render_template("Cocina/cocina.html")



#Clientes
@app.route("/cliente")
def cliente():
    return render_template("Cliente/inicioCliente.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# =======================
# Catálogo de galletas
# =======================
@app.route('/catalogo')
def catalogo_galletas():
    galletas = Galleta.query.all()
    return render_template("Cliente/catalogo.html", galletas=galletas)

# =======================
# Manejo de pedidos
# =======================
@app.route('/cliente/pedidos', methods=['GET'])
def mostrar_pedidos():
    galletas = Galleta.query.all()
    carrito = session.get("carrito", [])
    for item in carrito:
        item['precio'] = float(item['precio'])

    return render_template("Cliente/pedidos.html", galletas=galletas, carrito=carrito)

@app.route('/agregar_carrito/<int:id>', methods=['POST'])
def agregar_carrito(id):
    galleta = Galleta.query.get(id)
    if not galleta:
        flash("Galleta no encontrada", "error")
        return redirect(url_for("mostrar_pedidos"))

    carrito = session.get("carrito", [])
    carrito.append({"id": galleta.id, "nombre": galleta.nombre, "precio": galleta.precio})

    session["carrito"] = carrito
    session.modified = True  
    flash("Galleta agregada al carrito", "success")
    
    return redirect(url_for("mostrar_pedidos"))



@app.route('/eliminar_carrito/<int:index>')
def eliminar_carrito(index):
    carrito = session.get("carrito", [])
    
    if 0 <= index < len(carrito):
        del carrito[index]
        session["carrito"] = carrito
        session.modified = True
        flash("Producto eliminado del carrito", "info")
    
    return redirect(url_for("mostrar_pedidos"))

@app.route('/vaciar_carrito')
def vaciar_carrito():
    session.pop("carrito", None)
    flash("Carrito vaciado", "info")
    return redirect(url_for("mostrar_pedidos"))

# =======================
# Guardar pedidos
# =======================
@app.route('/cliente/pedidos/guardar', methods=['POST'])
def guardar_pedido():
    try:
        data = request.get_json()
        nombre_cliente = data.get("name")
        direccion = data.get("address")
        metodo_pago = data.get("payment")
        carrito = session.get("carrito", [])

        if not carrito:
            return jsonify({"error": "El carrito está vacío"}), 400

        cliente = Cliente.query.filter_by(nombre=nombre_cliente).first()
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        nuevo_pedido = Pedido(idCliente=cliente.id, fechaRecogida=None, estado='pendiente')
        db.session.add(nuevo_pedido)
        db.session.commit()

        for item in carrito:
            galleta = Galleta.query.filter_by(nombre=item["nombre"]).first()
            if not galleta:
                return jsonify({"error": f"Galleta '{item['nombre']}' no encontrada"}), 404

            nuevo_detalle = DetallePedido(
                idPedido=nuevo_pedido.id,
                idGalleta=galleta.id,
                tipoPresentacion="piezas",
                cantidad=1,
                subtotal=item["precio"]
            )
            db.session.add(nuevo_detalle)

        db.session.commit()

        session.pop("carrito", None)
        flash("Pedido guardado exitosamente", "success")
        return jsonify({"message": "Pedido guardado exitosamente"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



# prueba ventas

@app.route('/ventas')
def ventas():
    # Obtener todas las galletas con sus presentaciones
    galletas = Galleta.query.options(db.joinedload(Galleta.presentaciones)).all()
    
    # Procesar los datos para la vista
    galletas_data = []
    for galleta in galletas:
        presentaciones = ", ".join([f"{p.cantidad} {p.tipoPresentacion}" 
                                  for p in galleta.presentaciones])
        galletas_data.append({
            'id': galleta.id,
            'nombre': galleta.nombre,
            'descripcion': galleta.descripcion,
            'precio': galleta.precio,
            'stock': galleta.stock,
            'presentaciones': presentaciones,
            'rutaFoto': galleta.rutaFoto
        })
    
    return render_template('Ventas/ventas2.html', galletas=galletas_data)






# =======================
# Iniciar aplicación
# =======================
if __name__ == '__main__':
    csrf.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
