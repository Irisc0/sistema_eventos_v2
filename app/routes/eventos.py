from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
import os
import re
from flask_login import login_required, current_user
from app.models import Evento, User
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask import make_response
from datetime import timedelta
from babel.dates import format_date
from calendar import monthrange 
from flask import request, redirect, url_for, render_template, flash, jsonify, make_response
import pdfkit
import shutil
import platform

# Configurar wkhtmltopdf dependiendo del sistema
if platform.system() == "Windows":
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
else:
    config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')  # Ruta por defecto en Render/Linux


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

@eventos.route('/admin')
@login_required
def admin_index():
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

    evento.nombre = request.form['nombre']
    evento.lugar = request.form['lugar']
    evento.responsable = request.form['responsable']
    evento.descripcion = request.form['descripcion']
    evento.fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%dT%H:%M')
    evento.fecha_fin = datetime.strptime(request.form['fecha_fin'], '%Y-%m-%dT%H:%M')

    evento.participantes = int(request.form.get('participantes')) if request.form.get('participantes') else None
    evento.genero = request.form.get('genero')
    evento.tipo_evento = request.form.get('tipo_evento')

    if evento.tipo_evento == "Interno":
        evento.organizacion = request.form.get('organizacion')
    elif evento.tipo_evento == "Externo":
        evento.organizacion = request.form.get('organizacion_texto')

    if evento.fecha_fin < evento.fecha_inicio:
        flash("La fecha y hora de fin no puede ser anterior a la de inicio.", "danger")
        return redirect(url_for('eventos.user_index'))

    conflicto = Evento.query.filter(
        Evento.id != evento.id,
        Evento.aprobado == True,
        Evento.lugar == evento.lugar,
        Evento.fecha_fin >= evento.fecha_inicio,
        Evento.fecha_inicio <= evento.fecha_fin
    ).first()

    if conflicto:
        flash(f"Error: El lugar '{evento.lugar}' ya está reservado del {conflicto.fecha_inicio.strftime('%d/%m/%Y')} al {conflicto.fecha_fin.strftime('%d/%m/%Y')}.", "danger")
        return redirect(url_for('eventos.user_index'))

    evento.aprobado = None
    evento.motivo_rechazo = None

    db.session.commit()
    flash("Evento editado y reenviado para revisión.", "info")
    return redirect(url_for('eventos.user_index'))

import os
import glob

@eventos.route('/eliminar_evento/<int:evento_id>', methods=['POST'])
@login_required
def eliminar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    # Validar que el evento pertenezca al usuario o sea admin
    if not current_user.es_admin() and evento.usuario_id != current_user.id:
        flash("No tienes permiso para eliminar este evento.", "danger")
        return redirect(url_for('eventos.user_index'))

    # Borrar imágenes asociadas
    nombre_limpio = evento.nombre.lower().replace(' ', '_')
    patron = os.path.join('app', 'static', 'uploads', f'evento_{nombre_limpio}_*')
    imagenes = glob.glob(patron)

    for ruta in imagenes:
        try:
            os.remove(ruta)
        except Exception as e:
            print(f"No se pudo eliminar la imagen {ruta}: {e}")

    # Eliminar el evento
    db.session.delete(evento)
    db.session.commit()
    flash("Evento y sus imágenes eliminados correctamente.", "success")

    return redirect(url_for('eventos.admin_index' if current_user.es_admin() else 'eventos.user_index'))


@eventos.route('/get_events')
def get_events():
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
                'responsable': evento.responsable,
                'participantes': evento.participantes,
                'genero': evento.genero,
                'tipo_evento': evento.tipo_evento,
                'organizacion': evento.organizacion,
                'solicitado_por': evento.usuario.username if evento.usuario else 'Desconocido'
            }
        })
    return jsonify(data)


@eventos.route('/inicio')
@login_required
def user_index():
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

    participantes = request.form.get('participantes')
    genero = request.form.get('genero')
    tipo_evento = request.form.get('tipo_evento')

    if tipo_evento == "Interno":
        organizacion = request.form.get('organizacion')  # de la lista
    elif tipo_evento == "Externo":
        organizacion = request.form.get('organizacion_texto')  # texto libre
    else:
        organizacion = None

    if fecha_fin < fecha_inicio:
        flash("La fecha y hora de fin no puede ser anterior a la de inicio.", "danger")
        return redirect(url_for('eventos.user_index'))

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
        participantes=int(participantes) if participantes else None,
        genero=genero,
        tipo_evento=tipo_evento,
        organizacion=organizacion,
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


from flask import current_app, request  

@eventos.route('/reporte_mes/<int:year>/<int:month>')
@login_required
def reporte_mes(year, month):
    start = datetime(year, month, 1)
    end = datetime(year, month, monthrange(year, month)[1], 23, 59)

    eventos = Evento.query.filter(
        Evento.aprobado == True,
        Evento.fecha_inicio >= start,
        Evento.fecha_inicio <= end
    ).order_by(Evento.fecha_inicio).all()

    if not eventos:
        flash("No hay eventos en este mes.", "warning")
        return redirect(url_for('eventos.admin_index' if current_user.rol == 'admin' else 'eventos.user_index'))

    titulo = f"Eventos de {format_date(start, format='MMMM yyyy', locale='es_ES')}"

    uploads_path = os.path.join(current_app.root_path, 'static', 'uploads')
    archivos = []

    if os.path.exists(uploads_path):
        for archivo in os.listdir(uploads_path):
            archivos.append(archivo)

    html = render_template(
        "reporte_pdf.html",
        eventos=eventos,
        titulo=titulo,
        archivos=archivos,
        timedelta=timedelta,
        format_date=format_date,
    )

    pdf = pdfkit.from_string(html, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=reporte_mes_{month}_{year}.pdf'
    return response

@eventos.route('/reporte_trimestre_rango/<int:anio_inicio>/<int:mes_inicio>')
@login_required
def reporte_trimestre_rango(anio_inicio, mes_inicio):
    start = datetime(anio_inicio, mes_inicio, 1)

    mes_fin = mes_inicio + 2
    anio_fin = anio_inicio
    if mes_fin > 12:
        mes_fin -= 12
        anio_fin += 1

    end = datetime(anio_fin, mes_fin, monthrange(anio_fin, mes_fin)[1], 23, 59)

    eventos = Evento.query.filter(
        Evento.aprobado == True,
        Evento.fecha_inicio >= start,
        Evento.fecha_inicio <= end
    ).order_by(Evento.fecha_inicio).all()

    if not eventos:
        flash("No hay eventos en este trimestre dinámico.", "warning")
        return redirect(url_for('eventos.admin_index' if current_user.rol == 'admin' else 'eventos.user_index'))

    titulo = f"Eventos de {format_date(start, format='MMMM', locale='es_ES').capitalize()} a {format_date(end, format='MMMM', locale='es_ES').capitalize()} de {end.year}"

    uploads_path = os.path.join(current_app.root_path, 'static', 'uploads')
    archivos = os.listdir(uploads_path) if os.path.exists(uploads_path) else []

    html = render_template(
        "reporte_pdf.html",
        eventos=eventos,
        titulo=titulo,
        archivos=archivos,
        timedelta=timedelta,
        format_date=format_date,
        es_trimestral=True
    )
    pdf = pdfkit.from_string(html, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=reporte_trimestre_custom.pdf'
    return response

@eventos.route('/subir_imagenes/<int:evento_id>', methods=['POST'])
@login_required
def subir_imagenes(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    if evento.usuario_id != current_user.id or not evento.aprobado:
        flash("No puedes subir imágenes para este evento.", "danger")
        return redirect(url_for('eventos.user_index'))

    archivos = request.files.getlist('imagenes')
    if not archivos or archivos[0].filename == '':
        flash("No se seleccionó ninguna imagen.", "warning")
        return redirect(url_for('eventos.user_index'))

    extensiones_permitidas = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    rutas_guardadas = []

    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    nombre_base = limpiar_nombre(evento.nombre)
    
    # Buscar cuántas imágenes ya existen con este nombre base
    archivos_existentes = [
        f for f in os.listdir(uploads_dir)
        if f.startswith(f"evento_{nombre_base}_")
    ]
    contador_inicial = len(archivos_existentes) + 1

    for i, archivo in enumerate(archivos, start=contador_inicial):
        if archivo and '.' in archivo.filename:
            extension = archivo.filename.rsplit('.', 1)[-1].lower()
            if extension not in extensiones_permitidas:
                continue

            nombre_archivo = f"evento_{nombre_base}_{i}.{extension}"
            ruta_completa = os.path.join(uploads_dir, nombre_archivo)
            archivo.save(ruta_completa)

            rutas_guardadas.append(f"static/uploads/{nombre_archivo}")

    if rutas_guardadas:
        evento.imagen = rutas_guardadas[-1]  # Última subida como principal
        db.session.commit()
        flash(f"Se subieron {len(rutas_guardadas)} imagen(es) correctamente.", "success")
    else:
        flash("No se subió ninguna imagen válida.", "warning")

    return redirect(url_for('eventos.user_index'))

@eventos.route('/eliminar_eventos_mes/<int:year>/<int:month>', methods=['POST'])
@login_required
def eliminar_eventos_mes(year, month):
    if not current_user.es_admin():
        flash("No tienes permisos para realizar esta acción.", "danger")
        return redirect(url_for('eventos.admin_index'))

    start = datetime(year, month, 1)
    end = datetime(year, month, monthrange(year, month)[1], 23, 59)

    eventos_a_borrar = Evento.query.filter(
        Evento.fecha_inicio >= start,
        Evento.fecha_inicio <= end
    ).all()

    count = len(eventos_a_borrar)
    for evento in eventos_a_borrar:
        db.session.delete(evento)

    db.session.commit()

    flash(f"Se eliminaron {count} evento(s) del mes seleccionado.", "success")
    return redirect(url_for('eventos.admin_index'))
