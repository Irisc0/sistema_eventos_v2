from app import create_app, db
from flask_migrate import upgrade
from datetime import timedelta
import os

app = create_app()

# Ejecutar migraciones en Render si es necesario
with app.app_context():
    try:
        upgrade()
    except Exception as e:
        print("⚠️ Migraciones fallaron, intentando crear las tablas manualmente...")
        db.create_all()
        print("✅ Tablas creadas con db.create_all()")

app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=0)

if __name__ == '__main__':
    app.run(debug=True)
