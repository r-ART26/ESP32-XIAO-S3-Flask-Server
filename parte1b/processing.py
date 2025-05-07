#processing.py 1.b
import cv2
import numpy as np
import time
import atexit
import requests
from threading import Thread

# Configuración reducida para ahorro de recursos
FRAME_WIDTH = 240
FRAME_HEIGHT = 180
camera = None
is_camera_active = False


IP   = "192.168.89.181"
PORT = 81
PATH = "/stream"
URL  = f"http://{IP}:{PORT}{PATH}"

# Variables globales para stream manual
frame_buffer = None
stream_active = False
camera_thread = None


# def start_camera():
#     global camera, is_camera_active
#     if not is_camera_active:
#         camera = cv2.VideoCapture(0)
#         camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
#         camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
#         camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#         is_camera_active = camera.isOpened()
#         print(f"Cámara iniciada: {is_camera_active}")

# def stop_camera():
#     global camera, is_camera_active
#     if camera and is_camera_active:
#         camera.release()
#         is_camera_active = False
#         print("Cámara detenida")
def fetch_stream():
    global frame_buffer, stream_active
    stream_active = True
    bytes_data = b''
    with requests.get(URL, stream=True) as r:
        for chunk in r.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # Inicio de JPEG
            b = bytes_data.find(b'\xff\xd9')  # Fin de JPEG
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                if len(jpg) > 100:  # Evitar buffers muy pequeños
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        frame_buffer = frame


def start_camera():
    global is_camera_active, camera_thread, stream_active
    if not is_camera_active:
        stream_active = True
        camera_thread = Thread(target=fetch_stream, daemon=True)
        camera_thread.start()
        is_camera_active = True
        print("Cámara iniciada (modo manual)")

def stop_camera():
    global is_camera_active, stream_active, frame_buffer
    is_camera_active = False
    stream_active = False
    frame_buffer = None
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
    global is_camera_active, frame_buffer
    while True:
        if not is_camera_active or frame_buffer is None:
            # Placeholder con 3 filas
            placeholder = np.zeros((FRAME_HEIGHT * 3, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(placeholder, "CAMARA DESACTIVADA", (20, FRAME_HEIGHT + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + 
                  cv2.imencode('.jpg', placeholder)[1].tobytes() + b'\r\n')
            time.sleep(0.2)
            continue

        frame = frame_buffer.copy()
        if frame is None or frame.size == 0:
            time.sleep(0.1)
            continue

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Aplicar ruido
        if noise_type == 'gaussian':
            noise = np.random.normal(mean, std, frame.shape).astype(np.float32)
            frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        elif noise_type == 'speckle':
            noise = np.random.randn(*frame.shape) * var
            frame = np.clip(frame.astype(np.float32) * (1 + noise), 0, 255).astype(np.uint8)

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        filtered_image = apply_filter(gray_frame, filter_type, kernel_size)
        edge_image = apply_edge_detection(filtered_image, edge_type)

        height, width = gray_frame.shape[:2]
        final_combined = np.zeros((height * 3, width, 3), dtype=np.uint8)

        final_combined[:height] = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)
        final_combined[height:2*height] = cv2.cvtColor(filtered_image, cv2.COLOR_GRAY2BGR)
        final_combined[2*height:3*height] = edge_image

        # Agregar etiquetas
        cv2.putText(final_combined, "Original", (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(final_combined, f"Filtro: {filter_type}", (10, height + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(final_combined, f"Borde: {edge_type}", (10, 2*height + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        ret, buffer = cv2.imencode('.jpg', final_combined, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ret:
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# Liberar recursos al salir
def release_camera():
    global camera
    if camera and camera.isOpened():
        camera.release()
        print("Cámara liberada")

atexit.register(release_camera)