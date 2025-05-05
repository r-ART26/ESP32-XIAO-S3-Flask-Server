from flask import Blueprint, render_template, Response, request, redirect, url_for
from .processing import generate_frames, start_camera, stop_camera

# Blueprint para parte1b
parte1b_bp = Blueprint('parte1b', __name__, 
                      template_folder='templates',
                      static_folder='static')

@parte1b_bp.route('/')
def index():
    return render_template('indexb.html')

@parte1b_bp.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
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