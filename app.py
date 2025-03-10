from flask import Flask, render_template, request, redirect, url_for
from flask import flash
from flask_wtf.csrf import CSRFProtect
from flask import g
from config import DevelopmentConfig

from models import db


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf=CSRFProtect()


@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

@app.route("/")
@app.route("/central")
def central():
	return render_template("Central/inicioCentral.html")

@app.route("/")
@app.route("/cliente")
def cliente():
	return render_template("Cliente/inicioCliente.html")

@app.errorhandler(404)
def page_not_found(e):
        return render_template('404.html'), 404

@app.route('/cliente/pedidos')
def modificar():
    # create_form=forms.UserForm2(request.form)
    # if request.method == "GET":
    #     id = request.args.get('id')
    #     alum1 = db.session.query(Alumnos).filter(Alumnos.id == id).first()
    #     create_form.nombre.data=alum1.nombre
    #     create_form.apaterno.data=alum1.apaterno
    #     create_form.email.data=alum1.email
    # if request.method == "POST":
    #     id = create_form.id.data
    #     id = request.args.get('id')
    #     alum1 = db.session.query(Alumnos).filter(Alumnos.id == id).first()
    #     alum1.nombre = create_form.nombre.data
    #     alum1.apaterno = create_form.apaterno.data
    #     alum1.email = create_form.email.data
    #     db.session.commit()
    #     return redirect(url_for('index'))
    return render_template("Cliente/pedidos.html")        

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run()