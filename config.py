import os
from sqlalchemy import create_engine
import urllib

class Config(object):
    SECRET_KEY = 'Clave nueva'
    SESSION_COOKIE_SECURE = False

class DevelopmentConfig(Config):
    DEBUG = True  
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:Dna77669@database-1.cqbgcuwuw6wt.us-east-1.rds.amazonaws.com/DonGalletoFlask'  # Corregido: AQLALCHEMY_DATABASE_URL -> SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False