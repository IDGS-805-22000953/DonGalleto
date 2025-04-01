from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, DateField, TextAreaField, SelectField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Email,Length, NumberRange

class GalletaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    descripcion = TextAreaField('Descripción', validators=[DataRequired(), Length(min=10, max=500)])
    rutaFoto = StringField('Ruta de la Imagen', validators=[Length(max=255)])
    submit = SubmitField('Guardar')

class PresentacionForm(FlaskForm):
    tipoPresentacion = SelectField('Tipo de Presentación', choices=[('Piezas', 'Piezas'), ('1kg', '1kg'), ('700g', '700g'), ('Gramos', 'Gramos')], validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    precio = DecimalField('Precio', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Agregar Presentación')

class AgregarAlCarritoForm(FlaskForm):
    galleta_id = IntegerField('Galleta ID', validators=[DataRequired()])
    presentacion_id = IntegerField('Presentación ID', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired()])
    submit = SubmitField('Agregar al carrito')

class RegistrationForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(max=50)])
    apellidoPa = StringField('Apellido Paterno', validators=[DataRequired(), Length(max=50)])
    apellidoMa = StringField('Apellido Materno', validators=[Length(max=50)])  # Opcional
    password = PasswordField('Contraseña', validators=[DataRequired()])
    rol = SelectField('Rol', choices=[('admin', 'Administrador'), ('cliente', 'Cliente')], validators=[DataRequired()])
    submit = SubmitField('Registrarme')

class LoginForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')


class RawMaterialForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=50)])
    expiration_date = DateField('Fecha de Caducidad', format='%Y-%m-%d', validators=[DataRequired()])
    quantity = DecimalField('Cantidad', validators=[DataRequired(), NumberRange(min=0)])
    unit = StringField('Unidad', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Descripción', validators=[Length(max=200)])
    provider = StringField('Proveedor', validators=[Length(max=50)])
    percentage_waste = DecimalField('Porcentaje de Merma', validators=[DataRequired(), NumberRange(min=0, max=100)])
    # Agrega este campo
    presentation = StringField('Presentación', validators=[Length(max=50)])
    submit = SubmitField('Guardar')