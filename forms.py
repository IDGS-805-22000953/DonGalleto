from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, DateField, TextAreaField, SelectField, IntegerField, DecimalField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from wtforms.widgets import NumberInput
from flask_wtf.file import FileRequired, FileAllowed
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models.models import Usuario




class GalletaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
                         DataRequired(), Length(min=2, max=100)])
    descripcion = TextAreaField('Descripción', validators=[
                                DataRequired(), Length(min=10, max=500)])
    rutaFoto = StringField('Ruta de la Imagen', validators=[Length(max=255)])

    submit = SubmitField('Guardar')

class ProveedorForm(FlaskForm):
    nombreProveedor = StringField('Nombre del Proveedor', validators=[DataRequired(), Length(max=50)])
    direccion = StringField('Dirección', validators=[Length(max=100)])
    correo = StringField('Correo Electrónico', validators=[DataRequired(), Length(max=50), Email()])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(max=15)])
    submit = SubmitField('Guardar')
    
class PresentacionForm(FlaskForm):
    tipoPresentacion = SelectField('Tipo de Presentación', choices=[('Piezas', 'Piezas'), (
        '1kg', '1kg'), ('700g', '700g'), ('Gramos', 'Gramos')], validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[
                         DataRequired(), NumberRange(min=0)])
    precio = DecimalField('Precio', validators=[
                          DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Agregar Presentación')


class AgregarAlCarritoForm(FlaskForm):
    galleta_id = IntegerField('Galleta ID', validators=[DataRequired()])
    presentacion_id = IntegerField(
        'Presentación ID', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired()])
    submit = SubmitField('Agregar al carrito')


class RegistrationForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    username = StringField('Nombre', validators=[DataRequired(), Length(max=50)])
    apellidoPa = StringField('Apellido Paterno', validators=[DataRequired(), Length(max=50)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Registrarme')


class LoginForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')


class RawMaterialForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=50)])
    expiration_date = DateField(
        'Fecha de Caducidad', format='%Y-%m-%d', validators=[DataRequired()])
    quantity = DecimalField('Cantidad', validators=[
                            DataRequired(), NumberRange(min=0)])
    unit = StringField('Unidad', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Descripción', validators=[Length(max=200)])
    provider = StringField('Proveedor', validators=[Length(max=50)])
    percentage_waste = DecimalField('Porcentaje de Merma', validators=[
                                    DataRequired(), NumberRange(min=0, max=100)])
    # Agrega este campo
    presentation = StringField('Presentación', validators=[Length(max=50)])
    submit = SubmitField('Guardar')


class GalletaForm(FlaskForm):
    nombre = StringField('Nombre de la Receta', 
                        validators=[
                            DataRequired(message="El nombre es requerido"),
                            Length(min=2, max=100, message="El nombre debe tener entre 2 y 100 caracteres")
                        ])
    
    descripcion = TextAreaField('Descripción', 
                              validators=[
                                  DataRequired(message="La descripción es requerida"),
                                  Length(min=10, max=500, message="La descripción debe tener entre 10 y 500 caracteres")
                              ])
    
    imagen = FileField('Imagen de la Galleta', validators=[FileRequired(message="La imagen es requerida")])

    
    submit = SubmitField('Crear Galleta')


class InsumoForm(FlaskForm):
    cantidad = DecimalField('Cantidad',
                            widget=NumberInput(step="0.01"),
                            validators=[DataRequired(message="La cantidad es requerida"),
                                        NumberRange(min=0.01, message="La cantidad debe ser mayor a 0")])

    unidad = SelectField('Unidad',
                         choices=[('kg', 'kg'), ('g', 'g'), ('mg', 'mg'),
                                  ('litros', 'litros'), ('ml', 'ml'),
                                  ('docena', 'docena'), ('unidad', 'unidad')],
                         validators=[DataRequired(message="La unidad es requerida")])


class EditarGalletaForm(FlaskForm):
    nombre = StringField("Nombre de la Receta", validators=[DataRequired()])
    descripcion = TextAreaField("Descripción", validators=[DataRequired()])
    # Puedes agregar un campo para los insumos de manera similar si quieres usar un formulario de insumos
    imagen = FileField("Imagen", validators=[FileAllowed(['jpg', 'png', 'gif'])])  # Si lo manejas aquí
    

class MermaForm(FlaskForm):
    tipo_merma = SelectField('Tipo de Merma', 
                           choices=[('galleta', 'Galleta'), ('insumo', 'Insumo')],
                           validators=[DataRequired()])
    
    id_insumo = SelectField('Insumo', 
                          coerce=int,
                          validators=[])
    
    tipo_galleta_merma = SelectField('Tipo de Galleta',
                                   validators=[])
    
    cantidad_merma = DecimalField('Cantidad',
                                widget=NumberInput(step="0.01"),
                                validators=[NumberRange(min=0.01)])
    
    cantidad_merma_galleta = IntegerField('Cantidad de Galletas',
                                        validators=[NumberRange(min=1)])
    
    motivo_merma = TextAreaField('Motivo',
                               validators=[DataRequired()])
    
    submit = SubmitField('Registrar Merma')
    

class CorteMensualForm(FlaskForm):
    fecha = DateField('Fecha del Corte', validators=[DataRequired()])
    mes = DateField('Mes del Corte', format='%Y-%m', validators=[DataRequired()])
    submit = SubmitField('Generar Corte')
    


class RegistroEmpleadoForm(FlaskForm):
    nombreUsuario = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])
    
    apellidoPa = StringField('Apellido Paterno', validators=[
        DataRequired(message='El apellido paterno es requerido'),
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])
    
    apellidoMa = StringField('Apellido Materno', validators=[
        Length(max=50, message='El apellido no puede exceder 50 caracteres')
    ])
    
    correo = StringField('Correo Electrónico', validators=[
        DataRequired(message='El correo electrónico es requerido'),
        Email(message='Ingrese un correo electrónico válido'),
        Length(max=50, message='El correo no puede exceder 50 caracteres')
    ])
    
    contrasenia = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida'),
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    
    confirmar_contrasenia = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Por favor confirme su contraseña'),
        EqualTo('contrasenia', message='Las contraseñas no coinciden')
    ])
    
    rol = SelectField('Rol', choices=[
        ('admin', 'Administrador'),
        ('cajero', 'Cajero'),
        ('inventario', 'Inventario'),
        ('produccion', 'Producción')
    ], validators=[DataRequired(message='Seleccione un rol')])
    
    submit = SubmitField('Registrar Empleado')
    
    def validate_correo(self, field):
        # Excluir el correo actual cuando se está editando
        if hasattr(self, 'obj') and self.obj.correo == field.data:
            return
            
        if Usuario.query.filter_by(correo=field.data).first():
            raise ValidationError('Este correo electrónico ya está registrado. Por favor use otro.')
