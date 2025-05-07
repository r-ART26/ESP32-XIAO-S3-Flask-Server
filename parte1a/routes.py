from flask import Blueprint, render_template, Response, request, redirect, url_for
from .processing import generate_frames
from camera_utils import start_camera, stop_camera

parte1a_bp = Blueprint(
    'parte1a', __name__,
    template_folder='templates',
    static_folder='static'
)

FILTERS = {
    'gray': 'Escala de Grises',
    'histeq': 'Ecualización Histograma',
    'clahe': 'CLAHE',
    'gamma': 'Corrección Gamma'
}

@parte1a_bp.route('/')
def index():
    active_filter = request.args.get('filter', 'gray')
    return render_template(
        'indexa.html',
        filters=FILTERS,
        active_filter=active_filter
    )

@parte1a_bp.route('/video_feed')
def video_feed():
    current_filter = request.args.get('filter', 'gray')
    if current_filter not in FILTERS:
        current_filter = 'gray'
    return Response(
        generate_frames(current_filter),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@parte1a_bp.route('/start_camera')
def start_camera_route():
    start_camera()
    return redirect(url_for('parte1a.index'))

@parte1a_bp.route('/stop_camera')
def stop_camera_route():
    stop_camera()
    return redirect(url_for('parte1a.index'))
