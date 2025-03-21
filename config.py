import os
from sqlalchemy import create_engine
import urllib

class Config(object):
    SECRET_KEY = 'Clave nueva'
    SESSION_COOKIE_SECURE = False

class DevelopmentConfig(Config):
    DEBUG = True  
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Dna77669@127.0.0.1/DonGalletooon'  # Corregido: AQLALCHEMY_DATABASE_URL -> SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False