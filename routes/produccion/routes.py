from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, date
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
    VentaLocal,
    EstatusProduccion

)
produccion_bp = Blueprint('produccion', __name__)

@produccion_bp.route("/produccion")
def produccion():
    galletas = Galleta.query.all()
    presentaciones = PresentacionGalleta.query.all()
    
  
    alertas = db.session.query(
        EstatusProduccion,
        PresentacionGalleta.tipoPresentacion
    ).join(
        PresentacionGalleta, EstatusProduccion.idPresentacion == PresentacionGalleta.id
    ).all()

 
    today = date.today()

   
    producciones_hoy = Produccion.query.filter(
        Produccion.fechaProduccion == today
    ).all()

    return render_template(
        "Produccion/inicioProduccion.html", 
        galletas=galletas, 
        presentaciones=presentaciones, 
        alertas=alertas,
        producciones_hoy=producciones_hoy,
        today=today.strftime('%Y-%m-%d')
    )


@produccion_bp.route("/piezas")
def piezas():
    presentaciones = PresentacionGalleta.query.filter_by(tipoPresentacion="piezas").all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="piezas")

@produccion_bp.route("/gramaje")
def gramaje():
    presentaciones = PresentacionGalleta.query.filter_by(tipoPresentacion="gramos").all()
    alertas = db.session.query(
        EstatusProduccion,
        PresentacionGalleta.tipoPresentacion
    ).join(
        PresentacionGalleta, EstatusProduccion.idPresentacion == PresentacionGalleta.id
    ).all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, alertas=alertas, filtro="gramaje")

@produccion_bp.route("/paquete1")
def paquete1():
    presentaciones = PresentacionGalleta.query.filter(PresentacionGalleta.tipoPresentacion.in_(["1kg"])).all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="paquete1")

@produccion_bp.route("/paquete2")
def paquete2():
    presentaciones = PresentacionGalleta.query.filter(PresentacionGalleta.tipoPresentacion.in_(["700g"])).all()
    return render_template("Produccion/inicioProduccion.html", presentaciones=presentaciones, filtro="paquete2")

@produccion_bp.route("/iniciar_produccion/<int:presentacion_id>", methods=["POST"])
def iniciar_produccion(presentacion_id):
    
    presentacion = PresentacionGalleta.query.get_or_404(presentacion_id)
    
   
    galleta = presentacion.galleta

   
    estatus_existente = EstatusProduccion.query.filter_by(idGalleta=galleta.id, idPresentacion=presentacion.id, estatus="En preparacion").first()

    if estatus_existente:
        flash(f"La producción de {galleta.nombre} ({presentacion.tipoPresentacion}) ya está en proceso.", "warning")
    else:
       
        estatus = EstatusProduccion(
            idGalleta=galleta.id,
            nombreGalleta=galleta.nombre,
            estatus="En preparacion",
            tiempoEstimado=30,  
            idPresentacion=presentacion.id 
        )

        db.session.add(estatus)
        db.session.commit()

        flash(f"Producción de {galleta.nombre} ({presentacion.tipoPresentacion}) iniciada con éxito.", "success")
    
    return redirect(url_for('produccion.produccion'))