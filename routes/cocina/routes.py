from flask import Blueprint,Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from datetime import datetime
import base64
from decimal import Decimal

from flask import request
from werkzeug.utils import secure_filename
from models.models import (
    db,
    Usuario,
    Cliente,
    Insumo,
    Proveedor,
    Produccion,
    InsumosProveedor,
    PagoProveedor,
    Receta,
    RecetaInsumos,
    Galleta,
    Merma,
    PresentacionGalleta,
    EstatusProduccion
)


cocina_bp = Blueprint('cocina', __name__)


@cocina_bp.route("/cocina")
def cocina():
    galletas = Galleta.query.all()  # Obtener todas las galletas de la base de datos
    presentaciones = PresentacionGalleta.query.all()
    insumos = Insumo.query.all()
    
    alertas = db.session.query(
        EstatusProduccion,
        PresentacionGalleta.tipoPresentacion
    ).join(
        PresentacionGalleta, EstatusProduccion.idPresentacion == PresentacionGalleta.id
    ).all()

    historial_merma = (
        db.session.query(
            Galleta.nombre,
            Merma.cantidad,
            Merma.motivo,
            Merma.fechaRegistro
        )
        .join(Galleta, Galleta.id == Merma.idGalleta)
        .order_by(Merma.fechaRegistro.desc())
        .all()
    )

    # Obtener todos los tipos de galletas
    tipos_galletas = [galleta.nombre for galleta in galletas]

    return render_template(
        "Cocina/cocina.html",
        alertas=alertas,
        historial_merma=historial_merma,
        tipos_galletas=tipos_galletas,
        insumos=insumos
    )



@cocina_bp.route("/nueva_galleta", methods=["GET", "POST"])
def nueva_galleta():
    insumos = Insumo.query.all()

    if request.method == "POST":
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        insumos_seleccionados = request.form.getlist("insumos")  
        imagen = request.files.get("imagen")
        precio = request.form.get("precio", type=float)  # Obtener precio

        if imagen:
            imagen_data = imagen.read()
            imagen_base64 = base64.b64encode(imagen_data).decode("utf-8")
        else:
            imagen_base64 = None

        nueva_receta = Receta(nombreReceta=nombre, descripcion=descripcion, rutaFoto=imagen_base64)
        db.session.add(nueva_receta)
        db.session.flush()  

        for id_insumo in insumos_seleccionados:
            cantidad_insumo = request.form.get(f"cantidad_{id_insumo}", type=int)
            if cantidad_insumo and cantidad_insumo > 0:
                receta_insumo = RecetaInsumos(
                    idReceta=nueva_receta.id,
                    idInsumo=int(id_insumo),
                    cantidadInsumo=cantidad_insumo
                )
                db.session.add(receta_insumo)

        nueva_galleta = Galleta(nombre=nombre, descripcion=descripcion, idReceta=nueva_receta.id, rutaFoto=imagen_base64)
        db.session.add(nueva_galleta)
        db.session.flush()  

        presentaciones = {
    "Piezas": precio,  # La pieza es de 100g y su precio es el ingresado
    "Gramos": precio / 100,  # Precio por gramo
    "1kg": precio * 10,  # 1000g → 10 piezas
    "700g": precio * 7,  # 700g → 7 piezas
}


        for tipo, precio_presentacion in presentaciones.items():
            nueva_presentacion = PresentacionGalleta(
                idGalleta=nueva_galleta.id,
                tipoPresentacion=tipo,
                cantidad=0,  # Stock inicial en 0
                stock=0,  # Se asignará después de la producción
                precio=precio_presentacion,  
                fechaCaducidad=datetime.now().date()  
            )
            db.session.add(nueva_presentacion)


        nueva_produccion = EstatusProduccion(
            idGalleta=nueva_galleta.id,
            nombreGalleta=nombre,
            estatus="En preparación",
            tiempoEstimado=30,
            idPresentacion=1  
        )
        db.session.add(nueva_produccion)

        db.session.commit()
        flash("Galleta creada correctamente", "success")
        return redirect(url_for("cocina.cocina"))

    return render_template("Cocina/nuevaGalleta.html", insumos=insumos)



@cocina_bp.route("/cambiar_estatus", methods=["POST"])
def cambiar_estatus():
    id_produccion = request.form.get("id_produccion")
    produccion = EstatusProduccion.query.get(id_produccion)

    if not produccion:
        flash("Producción no encontrada", "error")
        return redirect(url_for("cocina.cocina"))

    estatus_orden = ["En preparacion", "Horneando", "Enfriando"]

    if produccion.estatus in estatus_orden:
        indice_actual = estatus_orden.index(produccion.estatus)
        
        if indice_actual < len(estatus_orden) - 1:
            
            produccion.estatus = estatus_orden[indice_actual + 1]
            db.session.commit()
        else:

            registrar_produccion(produccion.idGalleta, produccion.idPresentacion)

            
            actualizar_stock(produccion.idGalleta, produccion.idPresentacion)
            db.session.delete(produccion)
            db.session.commit()

    return redirect(url_for("cocina.cocina"))

def registrar_produccion(id_galleta, id_presentacion):
    galleta = Galleta.query.get(id_galleta)
    presentacion = PresentacionGalleta.query.get(id_presentacion)

    if not galleta or not presentacion:
        print("Galleta o presentación no encontrada.")
        return

    # Definir la cantidad producida según la presentación
    cantidad_producida = 0
    if presentacion.tipoPresentacion == "1kg":
        cantidad_producida = 10  # 10 paquetes de 1kg
    elif presentacion.tipoPresentacion == "700g":
        cantidad_producida = 14  # 14 paquetes de 700g
    elif presentacion.tipoPresentacion == "Gramos":
        cantidad_producida = 10000  # 10000g (100 galletas)
    elif presentacion.tipoPresentacion == "Piezas":
        cantidad_producida = 100  # 100 piezas

    nueva_produccion = Produccion(
        idReceta=galleta.idReceta,
        idGalleta=galleta.id, 
        cantidadProducida=cantidad_producida,
        fechaProduccion=datetime.now()
    )
    db.session.add(nueva_produccion)
    db.session.commit()
    print(f"Producción registrada: {cantidad_producida} {presentacion.tipoPresentacion}")


def actualizar_stock(id_galleta, id_presentacion):
    presentacion = PresentacionGalleta.query.get(id_presentacion)
    if not presentacion:
        print("No se encontró la presentación con ID:", id_presentacion)
        return

    galleta = Galleta.query.get(id_galleta)
    if not galleta:
        print("No se encontró la galleta con ID:", id_galleta)
        return

    receta = Receta.query.get(galleta.idReceta)
    if not receta:
        print("No se encontró la receta con ID:", galleta.idReceta)
        return

    # Ajuste de stock al completar la producción para todas las presentaciones
    if presentacion.tipoPresentacion == "1kg":
        presentacion.stock += 10  # 10 paquetes de 1kg
    elif presentacion.tipoPresentacion == "700g":
        presentacion.stock += 14  # 14 paquetes de 700g
        # Agregar los gramos restantes
        gramaje = PresentacionGalleta.query.filter_by(tipoPresentacion="Gramos", idGalleta=id_galleta).first()
        if gramaje:
            gramaje.stock += 200
    elif presentacion.tipoPresentacion == "Gramos":
        presentacion.stock += 10000  # 10000g (100 galletas)
    elif presentacion.tipoPresentacion == "Piezas":
        presentacion.stock += 100  # 100 piezas

    # Descontar insumos usados en la receta
    insumos_receta = RecetaInsumos.query.filter_by(idReceta=receta.id).all()
    for receta_insumo in insumos_receta:
        insumo = Insumo.query.get(receta_insumo.idInsumo)
        if insumo:
            insumo.cantidad -= receta_insumo.cantidadInsumo  # Descontar la cantidad usada
            if insumo.cantidad < 0:
                insumo.cantidad = 0  # Evitar negativos

    db.session.commit()

@cocina_bp.route("/ingresar_merma", methods=["GET", "POST"])
def ingresar_merma():
    galletas = Galleta.query.all()  # Obtener todas las galletas de la base de datos
    insumos = Insumo.query.all()  # Obtener todos los insumos
    if request.method == "POST":
        tipo_merma = request.form.get("tipo_merma")
        motivo_merma = request.form.get("motivo_merma")

        # Caso de merma de galleta
        if tipo_merma == "galleta":
            tipo_galleta_merma = request.form.get("tipo_galleta_merma")
            cantidad_merma = request.form.get("cantidad_merma_galleta")

            # Verificar si la cantidad_merma no está vacía y es un número válido
            if not cantidad_merma:
                return "La cantidad de merma no puede estar vacía"
            try:
                cantidad_merma = int(cantidad_merma)
            except ValueError:
                return "Valor inválido para la cantidad de merma"

            # Obtener la receta de la galleta seleccionada
            galleta = Galleta.query.filter_by(nombre=tipo_galleta_merma).first()
            if not galleta:
                return "Galleta no encontrada"
            receta = Receta.query.get(galleta.idReceta)

            # Calcular el descuento de insumos basado en la cantidad de galletas
            insumos_receta = RecetaInsumos.query.filter_by(idReceta=receta.id).all()
            for receta_insumo in insumos_receta:
                insumo = Insumo.query.get(receta_insumo.idInsumo)
                if insumo:
                    cantidad_a_descartar = receta_insumo.cantidadInsumo * (cantidad_merma / 100)
                    insumo.cantidad -= cantidad_a_descartar
                    if insumo.cantidad < 0:
                        insumo.cantidad = 0

            # Registrar la merma de galleta
            merma = Merma(
                idGalleta=galleta.id,
                cantidad=cantidad_merma,
                motivo=motivo_merma,
                fechaRegistro=datetime.now()
            )
            db.session.add(merma)

        # Caso de merma de insumo
        elif tipo_merma == "insumo":
            id_insumo = request.form.get("id_insumo")
            cantidad_merma = request.form.get("cantidad_merma")

            # Verificar si la cantidad_merma no está vacía y es un número válido
            if not cantidad_merma:
                return "La cantidad de merma no puede estar vacía"
            try:
                cantidad_merma = float(cantidad_merma)
            except ValueError:
                return "Valor inválido para la cantidad de merma"

            # Descontar la cantidad de insumo seleccionado
            if id_insumo and cantidad_merma:
                insumo = Insumo.query.get(id_insumo)
                if insumo:
                    insumo.cantidad -= Decimal(cantidad_merma)
                    if insumo.cantidad < 0:
                        insumo.cantidad = 0

                    # Registrar la merma de insumo
                    merma = Merma(
                        idInsumo=insumo.id,
                        cantidad=cantidad_merma,
                        motivo=motivo_merma,
                        fechaRegistro=datetime.now()
                    )
                    db.session.add(merma)

        # Confirmación y redirección
        db.session.commit()
        flash("Merma registrada correctamente", "success")
        return redirect(url_for("cocina.cocina"))

    return render_template("Cocina/cocina.html", galletas=galletas, insumos=insumos)

@cocina_bp.route("/historial_merma", methods=["GET"])
def historial_merma():
    tipo_merma = request.args.get("tipo_merma", "galleta")  # Por defecto es 'galleta'

    if tipo_merma == "galleta":
        historial_merma = (
            db.session.query(
                Galleta.nombre,
                Merma.cantidad,
                Merma.motivo,
                Merma.fechaRegistro
            )
            .join(Galleta, Galleta.id == Merma.idGalleta)
            .order_by(Merma.fechaRegistro.desc())
            .all()
        )
    elif tipo_merma == "insumo":
        historial_merma = (
            db.session.query(
                Insumo.nombre,
                Merma.cantidad,
                Merma.motivo,
                Merma.fechaRegistro
            )
            .join(Insumo, Insumo.id == Merma.idInsumo)
            .order_by(Merma.fechaRegistro.desc())
            .all()
        )
    else:
        historial_merma = []

    return render_template(
        "Cocina/cocina.html",
        historial_merma=historial_merma,
        tipo_merma=tipo_merma
    )
