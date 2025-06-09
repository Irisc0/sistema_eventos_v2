from app import create_app, db
from flask_migrate import upgrade
from datetime import timedelta

app = create_app()

# Ejecutar migraciones automáticamente al arrancar en Render
with app.app_context():
    upgrade()

# Configurar duración de sesión
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=0)

if __name__ == '__main__':
    app.run(debug=True)
