from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.forms import LoginForm
from app import db

auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        if current_user.rol == 'admin':
            return redirect(url_for('eventos.admin_index'))
        else:
            return redirect(url_for('eventos.user_index'))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = User.query.filter_by(username=form.username.data).first()
        if usuario and usuario.check_password(form.password.data):
            login_user(usuario)
            flash('Inicio de sesión exitoso', 'success')
            if usuario.rol == 'admin':
                return redirect(url_for('eventos.admin_index'))
            else:
                return redirect(url_for('eventos.user_index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('index.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('auth.index'))

