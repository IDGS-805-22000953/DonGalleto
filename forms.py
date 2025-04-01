from wtforms import Form
from flask_wtf import FlaskForm
 
from wtforms import StringField,IntegerField
from wtforms import EmailField
from wtforms import validators

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, DateField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange
from models.models import Usuario  # Asegúrate de importar 'Usuario', no 'User'

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length

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
 
