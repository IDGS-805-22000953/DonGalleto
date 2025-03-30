from flask import Blueprint,Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from datetime import datetime
import base64
from flask import request
from werkzeug.utils import secure_filename
from models.models import (
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
    Venta,
    Merma,
    PresentacionGalleta,
    VentaLocal

)



cocina_bp = Blueprint('cocina', __name__)


@cocina_bp.route("/cocina")
def cocina():
    galletas = Galleta.query.all()
    presentaciones = PresentacionGalleta.query.all()
    
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

    return render_template(
        "Cocina/cocina.html",
        alertas=alertas,  
        historial_merma=historial_merma
    )

@cocina_bp.route("/nueva")
def nueva():
    insumos = Insumo.query.all()

    return render_template("Cocina/nuevaGalleta.html", insumos=insumos)

@cocina_bp.route("/nueva_galleta", methods=["GET", "POST"])
def nueva_galleta():
    insumos = Insumo.query.all()

    if request.method == "POST":
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        insumos_seleccionados = request.form.getlist("insumos")  
        imagen = request.files.get("imagen")

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

        
        tipos_presentacion = ["Piezas", "Gramos", "1kg", "700g"]
        for tipo in tipos_presentacion:
            presentacion_existente = PresentacionGalleta.query.filter_by(idGalleta=nueva_galleta.id, tipoPresentacion=tipo).first()
            if not presentacion_existente:
                 
                stock_inicial = 100 if tipo == "Piezas" else 0
                nueva_presentacion = PresentacionGalleta(
                    idGalleta=nueva_galleta.id,
                    tipoPresentacion=tipo,
                    cantidad=0, 
                    stock=stock_inicial,  
                    precio=0, 
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

    
    insumos_receta = RecetaInsumos.query.filter_by(idReceta=receta.id).all()

   
    if presentacion.tipoPresentacion == "1kg":
        presentacion.stock += 10  # 10 paquetes de 1kg
    elif presentacion.tipoPresentacion == "700g":
        presentacion.stock += 14  # 14 paquetes de 700g
       
        gramaje = PresentacionGalleta.query.filter_by(tipoPresentacion="Gramos", idGalleta=id_galleta).first()
        if gramaje:
            gramaje.stock += 200
    elif presentacion.tipoPresentacion == "Gramos":
        presentacion.stock += 10000  # 10000g (100 galletas)
    elif presentacion.tipoPresentacion == "Piezas":
        presentacion.stock += 100  # 100 piezas

    
    db.session.commit()
