#routes.py 1.a
from flask import Blueprint, render_template, Response, request, redirect, url_for
from .processing import generate_frames, start_camera, stop_camera, is_camera_active
# from .processing import generate_motion_frames

parte1a_bp = Blueprint('parte1a', __name__, 
                      template_folder='templates',
                      static_folder='static')

FILTERS = {
    'gray': 'Escala de Grises',
    'histeq': 'Ecualización Histograma',
    'clahe': 'CLAHE',
    'gamma': 'Corrección Gamma'
}


@parte1a_bp.route('/')
def index():
    active_filter = request.args.get('filter', 'gray')  # Filtro inicial
    return render_template('indexa.html', 
                           filters=FILTERS,
                           active_filter=active_filter)

@parte1a_bp.route('/video_feed')
def video_feed():
    current_filter = request.args.get('filter', 'gray')  # Consistente con el template
    print("Filtro aplicado:", current_filter)
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

# @parte1a_bp.route('/motion_feed')
# def motion_feed():
#     return Response(
#         generate_motion_frames(),
#         mimetype='multipart/x-mixed-replace; boundary=frame'
#     )
