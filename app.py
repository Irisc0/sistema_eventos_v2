from app import create_app, db
from flask import Flask
from datetime import timedelta

app = create_app()

# Configurar Flask-Login para que la sesión se cierre al cerrar el navegador
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=0)

# Forzar creación de tablas en cualquier entorno
with app.app_context():
    try:
        print("⏳ Intentando crear las tablas directamente...")
        db.create_all()
        print("✅ Tablas creadas correctamente.")
    except Exception as e:
        print("❌ Error creando las tablas:", e)

if __name__ == '__main__':
    app.run(debug=True)
