import cv2
import numpy as np
import time
import atexit

# Configuración reducida para ahorro de recursos
FRAME_WIDTH = 240
FRAME_HEIGHT = 180
camera = None
is_camera_active = False

def start_camera():
    global camera, is_camera_active
    if not is_camera_active:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        is_camera_active = camera.isOpened()
        print(f"Cámara iniciada: {is_camera_active}")

def stop_camera():
    global camera, is_camera_active
    if camera and is_camera_active:
        camera.release()
        is_camera_active = False
        print("Cámara detenida")

def apply_filter(image, filter_type, kernel_size):
    # Aplicar solo el filtro seleccionado
    if filter_type == 'gaussian':
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    elif filter_type == 'median':
        return cv2.medianBlur(image, kernel_size)
    elif filter_type == 'blur':
        return cv2.blur(image, (kernel_size, kernel_size))
    return image  # 'none'

def apply_edge_detection(image, edge_type):
    # Aplicar solo el algoritmo de bordes seleccionado
    if edge_type == 'sobel':
        sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        edge = cv2.magnitude(sobel_x, sobel_y)
        edge = np.uint8(255 * edge / np.max(edge))
        return cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
    elif edge_type == 'canny':
        v = np.median(image)
        sigma = 0.33
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        edge = cv2.Canny(image, lower, upper)
        return cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
    # 'none'
    return np.zeros_like(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR))

def generate_frames(noise_type='original', mean=0.0, std=0.0, var=0.0, 
                   kernel_size=3, filter_type='gaussian', edge_type='none'):
    global is_camera_active
    while True:
        if not is_camera_active or not camera.isOpened():
            # Placeholder con 3 filas (cada una de 240x180)
            placeholder = np.zeros((FRAME_HEIGHT * 3, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(placeholder, "CAMARA DESACTIVADA", (20, FRAME_HEIGHT + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + 
                  cv2.imencode('.jpg', placeholder)[1].tobytes() + b'\r\n')
            time.sleep(0.2)
            continue
        
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Aplicar ruido si es necesario
        if noise_type == 'gaussian':
            noise = np.random.normal(mean, std, frame.shape).astype(np.float32)
            frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        elif noise_type == 'speckle':
            noise = np.random.randn(*frame.shape) * var
            frame = np.clip(frame.astype(np.float32) * (1 + noise), 0, 255).astype(np.uint8)

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Aplicar filtro seleccionado
        filtered_image = apply_filter(gray_frame, filter_type, kernel_size)

        # Aplicar detección de bordes seleccionada
        edge_image = apply_edge_detection(filtered_image, edge_type)

        # Crear imagen final combinada (3 filas de 240x180)
        height, width = gray_frame.shape[:2]
        final_combined = np.zeros((height * 3, width, 3), dtype=np.uint8)

        # Fila 1: Imagen original en escala de grises
        final_combined[:height] = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

        # Fila 2: Filtro seleccionado
        final_combined[height:2*height] = cv2.cvtColor(filtered_image, cv2.COLOR_GRAY2BGR)

        # Fila 3: Detección de bordes seleccionada
        final_combined[2*height:3*height] = edge_image

        # Agregar etiquetas
        cv2.putText(final_combined, "Original", (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(final_combined, f"Filtro: {filter_type}", (10, height + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(final_combined, f"Borde: {edge_type}", (10, 2*height + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        # Codificar y enviar frame
        ret, buffer = cv2.imencode('.jpg', final_combined, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ret:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# Liberar recursos al salir
def release_camera():
    global camera
    if camera and camera.isOpened():
        camera.release()
        print("Cámara liberada")

atexit.register(release_camera)