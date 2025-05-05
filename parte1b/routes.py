from flask import Blueprint, render_template, Response, request, redirect, url_for
from .processing import generate_frames, start_camera, stop_camera

# Blueprint para parte1b
parte1b_bp = Blueprint('parte1b', __name__, 
                      template_folder='templates',
                      static_folder='static')

NOISE_TYPES = {
    'original': 'Original',
    'gaussian': 'Gaussiano',
    'speckle': 'Speckle'
}

@parte1b_bp.route('/')
def index():
    return render_template('indexb.html', noise_types=NOISE_TYPES)

@parte1b_bp.route('/video_feed')
def video_feed():
    # Leer parámetros desde URL
    noise_type = request.args.get('noise_type', 'original')
    mean = float(request.args.get('mean', 0))
    std = float(request.args.get('std', 0))
    var = float(request.args.get('var', 0))

    # Validar que el tipo de ruido sea válido
    if noise_type not in NOISE_TYPES:
        noise_type = 'original'

    return Response(
        generate_frames(noise_type=noise_type, mean=mean, std=std, var=var),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@parte1b_bp.route('/start_camera')
def start_camera_route():
    start_camera()
    return redirect(url_for('parte1b.index'))

@parte1b_bp.route('/stop_camera')
def stop_camera_route():
    stop_camera()
    return redirect(url_for('parte1b.index'))