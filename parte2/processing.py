import cv2
import numpy as np
import os
from pathlib import Path

# Directorio donde están las imágenes médicas
MEDICAL_IMAGES_DIR = os.path.join('static', 'medical_images')

# Tipos de operaciones morfológicas
KERNEL_SIZES = {
    'pequeno': 5,
    'mediano': 15,
    'grande': 37
}

# Cargar nombres de imágenes médicas
def load_medical_images():
    images = {}
    if not os.path.exists(MEDICAL_IMAGES_DIR):
        os.makedirs(MEDICAL_IMAGES_DIR)
        print(f"¡Carpeta creada! Coloca tus imágenes en: {MEDICAL_IMAGES_DIR}")
    for img_file in Path(MEDICAL_IMAGES_DIR).glob('*.*'):
        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            key = img_file.stem
            images[key] = img_file.name
    return images

MEDICAL_IMAGES = load_medical_images()

def apply_morphological_operation(image_key, operation, kernel_size_key):
    # Cargar imagen médica
    image_path = os.path.join(MEDICAL_IMAGES_DIR, MEDICAL_IMAGES.get(image_key, ""))
    if not os.path.exists(image_path):
        # Imagen no encontrada
        placeholder = np.zeros((512, 512), dtype=np.uint8)
        cv2.putText(placeholder, "IMAGEN NO ENCONTRADA", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        _, buffer = cv2.imencode('.jpg', placeholder)
        return buffer.tobytes()

    # Leer imagen en escala de grises
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        placeholder = np.zeros((512, 512), dtype=np.uint8)
        cv2.putText(placeholder, "ERROR AL CARGAR IMAGEN", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        _, buffer = cv2.imencode('.jpg', placeholder)
        return buffer.tobytes()

    # Ajustar tamaño
    image = cv2.resize(image, (400, 400))

    # Aplicar operación morfológica
    kernel_size = KERNEL_SIZES.get(kernel_size_key, 5)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

    if operation == 'erosion':
        result = cv2.erode(image, kernel)
    elif operation == 'dilation':
        result = cv2.dilate(image, kernel)
    elif operation == 'tophat':
        result = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)
    elif operation == 'blackhat':
        result = cv2.morphologyEx(image, cv2.MORPH_BLACKHAT, kernel)
    elif operation == 'enhanced':
        tophat = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)
        blackhat = cv2.morphologyEx(image, cv2.MORPH_BLACKHAT, kernel)
        result = cv2.add(image, cv2.subtract(tophat, blackhat))
    else:
        result = image

    # Normalizar para mejorar visualización
    result = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX)

    # Convertir a color para etiquetas
    image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    result_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    # Combinar imágenes usando NumPy slicing (alternativa a copyTo())
    height, width = image.shape[:2]
    final_combined = np.zeros((height * 2, width, 3), dtype=np.uint8)
    final_combined[:height] = image_bgr
    final_combined[height:2*height] = result_bgr

    # Agregar etiquetas
    cv2.putText(final_combined, f"Original: {image_key}", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    cv2.putText(final_combined, f"Operacion: {operation.upper()}", (10, height + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)


    # Codificar imagen combinada
    _, buffer = cv2.imencode('.jpg', final_combined, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return buffer.tobytes()