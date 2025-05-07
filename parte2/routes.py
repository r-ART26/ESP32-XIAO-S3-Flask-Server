from flask import Blueprint, render_template, Response, request
from .processing import apply_morphological_operation

# Blueprint para parte2
parte2_bp = Blueprint('parte2', __name__,
                      template_folder='templates',
                      static_folder='static')

# Opciones para el formulario
IMAGE_OPTIONS = {
    'radiografia': 'Radiografía',
    'angio': 'Angiografía',
    'tac': 'TAC'
}
OPERATION_OPTIONS = {
    'none': 'Original',
    'erosion': 'Erosión',
    'dilation': 'Dilatación',
    'tophat': 'Top Hat',
    'blackhat': 'Black Hat',
    'enhanced': 'Original + (Top Hat - Black Hat)'
}
KERNEL_OPTIONS = {
    'pequeno': 'Pequeño (5x5)',
    'mediano': 'Mediano (15x15)',
    'grande': 'Grande (37x37)'
}

@parte2_bp.route('/')
def index():
    return render_template('indexc.html',
                           images=IMAGE_OPTIONS,
                           operations=OPERATION_OPTIONS,
                           kernels=KERNEL_OPTIONS)

@parte2_bp.route('/image_feed')
def image_feed():
    # Leer parámetros desde URL
    image_key = request.args.get('image', 'radiografia')
    operation = request.args.get('operation', 'none')
    kernel_size = request.args.get('kernel', 'grande')

    # Validar parámetros
    if image_key not in IMAGE_OPTIONS:
        image_key = 'radiografia'
    if operation not in OPERATION_OPTIONS:
        operation = 'none'
    if kernel_size not in KERNEL_OPTIONS:
        kernel_size = 'grande'

    # Generar imagen procesada
    image_bytes = apply_morphological_operation(image_key, operation, kernel_size)
    return Response(image_bytes, mimetype='image/jpeg')