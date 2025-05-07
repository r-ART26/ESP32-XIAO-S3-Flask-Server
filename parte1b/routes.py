from flask import Blueprint, render_template, Response, request, redirect, url_for
from .processing import generate_frames
from camera_utils import start_camera, stop_camera

parte1b_bp = Blueprint(
    'parte1b', __name__,
    template_folder='templates',
    static_folder='static'
)

NOISE_TYPES = {
    'original': 'Original',
    'gaussian': 'Gaussiano',
    'speckle': 'Speckle'
}

FILTER_TYPES = {
    'gaussian': 'Gaussiano',
    'median': 'Mediana',
    'blur': 'Blur',
    'none': 'Ninguno'
}

EDGE_TYPES = {
    'sobel': 'Sobel',
    'canny': 'Canny',
    'none': 'Ninguno'
}

@parte1b_bp.route('/')
def index():
    return render_template(
        'indexb.html',
        noise_types=NOISE_TYPES,
        filter_types=FILTER_TYPES,
        edge_types=EDGE_TYPES
    )

@parte1b_bp.route('/video_feed')
def video_feed():
    noise_type = request.args.get('noise_type', 'original')
    mean       = float(request.args.get('mean', 0))
    std        = float(request.args.get('std', 0))
    var        = float(request.args.get('var', 0))
    kernel     = int(request.args.get('kernel', 3))
    filter_t   = request.args.get('filter', 'gaussian')
    edge_t     = request.args.get('edge', 'none')

    if noise_type not in NOISE_TYPES:
        noise_type = 'original'
    if filter_t not in FILTER_TYPES:
        filter_t = 'gaussian'
    if edge_t not in EDGE_TYPES:
        edge_t = 'none'

    return Response(
        generate_frames(
            noise_type=noise_type,
            mean=mean,
            std=std,
            var=var,
            kernel_size=kernel,
            filter_type=filter_t,
            edge_type=edge_t
        ),
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
