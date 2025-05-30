from flask import Blueprint, Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from datetime import datetime, timedelta
import base64
from decimal import Decimal
from flask_login import login_user, logout_user, login_required, current_user
from flask import request
from werkzeug.utils import secure_filename
from models.models import (
    db,
    Usuario,
    Insumo,
    Proveedor,
    InsumosProveedor,
    PagoProveedor,
    PedidosCliente,
    Receta,
    RecetaInsumos,
    Galleta,
    Merma,
    PresentacionGalleta,
    VentaLocal,
    EstatusProduccion,
    Produccion

)
from forms import GalletaForm

# hola

cocina_bp = Blueprint('cocina', __name__)


@cocina_bp.route("/cocina")
def cocina():
    galletas = Galleta.query.all()
    presentaciones = PresentacionGalleta.query.all()
    insumos = Insumo.query.all()

    # Obtener alertas de producción
    alertas = db.session.query(
        EstatusProduccion,
        PresentacionGalleta.tipoPresentacion
    ).join(
        PresentacionGalleta, EstatusProduccion.idPresentacion == PresentacionGalleta.id
    ).all()

    # Obtener alertas de "caducidad" basadas en producción
    alertas_caducidad = []
    hoy = datetime.now().date()

    # 1. Obtener todas las producciones recientes (últimos 30 días)
    producciones_recientes = Produccion.query.filter(
        Produccion.fechaProduccion >= hoy - timedelta(days=30))

    # 2. Para cada producción, verificar si está cerca de "caducar" (2 días antes)
    for produccion in producciones_recientes:
        dias_desde_produccion=(hoy - produccion.fechaProduccion).days
        dias_para_alerta=28  # Alertar cuando faltan 2 días para los 30 días de "caducidad"

        if dias_desde_produccion >= dias_para_alerta:
            galleta=Galleta.query.get(produccion.idGalleta)
            if galleta:
                dias_restantes=30 - dias_desde_produccion
                alertas_caducidad.append({
                    'galleta': galleta.nombre,
                    'fecha_produccion': produccion.fechaProduccion,
                    'dias_restantes': dias_restantes,
                    'cantidad': produccion.cantidadProducida
                })

    historial_merma=(
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
    tipos_galletas=[galleta.nombre for galleta in galletas]

    return render_template(
        "Cocina/cocina.html",
        alertas=alertas,
        alertas_caducidad=alertas_caducidad,  # Pasar las alertas al template
        historial_merma=historial_merma,
        tipos_galletas=tipos_galletas,
        insumos=insumos
    )


@ cocina_bp.route("/nueva_galleta", methods=["GET", "POST"])
def nueva_galleta():
    galletas=Galleta.query.all()
    insumos=Insumo.query.all()
    form=GalletaForm()

    if form.validate_on_submit():
        nombre=form.nombre.data
        descripcion=form.descripcion.data
        imagen=form.imagen.data
        insumos_seleccionados=request.form.getlist("insumos")

        if len(insumos_seleccionados) < 6:
            flash("Debes seleccionar al menos 6 insumos", "formulario1_error")
            return render_template("Cocina/nuevaGalleta.html", form=form, insumos=insumos, galletas=galletas)

        if imagen:
            imagen_data=imagen.read()
            imagen_base64=base64.b64encode(imagen_data).decode("utf-8")
        else:
            imagen_base64=None

        nueva_receta=Receta(nombreReceta=nombre,
                            descripcion=descripcion, rutaFoto=imagen_base64)
        db.session.add(nueva_receta)
        db.session.flush()

        for id_insumo in insumos_seleccionados:
            cantidad=request.form.get(f"cantidad_{id_insumo}", type=float)
            unidad=request.form.get(f"unidad_{id_insumo}")

            if cantidad and cantidad > 0:
                insumo=Insumo.query.get(id_insumo)
                cantidad_base=convertir_a_unidad_base(
                    cantidad, unidad, insumo.unidadBase)

                receta_insumo=RecetaInsumos(
                    idReceta=nueva_receta.id,
                    idInsumo=int(id_insumo),
                    cantidadInsumo=cantidad_base,
                    cantidadSeleccionada=cantidad,
                    unidadSeleccionada=unidad
                )
                db.session.add(receta_insumo)

        nueva_galleta=Galleta(nombre=nombre, descripcion=descripcion,
                              idReceta=nueva_receta.id, rutaFoto=imagen_base64)
        db.session.add(nueva_galleta)
        db.session.flush()

        # CÁLCULO ACTUALIZADO PARA 20g POR GALLETA
        costo_total=calcular_costo_total(
            nueva_receta.id)  # Costo para 100 galletas
        costo_por_galleta=costo_total / Decimal('100')

        # Margen de ganancia (50%) + costos indirectos ($0.30 por galleta)
        precio_por_galleta=(costo_por_galleta *
                            Decimal('1.5')) + Decimal('0.30')

        # Presentaciones actualizadas
        presentaciones={
            # 1 galleta (20g)
            "Piezas": precio_por_galleta.quantize(Decimal('0.01')),
            # 100g (5 galletas)
            "Gramos": (precio_por_galleta * Decimal('5')).quantize(Decimal('0.01')),
            # 1kg (50 galletas)
            "1kg": (precio_por_galleta * Decimal('50')).quantize(Decimal('0.01')),
            # 700g (35 galletas)
            "700g": (precio_por_galleta * Decimal('35')).quantize(Decimal('0.01'))
        }

        for tipo, precio_presentacion in presentaciones.items():
            cantidad_presentacion={
                "Piezas": 1,
                "Gramos": 100,
                "1kg": 1000,
                "700g": 700
            }[tipo]

            nueva_presentacion=PresentacionGalleta(
                idGalleta=nueva_galleta.id,
                tipoPresentacion=tipo,
                cantidad=cantidad_presentacion,
                stock=0,
                precio=precio_presentacion,
                fechaCaducidad=datetime.now().date() + timedelta(days=30)
            )
            db.session.add(nueva_presentacion)
            db.session.flush()

            nueva_produccion=EstatusProduccion(
                idGalleta=nueva_galleta.id,
                nombreGalleta=nombre,
                estatus="En preparación",
                tiempoEstimado=30,
                idPresentacion=nueva_presentacion.id
            )
            db.session.add(nueva_produccion)

        db.session.commit()
        flash("Galleta creada correctamente", "formulario1_success")
        return redirect(url_for("cocina.nueva_galleta"))

    return render_template("Cocina/nuevaGalleta.html", form=form, insumos=insumos, galletas=galletas)

def calcular_costo_total(id_receta):
    # 1. Obtener todos los insumos asociados a esta receta
    receta_insumos=RecetaInsumos.query.filter_by(idReceta=id_receta).all()

    costo_total=Decimal('0.0')  # Inicializamos en 0

    # 2. Para cada relación receta-insumo
    for ri in receta_insumos:
        # 3. Obtener el insumo completo de la base de datos
        insumo=Insumo.query.get(ri.idInsumo)

        # 4. Calcular costo de este insumo en la receta:
        # cantidad (convertida a unidad base) × costo por unidad
        costo_total += Decimal(str(ri.cantidadInsumo)) * insumo.costoPorUnidad

    return costo_total

def convertir_a_unidad_base(cantidad, unidad_origen, unidad_destino):
    try:
        print(f"Conversión solicitada: {cantidad} {unidad_origen} → {unidad_destino}")

        # Validación básica
        if not cantidad or not unidad_origen or not unidad_destino:
            flash("Datos de conversión incompletos", "formulario1_error")
            return Decimal('0')

        cantidad = Decimal(str(cantidad))
        
        # Si las unidades son iguales, no hay necesidad de conversión
        if unidad_origen == unidad_destino:
            print("Mismas unidades, retornando cantidad original")
            return cantidad

        # Definición completa de conversiones
        conversiones = {
            'g': {'kg': Decimal('0.001'), 'mg': Decimal('1000')},
            'kg': {'g': Decimal('1000'), 'mg': Decimal('1000000')},
            'mg': {'g': Decimal('0.001'), 'kg': Decimal('0.000001')},
            'l': {'ml': Decimal('1000')},
            'ml': {'l': Decimal('0.001')},
            'docena': {'unidad': Decimal('12')},
            'unidad': {'docena': Decimal('1')/Decimal('12')}
        }

        # Validar unidades
        if unidad_origen not in conversiones:
            flash(f"Unidad de origen '{unidad_origen}' no soportada", "cocina_error")
            return Decimal('0')

        if unidad_destino not in conversiones[unidad_origen]:
            flash(f"No se puede convertir de {unidad_origen} a {unidad_destino}", "cocina_error")
            return Decimal('0')

        resultado = cantidad * conversiones[unidad_origen][unidad_destino]
        print(f"Resultado de conversión: {resultado} {unidad_destino}")
        return resultado

    except Exception as e:
        print(f"Error en conversión: {str(e)}")
        flash(f"Error en conversión de unidades: {str(e)}", "error")
        return Decimal('0')
    
def calcular_costo_total(id_receta):
    receta_insumos=RecetaInsumos.query.filter_by(idReceta=id_receta).all()
    costo_total=Decimal('0.0')  # Inicializar como Decimal

    for ri in receta_insumos:
        insumo=Insumo.query.get(ri.idInsumo)
        # Convertir ambos valores a Decimal antes de operar
        cantidad=Decimal(str(ri.cantidadInsumo))
        costo_por_unidad=insumo.costoPorUnidad  # Ya debería ser Decimal
        costo_total += cantidad * costo_por_unidad

    return costo_total


@ cocina_bp.route("/cambiar_estatus", methods=["POST"])
def cambiar_estatus():
    try:
        id_produccion=request.form.get("id_produccion")
        produccion=EstatusProduccion.query.get(id_produccion)

        if not produccion:
            flash("Producción no encontrada", "cocina_success")
            return redirect(url_for("cocina.cocina"))

        estatus_orden=["En preparacion", "Horneando", "Enfriando"]

        if produccion.estatus in estatus_orden:
            indice_actual=estatus_orden.index(produccion.estatus)

            if indice_actual < len(estatus_orden) - 1:
                # Avanzar al siguiente estado normal
                produccion.estatus=estatus_orden[indice_actual + 1]
                db.session.commit()
                flash(
                    f"Estado cambiado a {produccion.estatus}", "cocina_succes")
            else:
                # Estado final - completar producción
                if not registrar_produccion(produccion.idGalleta, produccion.idPresentacion):
                    raise Exception("Error al registrar producción")

                if not actualizar_stock(produccion.idGalleta, produccion.idPresentacion):
                    raise Exception("Error al actualizar stock")

                db.session.delete(produccion)
                db.session.commit()
                flash("Producción completada correctamente", "cocina_success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error al cambiar estatus: {str(e)}", "cocina_error")
        print(f"Error en cambiar_estatus: {str(e)}")

    return redirect(url_for("cocina.cocina"))

def registrar_produccion(id_galleta, id_presentacion):
    galleta = Galleta.query.get(id_galleta)
    presentacion = PresentacionGalleta.query.get(id_presentacion)

    if not galleta or not presentacion:
        print("Galleta o presentación no encontrada.")
        return False

    # Definir cantidades producidas consistentes
    cantidad_producida = {
        "1kg": 10,      # 10 paquetes de 1kg
        "700g": 14,     # 14 paquetes de 700g
        "Gramos": 100,  # 100 porciones de 100g
        "Piezas": 100   # 100 galletas individuales
    }.get(presentacion.tipoPresentacion, 0)

    if cantidad_producida <= 0:
        print("Tipo de presentación no válido")
        return False

    try:
        nueva_produccion = Produccion(
            idReceta=galleta.idReceta,
            idGalleta=galleta.id, 
            cantidadProducida=cantidad_producida,
            fechaProduccion=datetime.now().date()
        )
        db.session.add(nueva_produccion)
        return True
    except Exception as e:
        print(f"Error al registrar producción: {str(e)}")
        return False

def actualizar_stock(id_galleta, id_presentacion):
    try:
        print(f"Iniciando actualización de stock para galleta {id_galleta}, presentación {id_presentacion}")
        
        presentacion = PresentacionGalleta.query.get(id_presentacion)
        if not presentacion:
            print("Presentación no encontrada")
            return False

        galleta = Galleta.query.get(id_galleta)
        if not galleta:
            print("Galleta no encontrada")
            return False

        receta = Receta.query.get(galleta.idReceta)
        if not receta:
            print("Receta no encontrada")
            return False

        # Definir cantidades consistentes con registrar_produccion()
        if presentacion.tipoPresentacion == "1kg":
            unidades_producidas = 10     # 10 paquetes de 1kg
            incremento_stock = 10        # +10 unidades de 1kg
        elif presentacion.tipoPresentacion == "700g":
            unidades_producidas = 14    # 14 paquetes de 700g
            incremento_stock = 14       # +14 unidades de 700g
        elif presentacion.tipoPresentacion == "Gramos":
            unidades_producidas = 100    # 100 porciones de 100g
            incremento_stock = 10000     # +10000g (100x100g)
        elif presentacion.tipoPresentacion == "Piezas":
            unidades_producidas = 100    # 100 galletas individuales
            incremento_stock = 100       # +100 unidades
        else:
            print("Tipo de presentación no válido")
            return False

        print(f"Unidades a producir: {unidades_producidas}")

        # Verificar y descontar insumos
        receta_insumos = RecetaInsumos.query.filter_by(idReceta=receta.id).all()
        
        for receta_insumo in receta_insumos:
            insumo = Insumo.query.get(receta_insumo.idInsumo)
            if insumo:
                print(f"Procesando insumo: {insumo.nombre}")
                
                # Convertir a unidad base
                cantidad_base = convertir_a_unidad_base(
                    receta_insumo.cantidadSeleccionada,
                    receta_insumo.unidadSeleccionada,
                    insumo.unidadBase
                )
                
                # Calcular cantidad total necesaria
                cantidad_necesaria = cantidad_base * Decimal(unidades_producidas) / Decimal(100)
                print(f"Necesario: {cantidad_necesaria} {insumo.unidadBase} de {insumo.nombre} (Stock actual: {insumo.cantidad})")

                if insumo.cantidad < cantidad_necesaria:
                    print(f"No hay suficiente {insumo.nombre}")
                    return False

        # Descontar insumos
        for receta_insumo in receta_insumos:
            insumo = Insumo.query.get(receta_insumo.idInsumo)
            if insumo:
                cantidad_base = convertir_a_unidad_base(
                    receta_insumo.cantidadSeleccionada,
                    receta_insumo.unidadSeleccionada,
                    insumo.unidadBase
                )
                cantidad_total = cantidad_base * Decimal(unidades_producidas) / Decimal(100)
                insumo.cantidad -= cantidad_total
                print(f"Descontados {cantidad_total} {insumo.unidadBase} de {insumo.nombre}")

        # Actualizar stock de la presentación
        presentacion.stock += incremento_stock
        presentacion.fechaCaducidad = datetime.now().date() + timedelta(days=30)
        print(f"Stock actualizado: {presentacion.tipoPresentacion} ahora tiene {presentacion.stock}")

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error en actualizar_stock: {str(e)}")
        return False

@ cocina_bp.route("/ingresar_merma", methods=["GET", "POST"])
def ingresar_merma():
    galletas=Galleta.query.all()  # Obtener todas las galletas de la base de datos
    insumos=Insumo.query.all()  # Obtener todos los insumos

    alertas=db.session.query(
        EstatusProduccion,
        PresentacionGalleta.tipoPresentacion
    ).join(
        PresentacionGalleta, EstatusProduccion.idPresentacion == PresentacionGalleta.id
    ).all()

    if request.method == "POST":
        tipo_merma=request.form.get("tipo_merma")
        motivo_merma=request.form.get("motivo_merma")

        # Caso de merma de galleta
        if tipo_merma == "galleta":
            tipo_galleta_merma=request.form.get("tipo_galleta_merma")
            cantidad_merma=request.form.get("cantidad_merma_galleta")

            # Verificar si la cantidad_merma no está vacía y es un número válido
            if not cantidad_merma:
                return "La cantidad de merma no puede estar vacía"
            try:
                cantidad_merma=int(cantidad_merma)
            except ValueError:
                return "Valor inválido para la cantidad de merma"

            # Obtener la receta de la galleta seleccionada
            galleta=Galleta.query.filter_by(nombre=tipo_galleta_merma).first()
            if not galleta:
                return "Galleta no encontrada"
            receta=Receta.query.get(galleta.idReceta)

            # Calcular el descuento de insumos basado en la cantidad de galletas
            insumos_receta=RecetaInsumos.query.filter_by(
                idReceta=receta.id).all()
            for receta_insumo in insumos_receta:
                insumo=Insumo.query.get(receta_insumo.idInsumo)
                if insumo:
                    cantidad_a_descartar=receta_insumo.cantidadInsumo * (Decimal(cantidad_merma) / Decimal(100))
                    insumo.cantidad -= cantidad_a_descartar
                    if insumo.cantidad < 0:
                        insumo.cantidad=0

            # Registrar la merma de galleta
            merma=Merma(
                idGalleta=galleta.id,
                cantidad=cantidad_merma,
                motivo=motivo_merma,
                fechaRegistro=datetime.now()
            )
            db.session.add(merma)

        # Caso de merma de insumo
        elif tipo_merma == "insumo":
            id_insumo=request.form.get("id_insumo")
            cantidad_merma=request.form.get("cantidad_merma")

            # Verificar si la cantidad_merma no está vacía y es un número válido
            if not cantidad_merma:
                return "La cantidad de merma no puede estar vacía"
            try:
                cantidad_merma=float(cantidad_merma)
            except ValueError:
                return "Valor inválido para la cantidad de merma"

            # Descontar la cantidad de insumo seleccionado
            if id_insumo and cantidad_merma:
                insumo=Insumo.query.get(id_insumo)
                if insumo:
                    insumo.cantidad -= Decimal(cantidad_merma)
                    if insumo.cantidad < 0:
                        insumo.cantidad=0

                    # Registrar la merma de insumo
                    merma=Merma(
                        idInsumo=insumo.id,
                        cantidad=cantidad_merma,
                        motivo=motivo_merma,
                        fechaRegistro=datetime.now()
                    )
                    db.session.add(merma)

        # Confirmación y redirección
        db.session.commit()
        flash("Merma registrada correctamente", "cocina_success")
        return redirect(url_for("cocina.cocina"))

    return render_template("Cocina/cocina.html", galletas=galletas, insumos=insumos, alertas=alertas)

@ cocina_bp.route("/historial_merma", methods=["GET"])
def historial_merma():
    # Por defecto es 'galleta'
    tipo_merma=request.args.get("tipo_merma", "galleta")
    alertas=db.session.query(
        EstatusProduccion,
        PresentacionGalleta.tipoPresentacion
    ).join(
        PresentacionGalleta, EstatusProduccion.idPresentacion == PresentacionGalleta.id
    ).all()

    if tipo_merma == "galleta":
        historial_merma=(
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
        historial_merma=(
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
        historial_merma=[]

    return render_template(
        "Cocina/cocina.html",
        historial_merma=historial_merma,
        tipo_merma=tipo_merma,
        alertas=alertas
    )


@ cocina_bp.route("/eliminar_galleta/<int:id>", methods=["POST"])
def eliminar_galleta(id):
    try:
        # Iniciar una transacción explícita
        db.session.begin()

        galleta=Galleta.query.get_or_404(id)

        # 1. Obtener todas las presentaciones de esta galleta
        presentaciones=PresentacionGalleta.query.filter_by(idGalleta=id).all()
        presentacion_ids=[p.id for p in presentaciones]

        # 2. Calcular el stock total para registrar merma
        total_galletas=0
        for presentacion in presentaciones:
            if presentacion.tipoPresentacion == "1kg":
                total_galletas += presentacion.stock * 10
            elif presentacion.tipoPresentacion == "700g":
                total_galletas += presentacion.stock * 7
            elif presentacion.tipoPresentacion == "Gramos":
                total_galletas += presentacion.stock / 100
            elif presentacion.tipoPresentacion == "Piezas":
                total_galletas += presentacion.stock

        # 3. Primero eliminar todas las relaciones que dependen de la galleta

        # a) Eliminar ventas locales asociadas a las presentaciones
        VentaLocal.query.filter(
            VentaLocal.id_presentacion.in_(presentacion_ids)).delete()

        # b) Eliminar pedidos de clientes asociados a las presentaciones
        if 'PedidosCliente' in globals():
            PedidosCliente.query.filter(
                PedidosCliente.id_presentacion.in_(presentacion_ids)).delete()

        # c) Eliminar estatus de producción
        EstatusProduccion.query.filter_by(idGalleta=id).delete()

        # d) Eliminar producciones
        Produccion.query.filter_by(idGalleta=id).delete()

        # e) Eliminar presentaciones
        PresentacionGalleta.query.filter_by(idGalleta=id).delete()

        # f) Eliminar mermas asociadas (DEBEMOS HACERLO ANTES de eliminar la galleta)
        Merma.query.filter_by(idGalleta=id).delete()

        # 4. Registrar nueva merma por eliminación si hay stock
        if total_galletas > 0:
            merma=Merma(
                idGalleta=galleta.id,  # Esto es válido porque aún no hemos eliminado la galleta
                cantidad=total_galletas,
                motivo="Eliminación de galleta y su stock",
                fechaRegistro=datetime.now()
            )
            db.session.add(merma)
            # Hacer commit intermedio para asegurar la merma
            db.session.flush()

        # 5. Ahora podemos eliminar la galleta
        db.session.delete(galleta)

        # 6. Verificar si la receta puede ser eliminada (solo si no hay otras galletas que la usen)
        receta=Receta.query.get(galleta.idReceta)
        if receta:
            otras_galletas=Galleta.query.filter(
                Galleta.idReceta == receta.id,
                Galleta.id != id
            ).count()

            if otras_galletas == 0:
                # Eliminar relaciones de receta-insumo
                RecetaInsumos.query.filter_by(idReceta=receta.id).delete()
                # Eliminar la receta
                db.session.delete(receta)

        # Confirmar todos los cambios
        db.session.commit()
        flash("Galleta eliminada correctamente", "formulario1_success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar la galleta: {str(e)}", "formulario1_error")
        print(f"Error en eliminar_galleta: {str(e)}")
        import traceback
        traceback.print_exc()

    return redirect(url_for("cocina.nueva_galleta"))


@ cocina_bp.route("/editar_galleta/<int:id>", methods=["GET", "POST"])
def editar_galleta(id):
    galleta=Galleta.query.get_or_404(id)
    receta=Receta.query.get_or_404(galleta.idReceta)
    insumos=Insumo.query.all()
    receta_insumos=RecetaInsumos.query.filter_by(idReceta=receta.id).all()

    if request.method == "POST":
        try:
            # Validar que se seleccionen al menos 6 insumos
            insumos_seleccionados=request.form.getlist("insumos")
            if len(insumos_seleccionados) < 6:
                flash("Debes seleccionar al menos 6 insumos.", "formulario2_error")
                return redirect(url_for("cocina.editar_galleta", id=galleta.id))

            # Actualizar datos básicos
            galleta.nombre=request.form.get("nombre")
            galleta.descripcion=request.form.get("descripcion")
            receta.nombreReceta=galleta.nombre
            receta.descripcion=galleta.descripcion

            # Manejar imagen
            imagen=request.files.get("imagen")
            if imagen:
                imagen_data=imagen.read()
                galleta.rutaFoto=base64.b64encode(imagen_data).decode("utf-8")
                receta.rutaFoto=galleta.rutaFoto

            # Eliminar insumos no seleccionados
            for ri in receta_insumos:
                if str(ri.idInsumo) not in insumos_seleccionados:
                    db.session.delete(ri)

            # Actualizar o agregar insumos seleccionados
            for id_insumo in insumos_seleccionados:
                cantidad=request.form.get(f"cantidad_{id_insumo}", type=float)
                unidad=request.form.get(f"unidad_{id_insumo}")

                if cantidad and cantidad > 0:
                    insumo=Insumo.query.get(id_insumo)
                    if insumo:
                        # Convertir a unidad base
                        cantidad_base=convertir_a_unidad_base(
                            cantidad, unidad, insumo.unidadBase)

                        # Buscar si ya existe la relación
                        receta_insumo=RecetaInsumos.query.filter_by(
                            idReceta=receta.id,
                            idInsumo=id_insumo
                        ).first()

                        if receta_insumo:
                            # Actualizar existente
                            receta_insumo.cantidadInsumo=cantidad_base
                            receta_insumo.cantidadSeleccionada=cantidad
                            receta_insumo.unidadSeleccionada=unidad
                        else:
                            # Crear nueva relación
                            receta_insumo=RecetaInsumos(
                                idReceta=receta.id,
                                idInsumo=id_insumo,
                                cantidadInsumo=cantidad_base,
                                cantidadSeleccionada=cantidad,
                                unidadSeleccionada=unidad
                            )
                            db.session.add(receta_insumo)

            db.session.commit()
            flash("Galleta actualizada correctamente", "formulario2_success")
            return redirect(url_for("cocina.cocina"))

        except Exception as e:
            db.session.rollback()
            flash(
                f"Error al actualizar galleta: {str(e)}", "formulario2_error")
            print(f"Error en editar_galleta: {str(e)}")

    return render_template(
        "Cocina/editar_galleta.html",
        galleta=galleta,
        insumos=insumos,
        receta_insumos=receta_insumos
    )
    #
