from app import create_app, db
from flask_migrate import upgrade
from datetime import timedelta

app = create_app()

# Ejecuta upgrade para aplicar migraciones automáticamente
with app.app_context():
    upgrade()

# Opcional: duración de sesión
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=0)

if __name__ == '__main__':
    app.run(debug=True)
