import cv2
import numpy as np
import time
import atexit  # Para liberar la cámara al salir

# Configuración de la cámara (inicializada una vez)
FRAME_WIDTH = 450
FRAME_HEIGHT = 450
MOTION_COLOR = (255, 0, 0)

# Inicializar cámara (global, una sola vez)
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reducir latencia

# Verificar si la cámara se abrió correctamente
if not camera.isOpened():
    raise Exception("Error: No se pudo abrir la cámara. Verifica el índice (0, 1, 2) o permisos.")

# Componentes de procesamiento
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=40, detectShadows=False)

def generate_frames(current_filter):
    prev_time = time.time()
    
    while True:
        success, frame = camera.read()  # Usa la cámara ya inicializada
        if not success:
            print("Error leyendo la cámara")
            break
        
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        # Procesar máscara de movimiento
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3,3)))
        
        # Crear overlay de movimiento
        color_overlay = np.full_like(frame, MOTION_COLOR)
        motion_mask = cv2.bitwise_and(
            color_overlay, 
            cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
        )
        
        # Procesar filtro
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
        
        # Convertir a 3 canales y combinar
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
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + 
                   buffer.tobytes() + b'\r\n')

# Liberar la cámara al cerrar la aplicación
def release_camera():
    if camera.isOpened():
        camera.release()
        print("Cámara liberada correctamente")

atexit.register(release_camera)