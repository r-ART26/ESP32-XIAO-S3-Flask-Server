from flask import Flask, render_template
from parte1a.routes import parte1a_bp

app = Flask(__name__)

# Registrar Blueprint
app.register_blueprint(parte1a_bp, url_prefix='/parte1a')

# Ruta raíz (menú principal)
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False)