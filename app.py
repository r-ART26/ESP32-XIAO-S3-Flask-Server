from flask import Flask, render_template
from parte1a.routes import parte1a_bp
from parte1b.routes import parte1b_bp
from parte2.routes import parte2_bp
from camera_utils import stop_camera
import atexit

app = Flask(__name__)

# Registrar Blueprint
app.register_blueprint(parte1a_bp, url_prefix='/parte1a')
app.register_blueprint(parte1b_bp, url_prefix='/parte1b')
app.register_blueprint(parte2_bp, url_prefix='/parte2')

# Ruta raíz (menú principal)
@app.route('/')
def home():
    return render_template('index.html')


# Liberar cámara al salir
atexit.register(stop_camera)

if __name__ == '__main__':
    app.run(debug=False)