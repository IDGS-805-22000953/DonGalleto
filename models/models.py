import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

from flask_login import UserMixin  # Importa UserMixin de Flask-Login


from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido_paterno = db.Column(db.String(50), nullable=False)
    apellido_materno = db.Column(db.String(50))
    correo = db.Column(db.String(120), unique=True, nullable=False)
    contrasenia_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('admin', 'cajero', 'inventario', 'cliente'), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    fecha_contratacion = db.Column(db.Date, nullable=True)
    salario = db.Column(db.Numeric(10, 2), nullable=True)
    fecha_registro = db.Column(db.DateTime, server_default=func.now())

    # Métodos de contraseña
    def set_password(self, password):
        self.contrasenia_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasenia_hash, password)

    # Relaciones CORREGIDAS
    ventas = db.relationship('VentaLocal', back_populates='usuario', lazy=True)
    pedidos_cliente = db.relationship('PedidosCliente', back_populates='usuario', lazy=True)


class Insumo(db.Model):
    __tablename__ = 'insumos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    fechaIngreso = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    fechaCaducidad = db.Column(db.Date, nullable=False)
    cantidad = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)
    unidadBase = db.Column(db.String(20), nullable=False)  # Unidad base (litros, kg, piezas)
    costoPorUnidad = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)  # Costo por unidad base
    descripcion = db.Column(db.Text)
    
    # Relación con Proveedor
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    proveedor = db.relationship('Proveedor', backref='insumos', lazy=True)



class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombreProveedor = db.Column(db.String(50), nullable=False)
    direccion = db.Column(db.String(100))
    correo = db.Column(db.String(50), unique=True, nullable=False)
    telefono = db.Column(db.String(15), nullable=False)

class InsumosProveedor(db.Model):
    __tablename__ = 'insumosProveedor'
    id = db.Column(db.Integer, primary_key=True)
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    idInsumo = db.Column(db.Integer, db.ForeignKey('insumos.id'), nullable=False)
    precio = db.Column(db.Numeric(10, 2))

class PagoProveedor(db.Model):
    __tablename__ = 'pagoProveedor'
    id = db.Column(db.Integer, primary_key=True)
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fechaPago = db.Column(db.DateTime, default=datetime.datetime.now)

class Receta(db.Model):
    __tablename__ = 'recetas'
    id = db.Column(db.Integer, primary_key=True)
    nombreReceta = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    rutaFoto = db.Column(db.Text)
   # cantidadGalletasProducidasPorInsumo = db.Column(db.Integer, nullable=False)


class RecetaInsumos(db.Model):
    __tablename__ = 'recetaInsumos'
    id = db.Column(db.Integer, primary_key=True)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.id'), nullable=False)
    idInsumo = db.Column(db.Integer, db.ForeignKey('insumos.id'), nullable=False)
    cantidadInsumo = db.Column(db.Numeric(10, 2, asdecimal=True), nullable=False)  # Cantidad en la unidad base
    cantidadSeleccionada = db.Column(db.Numeric(10, 2), nullable=False)  # Cantidad en la unidad que eligió el usuario
    unidadSeleccionada = db.Column(db.String(20), nullable=False)  # Unidad que eligió el usuario

class Galleta(db.Model):
    __tablename__ = 'galletas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.id'), nullable=False)
    rutaFoto = db.Column(db.Text)  # Cambiado de LargeBinary a Text

    presentaciones = db.relationship('PresentacionGalleta', backref='galleta', lazy=True)

class PresentacionGalleta(db.Model):
    __tablename__ = 'presentacionesGalletas'
    id = db.Column(db.Integer, primary_key=True)
    idGalleta = db.Column(db.Integer, db.ForeignKey('galletas.id'), nullable=False)
    tipoPresentacion = db.Column(db.Enum('Piezas', 'Gramos', '1kg', '700g'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)  # Cantidad de unidades/gramos según la presentación
    precio = db.Column(db.Numeric(10, 2), nullable=False)  # Precios sugeridos:
        # 'piezas': 5.00 c/u (paquete individual)
        # 'gramos': 0.15 por gramo (para paquetes personalizados)
        # '700g': 105.00 (700g × 0.15)
        # '1kg': 150.00 (1000g × 0.15)
    stock = db.Column(db.Integer, nullable=False)
    fechaCaducidad = db.Column(db.Date, nullable=False)

class Produccion(db.Model):
    __tablename__ = 'produccion'
    id = db.Column(db.Integer, primary_key=True)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.id'), nullable=False)
    idGalleta = db.Column(db.Integer, db.ForeignKey('galletas.id'), nullable=False)  
    cantidadProducida = db.Column(db.Integer, nullable=False)
    fechaProduccion = db.Column(db.Date, default=date.today)

    # Relación con Galleta
    galleta = db.relationship('Galleta', backref='producciones')
    receta = db.relationship('Receta', backref='producciones')


from datetime import datetime

class Merma(db.Model):
    __tablename__ = 'mermas'
    id = db.Column(db.Integer, primary_key=True)
    idGalleta = db.Column(db.Integer, db.ForeignKey('galletas.id'), nullable=True)
    idInsumo = db.Column(db.Integer, db.ForeignKey('insumos.id'), nullable=True)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    fechaRegistro = db.Column(db.DateTime, default=datetime.now)  # Aquí usa datetime.now correctamente

    galleta = db.relationship('Galleta', backref='mermas')
    insumo = db.relationship('Insumo', backref='mermas')



    
class EstatusProduccion(db.Model):
    __tablename__ = 'estatusProduccion'
    id = db.Column(db.Integer, primary_key=True)
    idGalleta = db.Column(db.Integer, db.ForeignKey('galletas.id'), nullable=False)
    nombreGalleta = db.Column(db.String(50), nullable=False)
    estatus = db.Column(db.Enum('En preparacion', 'Horneando', 'Enfriando'), default='En preparacion')
    tiempoEstimado = db.Column(db.Integer, nullable=False)  
    fechaInicio = db.Column(db.DateTime, default=datetime.now)
    idPresentacion = db.Column(db.Integer, db.ForeignKey('presentacionesGalletas.id'), nullable=False)  

    galleta = db.relationship('Galleta', backref='estatusProduccion', lazy=True)
    presentacion = db.relationship('PresentacionGalleta', backref='estatusProduccion', lazy=True) 

from datetime import datetime  # Importación corregida en la parte superior

class VentaLocal(db.Model):
    __tablename__ = 'ventaslocal'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_presentacion = db.Column(db.Integer, db.ForeignKey('presentacionesGalletas.id'), nullable=False)
    cantidadcomprado = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    fechaCompra = db.Column(db.DateTime, default=datetime.now)  # Corregido aquí
    
    usuario = db.relationship('Usuario', back_populates='ventas')
    presentacion = db.relationship('PresentacionGalleta', backref='ventas_locales')
    
class PedidosCliente(db.Model):
    __tablename__ = 'pedidoscliente'  # Nombre corregido
    
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_presentacion = db.Column(db.Integer, db.ForeignKey('presentacionesGalletas.id'), nullable=False)
    cantidadcomprado = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    fechaPedido = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    fechaRecogida = db.Column(db.DateTime)
    estatus = db.Column(db.Enum('pendiente', 'completado', 'cancelado'), nullable=False, default='pendiente')
    
    # Relaciones CORREGIDAS
    usuario = db.relationship('Usuario', back_populates='pedidos_cliente')
    presentacion = db.relationship('PresentacionGalleta', backref='pedidos_clientes')
    
    class CorteCaja(db.Model):
        __tablename__ = 'cortes_caja'
        id = db.Column(db.Integer, primary_key=True)
        mes = db.Column(db.String(7), nullable=False)  # formato YYYY-MM
        ingreso_total = db.Column(db.Numeric(10, 2), nullable=False)
        egresos_total = db.Column(db.Numeric(10, 2), nullable=False)
        monto_mermas = db.Column(db.Numeric(10, 2), nullable=False)
        caja_reportada = db.Column(db.Numeric(10, 2), nullable=False)  # lo que el usuario ingresó manualmente
        utilidad = db.Column(db.Numeric(10, 2), nullable=False)
        fecha_creacion = db.Column(db.DateTime, default=datetime.now)
