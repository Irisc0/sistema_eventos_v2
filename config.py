import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_secreta')
    
    # Usar PostgreSQL si está definida la variable de entorno DATABASE_URL (como en Render)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'instance', 'eventos.db')
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

