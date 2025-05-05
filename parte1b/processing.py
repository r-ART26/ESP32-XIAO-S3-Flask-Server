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

def generate_frames(noise_type='original', mean=0.0, std=0.0, var=0.0):
    global is_camera_active
    while True:
        if not is_camera_active or not camera.isOpened():
            placeholder = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(placeholder, "CAMARA DESACTIVADA", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + 
                  cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes() + b'\r\n')
            time.sleep(0.2)
            continue
        
        success, frame = camera.read()
        if not success:
            break
        
        # Aplicar ruido según tipo seleccionado
        if noise_type == 'gaussian':
            noise = np.random.normal(mean, std, frame.shape).astype(np.float32)
            frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        elif noise_type == 'speckle':
            noise = np.random.randn(*frame.shape) * var
            frame = np.clip(frame.astype(np.float32) * (1 + noise), 0, 255).astype(np.uint8)
        # Si es 'original', no se aplica ruido

        # Codificar y enviar frame
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ret:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# Liberar recursos al salir
def release_camera():
    global camera
    if camera and camera.isOpened():
        camera.release()
        print("Cámara liberada")

atexit.register(release_camera)