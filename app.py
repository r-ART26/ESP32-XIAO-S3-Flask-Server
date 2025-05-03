import cv2
from flask import Flask, Response, render_template
from io import BytesIO
import numpy as np

app = Flask(__name__)

def video_capture():
    # Usar OpenCV para capturar video de la webcam (0 = integrada)
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("Error: No se pudo acceder a la webcam.")
        return
    
    while True:
        # Leer frame de la webcam
        success, frame = camera.read()
        if not success:
            break
        
        # Convertir frame a bytes (simulando el flujo de la ESP32)
        img_data = BytesIO()
        ret, encodedImage = cv2.imencode(".jpg", frame)
        img_data.write(encodedImage.tobytes())
        
        # Simular el procesamiento del chunk (como en tu código original)
        try:
            # Convertir bytes a frame (esto ya no es necesario, pero lo dejo para mantener la lógica)
            chunk = img_data.getvalue()
            if len(chunk) > 100:
                cv_img = cv2.imdecode(np.frombuffer(chunk, np.uint8), 1)
                
                # Codificar y enviar frame
                (flag, encodedImageFinal) = cv2.imencode(".jpg", cv_img)
                if not flag:
                    continue
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + 
                       bytearray(encodedImageFinal) + b'\r\n')
        except Exception as e:
            print(e)
            continue

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_stream")
def video_stream():
    return Response(
        video_capture(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    app.run(debug=True)