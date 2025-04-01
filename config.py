import os
import secrets
from sqlalchemy import create_engine
import urllib

class Config(object):
    SECRET_KEY = secrets.token_hex(16)  # Clave secreta segura generada aleatoriamente
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:tokis@127.0.0.1/DonGalletoFlask'
    SQLALCHEMY_TRACK_MODIFICATIONS = False