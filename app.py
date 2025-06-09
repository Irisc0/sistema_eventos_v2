from app import create_app, db
from flask_migrate import upgrade
from flask import Flask
from datetime import timedelta

app = create_app()

# Configurar Flask-Login para que la sesión se cierre al cerrar el navegador
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=0)

# Forzar creación de tablas si no existen (solo si estás en Render)
with app.app_context():
    try:
        print("Intentando aplicar migraciones...")
        upgrade()
        print("✅ Migraciones aplicadas.")
    except Exception as e:
        print("⚠️ Error aplicando migraciones:", e)
        print("Intentando crear tablas con db.create_all()...")
        db.create_all()
        print("✅ Tablas creadas con create_all().")

if __name__ == '__main__':
    app.run(debug=True)
