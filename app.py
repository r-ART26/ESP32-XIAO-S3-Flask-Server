from flask import Flask, render_template
from parte1a.routes import parte1a_bp
from parte1b.routes import parte1b_bp
from parte2.routes import parte2_bp
import atexit
import camera_utils

app = Flask(__name__)

# Registrar Blueprints
app.register_blueprint(parte1a_bp, url_prefix='/parte1a')
app.register_blueprint(parte1b_bp, url_prefix='/parte1b')
app.register_blueprint(parte2_bp,   url_prefix='/parte2')

@app.route('/')
def home():
    return render_template('index.html')

# Al salir, detener la cámara centralizada
atexit.register(camera_utils.stop_camera)

if __name__ == '__main__':
    app.run(debug=False)
