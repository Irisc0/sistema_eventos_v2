import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_secreta')
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///eventos.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
