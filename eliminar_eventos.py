from app import create_app, db
from app.models import Evento
from datetime import datetime

app = create_app()

with app.app_context():
    hoy = datetime.now()
    eventos_vencidos = Evento.query.filter(Evento.fecha_fin < hoy).all()
    for evento in eventos_vencidos:
        db.session.delete(evento)
    db.session.commit()
    print(f"{len(eventos_vencidos)} evento(s) vencido(s) eliminado(s).")
