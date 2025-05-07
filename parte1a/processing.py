#prosessing.py 1.a
import cv2
import numpy as np
import time
import atexit  # Para liberar la cámara al salir
import requests
from threading import Thread

# Configuración de la cámara (inicializada una vez)
FRAME_WIDTH = 450
FRAME_HEIGHT = 450
MOTION_COLOR = (255, 0, 0)
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

# Componentes de procesamiento
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=40, detectShadows=False)

# def start_camera():
#     global camera, is_camera_active
#     if not is_camera_active:
#         #camera = cv2.VideoCapture(0)
        
#         # camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
#         # camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
#         # camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#         # is_camera_active = camera.isOpened()
#         # print(f"Cámara iniciada: {is_camera_active}")
        
#         camera = cv2.VideoCapture(URL, cv2.CAP_FFMPEG)
#         # camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
#         # camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
#         # camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# def start_camera():
#     global camera, is_camera_active
#     if not is_camera_active:
#         for backend in [cv2.CAP_FFMPEG, cv2.CAP_DSHOW, cv2.CAP_GSTREAMER]:
#             camera = cv2.VideoCapture(URL, backend)
#             if camera.isOpened():
#                 print(f"Cámara iniciada con backend {backend}")
#                 is_camera_active = True
#                 return
#         print("No se pudo abrir el stream desde la ESP32-CAM")

#         is_camera_active = True
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

def generate_frames(current_filter):
    global is_camera_active, frame_buffer
    prev_time = time.time()

    while True:
        if not is_camera_active or frame_buffer is None:
            placeholder = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(placeholder, "CAMARA DESACTIVADA", 
                       (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', placeholder)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.1)
            continue

        frame = frame_buffer.copy()

        # Redimensionar
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Procesar máscara de movimiento
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3,3)))

        # Overlay de movimiento
        color_overlay = np.full_like(frame, MOTION_COLOR)
        motion_mask = cv2.bitwise_and(
            color_overlay, 
            cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
        )

        # Filtro seleccionado
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if current_filter == 'histeq':
            processed = cv2.equalizeHist(gray)
        elif current_filter == 'clahe':
            processed = clahe.apply(gray)
        elif current_filter == 'gamma':
            gamma = 1.5
            lookUpTable = np.empty((1,256), np.uint8)
            for i in range(256):
                lookUpTable[0,i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
            processed = cv2.LUT(gray, lookUpTable)
        else:
            processed = gray

        processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        combined = np.hstack((processed, motion_mask))

        # Mostrar FPS
        current_time = time.time()
        fps = 1 / (current_time - prev_time)
        prev_time = current_time
        cv2.putText(combined, f"FPS: {int(fps)}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Codificar frame
        ret, buffer = cv2.imencode('.jpg', combined)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# Liberar la cámara al cerrar la aplicación
def release_camera():
    global camera
    if camera is not None and camera.isOpened():
        camera.release()
        print("Cámara liberada correctamente")

# def generate_motion_frames():
#     global is_camera_active, frame_buffer
#     while True:
#         if not is_camera_active or frame_buffer is None:
#             placeholder = np.zeros((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8)
#             cv2.putText(placeholder, "CAMARA DESACTIVADA", 
#                        (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100), 2)
#             ret, buffer = cv2.imencode('.jpg', placeholder)
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
#             time.sleep(0.1)
#             continue

#         frame = frame_buffer.copy()

#         # Procesar máscara de movimiento
#         fg_mask = bg_subtractor.apply(frame)
#         fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3)))

#         ret, buffer = cv2.imencode('.jpg', fg_mask)
#         if ret:
#             yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
atexit.register(release_camera)