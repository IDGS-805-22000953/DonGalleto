from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

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
