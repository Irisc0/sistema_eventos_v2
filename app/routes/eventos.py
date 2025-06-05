from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Evento, User
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask import make_response
from datetime import timedelta
from calendar import monthrange
from flask import request, redirect, url_for, render_template, flash, jsonify, make_response
import pdfkit
import shutil
import platform

eventos = Blueprint('eventos', __name__)

# Lista de lugares reusables
LUGARES = [
    "34 - A, Jefatura DAE",
    "34 - B, Salones Cultural",
    "34 - C, Dojo, Área de Pesas, Leoncio y Coordinación Cívica",
    "31 - Coordinación Cultural",
    "38 - Cuarto de Maq. / Coordinación deportiva / Baños H y M",
    "39 - Oficina Deportivo",
    "92 - Almacén de Equipo de Beisbol",
    "98 - A, Pista de Atletismo",
    "98 - B, Cancha Futbol Sintético",
    "99 - 1, Cancha 1, Canchas de Tenis",
    "99 - 2, Cancha 2, Canchas de Tenis",
    "100 - 1, Cancha 1, Domo - Canchas Deportivas Mixtas",
    "100 - 2, Cancha 2, Domo - Canchas Deportivas Mixtas",
    "100 - 3, Cancha 3, Domo - Canchas Deportivas Mixtas",
    "100 - 4, Cancha 4, Domo - Canchas Deportivas Mixtas",
    "100 - 5, Cancha 5, Domo - Canchas Deportivas Mixtas",
    "100 - 6, Cancha 6, Domo - Canchas Deportivas Mixtas",
    "101 - Alberca",
    "102 - Voleibol Playero",
    "103 - Campo de Beisbol",
    "104 - Gimnasio (Cancha de Basquetbol y Voleibol)",
    "105 - Campo de Softbol",
    "106 - Cancha 1, Canchas de Futbol",
    "106 - Cancha 2, Canchas de Futbol",
    "106 - Cancha 3, Canchas de Futbol",
    "106 - Cancha 4, Canchas de Futbol",
    "107 - Canchas de Futbol Rápido",
    "DAE - Cancha 1, Cancha de Basquetbol cerrada",
    "DAE - Cancha 2, Cancha de Basquetbol y Voleibol",
    "DAE - Cancha 3, Cancha de Basquetbol y Voleibol",
    "DAE - Cancha 4, Cancha de Basquetbol y Voleibol",
    "DAE - Salón - Salones Cultural",
    "108 - Mesas de Ping Pong - NO HABILITADO"
]

# Eliminar eventos pasados
def eliminar_eventos_vencidos():
    hoy = datetime.now()
    eventos_pasados = Evento.query.filter(Evento.fecha_fin < hoy).all()
    for evento in eventos_pasados:
        db.session.delete(evento)
    db.session.commit()

@eventos.route('/admin')
@login_required
def admin_index():
    eliminar_eventos_vencidos()
    eventos_pendientes = Evento.query.filter(Evento.aprobado == None).all()
    return render_template('admin_index.html', eventos=eventos_pendientes, lugares=LUGARES)

@eventos.route('/aprobar/<int:evento_id>')
@login_required
def aprobar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    evento.aprobado = True
    evento.motivo_rechazo = None
    db.session.commit()
    flash(f'Evento "{evento.nombre}" aprobado.', 'success')
    return redirect(url_for('eventos.admin_index'))

@eventos.route('/rechazar/<int:evento_id>', methods=['POST'])
@login_required
def rechazar_evento(evento_id):
    motivo = request.form.get('motivo_rechazo')
    if not motivo:
        flash("Debes ingresar un motivo para el rechazo.", "danger")
        return redirect(url_for('eventos.admin_index'))

    evento = Evento.query.get_or_404(evento_id)
    evento.aprobado = False
    evento.motivo_rechazo = motivo
    db.session.commit()
    flash(f'Evento "{evento.nombre}" rechazado.', 'warning')
    return redirect(url_for('eventos.admin_index'))

@eventos.route('/editar_evento/<int:evento_id>', methods=['POST'])
@login_required
def editar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    nuevo_nombre = request.form['nombre']
    nuevo_lugar = request.form['lugar']
    nueva_descripcion = request.form['descripcion']
    nuevo_responsable = request.form['responsable']
    nueva_fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%dT%H:%M')
    nueva_fecha_fin = datetime.strptime(request.form['fecha_fin'], '%Y-%m-%dT%H:%M')

    if nueva_fecha_fin < nueva_fecha_inicio:
        flash("La fecha y hora de fin no puede ser anterior a la de inicio.", "danger")
        return redirect(url_for('eventos.user_index'))

    conflicto = Evento.query.filter(
        Evento.id != evento.id,
        Evento.aprobado == True,
        Evento.lugar == nuevo_lugar,
        Evento.fecha_fin >= nueva_fecha_inicio,
        Evento.fecha_inicio <= nueva_fecha_fin
    ).first()

    if conflicto:
        flash(f"Error: El lugar '{nuevo_lugar}' ya está reservado del {conflicto.fecha_inicio.strftime('%d/%m/%Y')} al {conflicto.fecha_fin.strftime('%d/%m/%Y')}.", "danger")
        return redirect(url_for('eventos.user_index'))

    evento.nombre = nuevo_nombre
    evento.lugar = nuevo_lugar
    evento.descripcion = nueva_descripcion
    evento.responsable = nuevo_responsable
    evento.fecha_inicio = nueva_fecha_inicio
    evento.fecha_fin = nueva_fecha_fin
    evento.aprobado = None
    evento.motivo_rechazo = None

    db.session.commit()
    flash("Evento editado y reenviado para revisión.", "info")
    return redirect(url_for('eventos.user_index'))

@eventos.route('/eliminar_evento/<int:evento_id>', methods=['POST'])
@login_required
def eliminar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    db.session.delete(evento)
    db.session.commit()
    flash("Evento eliminado correctamente.", "success")
    return redirect(url_for('eventos.user_index'))

@eventos.route('/get_events')
def get_events():
    eliminar_eventos_vencidos()
    eventos_aprobados = Evento.query.filter_by(aprobado=True).all()
    data = []
    for evento in eventos_aprobados:
        data.append({
            "id": evento.id,
            'title': evento.nombre,
            'start': evento.fecha_inicio.isoformat(),
            'end': evento.fecha_fin.isoformat(),
            'extendedProps': {
                'descripcion': evento.descripcion,
                'lugar': evento.lugar,
                'responsable': evento.responsable
            }
        })
    return jsonify(data)

@eventos.route('/inicio')
@login_required
def user_index():
    eliminar_eventos_vencidos()
    eventos_usuario = Evento.query.filter_by(usuario_id=current_user.id).all()
    return render_template('index_users.html', eventos_usuario=eventos_usuario, lugares=LUGARES)

@eventos.route('/solicitar_evento', methods=['POST'])
@login_required
def solicitar_evento():
    nombre = request.form['nombre']
    lugar = request.form['lugar']
    responsable = request.form['responsable']
    descripcion = request.form['descripcion']
    fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%dT%H:%M')
    fecha_fin = datetime.strptime(request.form['fecha_fin'], '%Y-%m-%dT%H:%M')

    if fecha_fin < fecha_inicio:
        flash("La fecha y hora de fin no puede ser anterior a la de inicio.", "danger")
        return redirect(url_for('eventos.user_index'))

    # Verificar conflictos con eventos ya aprobados en el mismo lugar y horario
    conflicto = Evento.query.filter(
        Evento.aprobado == True,
        Evento.lugar == lugar,
        Evento.fecha_fin >= fecha_inicio,
        Evento.fecha_inicio <= fecha_fin
    ).first()

    if conflicto:
        flash(f"Error: El lugar '{lugar}' ya está reservado del {conflicto.fecha_inicio.strftime('%d/%m/%Y %H:%M')} al {conflicto.fecha_fin.strftime('%d/%m/%Y %H:%M')}.", "danger")
        return redirect(url_for('eventos.user_index'))

    nuevo_evento = Evento(
        nombre=nombre,
        lugar=lugar,
        responsable=responsable,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        descripcion=descripcion,
        aprobado=None,
        usuario_id=current_user.id
    )
    db.session.add(nuevo_evento)
    db.session.commit()
    flash("Solicitud enviada correctamente.", "success")
    return redirect(url_for('eventos.admin_index' if current_user.rol == 'admin' else 'eventos.user_index'))

@eventos.route('/verificar_admin', methods=['GET', 'POST'])
@login_required
def verificar_admin():
    if current_user.rol != 'admin':
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for('eventos.admin_index'))

    if request.method == 'POST':
        clave = request.form.get('clave_segura')
        if clave == 'R2487t{ON;':  
            return redirect(url_for('eventos.gestion_usuarios'))
        else:
            flash("Clave incorrecta.", "danger")
    
    return render_template('verificar_admin.html')

@eventos.route('/gestion_usuarios', methods=['GET', 'POST'])
@login_required
def gestion_usuarios():
    if current_user.rol != 'admin':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('eventos.admin_index'))

    usuarios = User.query.all()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        rol = request.form.get('rol')

        if not all([username, password, rol]):
            flash("Todos los campos son obligatorios.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("El nombre de usuario ya existe.", "danger")
        else:
            nuevo_usuario = User(
                username=username,
                password_hash=generate_password_hash(password),
                rol=rol
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash("Usuario creado exitosamente.", "success")
            return redirect(url_for('eventos.gestion_usuarios'))

    return render_template('gestion_usuarios.html', usuarios=usuarios)

# Editar rol  de usuario
@eventos.route('/editar_usuario/<int:user_id>', methods=['POST'])
@login_required
def editar_usuario(user_id):
    if current_user.rol != 'admin':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('eventos.admin_index'))

    nuevo_rol = request.form.get('nuevo_rol')
    usuario = User.query.get_or_404(user_id)

    if usuario.id == current_user.id:
        flash("No puedes cambiar tu propio rol.", "warning")
        return redirect(url_for('eventos.gestion_usuarios'))

    usuario.rol = nuevo_rol
    db.session.commit()
    flash(f"Rol de usuario '{usuario.username}' actualizado a '{nuevo_rol}'.", "success")
    return redirect(url_for('eventos.gestion_usuarios'))

# Eliminar usuario
@eventos.route('/eliminar_usuario/<int:user_id>', methods=['POST'])
@login_required
def eliminar_usuario(user_id):
    if current_user.rol != 'admin':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('eventos.admin_index'))

    usuario = User.query.get_or_404(user_id)

    if usuario.id == current_user.id:
        flash("No puedes eliminar tu propia cuenta.", "warning")
        return redirect(url_for('eventos.gestion_usuarios'))

    db.session.delete(usuario)
    db.session.commit()
    flash(f"Usuario '{usuario.username}' eliminado.", "info")
    return redirect(url_for('eventos.gestion_usuarios'))

@eventos.route('/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.rol != 'admin':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('eventos.admin_index'))

    usuario = User.query.get_or_404(user_id)
    nueva_password = request.form.get('nueva_password')

    if not nueva_password or len(nueva_password) < 4:
        flash("La nueva contraseña debe tener al menos 4 caracteres.", "warning")
        return redirect(url_for('eventos.gestion_usuarios'))

    usuario.password_hash = generate_password_hash(nueva_password)
    db.session.commit()
    flash(f"Contraseña de usuario '{usuario.username}' actualizada.", "success")
    return redirect(url_for('eventos.gestion_usuarios'))


@eventos.route('/reporte_mes/<int:year>/<int:month>')
@login_required
def reporte_mes(year, month):
    try:
        import locale
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except:
        pass

    start = datetime(year, month, 1)
    end_day = monthrange(year, month)[1]
    end = datetime(year, month, end_day, 23, 59)

    eventos = Evento.query.filter(
        Evento.aprobado == True,
        Evento.fecha_inicio >= start,
        Evento.fecha_inicio <= end
    ).order_by(Evento.fecha_inicio.asc()).all()

    if not eventos:
        flash("No hay eventos en este mes.", "warning")
        return redirect(url_for('eventos.admin_index' if current_user.rol == 'admin' else 'eventos.user_index'))

    titulo = f"Eventos de {start.strftime('%B de %Y')}"
    html = render_template("reporte_pdf.html", eventos=eventos, titulo=titulo)

    # Detectar sistema y configurar ruta de wkhtmltopdf
    if platform.system() == "Windows":
        path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    else:
        path_wkhtmltopdf = "/usr/bin/wkhtmltopdf"  # en Render/Linux

    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    pdf = pdfkit.from_string(html, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=reporte_mes_{month}_{year}.pdf'
    return response