from app import create_app
from flask import Flask
from datetime import timedelta

app = create_app()

# Configurar Flask-Login para que la sesión se cierre al cerrar el navegador
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(seconds=0)

if __name__ == '__main__':
    app.run(debug=True)