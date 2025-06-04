from app import create_app, db
from app.models import Evento
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    hoy = datetime.now()
    hace_una_semana = hoy - timedelta(days=7)

    # Buscar eventos rechazados hace más de 7 días (no modificados ni reenviados)
    eventos_a_eliminar = Evento.query.filter(
        Evento.aprobado == False,
        Evento.fecha_fin >= hoy,  # solo si aún no caduca
        Evento.motivo_rechazo != None,
        Evento.fecha_fin <= hace_una_semana
    ).all()

    for evento in eventos_a_eliminar:
        db.session.delete(evento)

    db.session.commit()
    print(f"{len(eventos_a_eliminar)} evento(s) rechazado(s) sin editar eliminados.")
