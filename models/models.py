from flask_sqlalchemy import SQLAlchemy
import datetime
from datetime import date


db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombreUsuario = db.Column(db.String(50), nullable=False)
    apellidoPa = db.Column(db.String(50), nullable=False)
    apellidoMa = db.Column(db.String(50))
    correo = db.Column(db.String(50), unique=True, nullable=False)
    contrasenia = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('admin', 'empleado'), nullable=False)
    fechaRegistro = db.Column(db.Date, default=datetime.date.today)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellidoPa = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(50), unique=True, nullable=False)
    contrasenia = db.Column(db.String(255), nullable=False)
    fechaRegistro = db.Column(db.Date, default=datetime.date.today)

class Insumo(db.Model):
    __tablename__ = 'insumos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    fechaIngreso = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    fechaCaducidad = db.Column(db.Date, nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    unidadMedida = db.Column(db.String(20))
    presentacion = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    porcentajeMerma = db.Column(db.Numeric(5, 2), nullable=False)

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
    rutaFoto = db.Column(db.String(255))

class RecetaInsumos(db.Model):
    __tablename__ = 'recetaInsumos'
    id = db.Column(db.Integer, primary_key=True)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.id'), nullable=False)
    idInsumo = db.Column(db.Integer, db.ForeignKey('insumos.id'), nullable=False)
    cantidadInsumo = db.Column(db.Numeric(10, 2), nullable=False)

class Galleta(db.Model):
    __tablename__ = 'galletas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.id'), nullable=False)
    rutaFoto = db.Column(db.String(255))

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

class Merma(db.Model):
    __tablename__ = 'merma'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Enum('insumo', 'galleta'), nullable=False)
    idInsumo = db.Column(db.Integer, db.ForeignKey('insumos.id'))
    idGalleta = db.Column(db.Integer, db.ForeignKey('galletas.id'))
    cantidad = db.Column(db.Numeric(10, 2))
    motivo = db.Column(db.Text, nullable=False)
    fechaRegistro = db.Column(db.Date, default=datetime.date.today)

    galleta = db.relationship('Galleta', backref='mermas')
    insumo = db.relationship('Insumo', backref='mermas')

class VentaLocal(db.Model):
    __tablename__ = 'ventaslocal'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_presentacion = db.Column(db.Integer, db.ForeignKey('presentacionesGalletas.id'), nullable=False)
    cantidadcomprado = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    fechaCompra = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    usuario = db.relationship('Usuario', backref='ventas_local')
    presentacion = db.relationship('PresentacionGalleta', backref='ventas_local')

class PedidosCliente(db.Model):
    __tablename__ = 'pedidoscliente'
    id = db.Column(db.Integer, primary_key=True)
    idCliente = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    id_presentacion = db.Column(db.Integer, db.ForeignKey('presentacionesGalletas.id'), nullable=False)
    cantidadcomprado = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    fechaPedido = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    fechaRecogida = db.Column(db.DateTime)
    estatus = db.Column(db.Enum('pendiente', 'completado', 'cancelado'), nullable=False, default='pendiente')

    cliente = db.relationship('Cliente', backref='pedidos')
    presentacion = db.relationship('PresentacionGalleta', backref='pedidos')

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    fechacompra = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    total = db.Column(db.Numeric(10, 2), nullable=False)

    usuario = db.relationship('Usuario', backref='ventas')
    cliente = db.relationship('Cliente', backref='ventas')

    
class EstatusProduccion(db.Model):
    __tablename__ = 'estatusProduccion'
    id = db.Column(db.Integer, primary_key=True)
    idGalleta = db.Column(db.Integer, db.ForeignKey('galletas.id'), nullable=False)
    nombreGalleta = db.Column(db.String(50), nullable=False)
    estatus = db.Column(db.Enum('En preparacion', 'Horneando', 'Enfriando'), default='En preparacion')
    tiempoEstimado = db.Column(db.Integer, nullable=False)  
    fechaInicio = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    idPresentacion = db.Column(db.Integer, db.ForeignKey('presentacionesGalletas.id'), nullable=False)  

    galleta = db.relationship('Galleta', backref='estatusProduccion', lazy=True)
    presentacion = db.relationship('PresentacionGalleta', backref='estatusProduccion', lazy=True)