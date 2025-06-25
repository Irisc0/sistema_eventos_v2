from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(10), nullable=False)

    eventos = db.relationship('Evento', backref='usuario', lazy=True)

    def es_admin(self):
        return self.rol == 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    lugar = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    responsable = db.Column(db.String(100), nullable=True)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)

    participantes = db.Column(db.Integer, nullable=True)
    genero = db.Column(db.String(10), nullable=True)  # "Femenil", "Varonil", "Mixto"
    tipo_evento = db.Column(db.String(10), nullable=True)  # "Interno", "Externo"
    organizacion = db.Column(db.String(100), nullable=True)  # Departamento o externo
    imagen = db.Column(db.String(255), nullable=True)  # Ruta de imagen

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', name='fk_evento_usuario'),
        nullable=False
    )

    aprobado = db.Column(db.Boolean, default=None)
    motivo_rechazo = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Evento {self.id}: {self.nombre} | Usuario: {self.usuario.username} | {'Aprobado' if self.aprobado else 'Pendiente'}>"
