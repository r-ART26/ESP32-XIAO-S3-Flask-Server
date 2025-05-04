import cv2
from flask import Flask, Response, render_template, request
import numpy as np
import time

app = Flask(__name__)

# Configuración de filtros
FILTERS = {
    'gray': 'Escala de Grises',
    'histeq': 'Ecualización Histograma',
    'clahe': 'CLAHE',
    'gamma': 'Corrección Gamma'
}
current_filter = 'gray' 

# Parámetros
FRAME_WIDTH = 450   
FRAME_HEIGHT = 450
MOTION_COLOR = (0, 255, 0)  

# Inicializar componentes
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=40, detectShadows=False)

def video_capture():
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    prev_frame_time = 0
    
    while True:
        new_frame_time = time.time()
        fps = 1/(new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        
        success, frame = camera.read()
        if not success:
            break
        
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        # Procesar máscara de movimiento
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3,3)))  # Eliminar ruido
        
        # Crear overlay de movimiento coloreado
        color_overlay = np.full_like(frame, MOTION_COLOR)
        motion_mask = cv2.bitwise_and(color_overlay, cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR))
        
        # Procesar filtro seleccionado
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
        
        # Convertir a 3 canales para combinar
        processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        
        # Combinar visualizaciones
        combined_frame = np.hstack((processed, motion_mask))
        
        # Agregar FPS
        cv2.putText(combined_frame, f"FPS: {int(fps)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Codificar y enviar
        (flag, encoded) = cv2.imencode(".jpg", combined_frame)
        if flag:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + 
                   bytearray(encoded) + b'\r\n')


@app.route("/")
def index():
    return render_template("index.html", 
                          width=FRAME_WIDTH*2,  # Ancho doble
                          height=FRAME_HEIGHT,
                          filters=FILTERS,
                          active_filter=current_filter)

@app.route("/video_stream")
def video_stream():
    return Response(
        video_capture(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/set_filter", methods=["POST"])
def set_filter():
    global current_filter
    new_filter = request.form.get("filter_type")
    if new_filter in FILTERS:
        current_filter = new_filter
    return '', 204

if __name__ == "__main__":
    app.run(debug=True)